import base64
import time
from fractions import Fraction
from typing import Dict, List, Optional, Tuple, Union

import piexif
from loguru import logger
from PIL import Image
from serpapi import GoogleSearch

from src.settings import Settings


class EXIFHelper:
    @classmethod
    def _convert_to_degrees(cls, value: Union[int, float, Tuple[int, int], Tuple[float, float]]) -> float:
        if isinstance(value[0], (int, float)):
            d = Fraction(value[0])
        else:
            d = Fraction(value[0][0], value[0][1])

        if isinstance(value[1], (int, float)):
            m = Fraction(value[1])
        else:
            m = Fraction(value[1][0], value[1][1])

        if isinstance(value[2], (int, float)):
            s = Fraction(value[2])
        else:
            s = Fraction(value[2][0], value[2][1])

        return float(d + (m / 60) + (s / 3600))

    @classmethod
    def extract_coordinates(cls, img: Image.Image) -> Tuple[Optional[float], Optional[float]]:
        """
        Extracts the latitude and longitude coordinates from the EXIF data of an image.

        Args:
            img (PIL.Image.Image): The image from which to extract the coordinates.

        Returns:
            Tuple[Optional[float], Optional[float]]: A tuple containing the latitude and longitude coordinates.
                Returns (None, None) if the image does not have EXIF data or if the coordinates are not found.
        """

        img_exif = img.info.get("exif")  # img.getexif()
        if not img_exif:
            return None, None
        exif = piexif.load(img_exif)
        exif_gps = exif.get("GPS")
        if not exif_gps:
            return None, None

        latitude = cls._convert_to_degrees(exif_gps[piexif.GPSIFD.GPSLatitude])
        longitude = cls._convert_to_degrees(exif_gps[piexif.GPSIFD.GPSLongitude])
        if exif_gps[piexif.GPSIFD.GPSLatitudeRef] == "S":
            latitude = -latitude
        if exif_gps[piexif.GPSIFD.GPSLongitudeRef] == "W":
            longitude = -longitude
        return (latitude, longitude)


class SerperHelper:
    ENGINE = "google_local"
    DOMAIN = "google.es"

    @staticmethod
    def generate_uule_v2(latitude, longitude, radius) -> str:
        """
        Generate a UULE v2 string based on the given latitude, longitude, and radius.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
            radius (float): The radius of the location in kilometers.

        Returns:
            str: The UULE v2 string.

        """
        latitude_e7 = int(latitude * 1e7)
        longitude_e7 = int(longitude * 1e7)
        radius = int(radius * 620)

        timestamp = int(time.time() * 1000000)

        uule_v2_string = f"role:1\nproducer:12\nprovenance:6\ntimestamp:{timestamp}\nlatlng{{\nlatitude_e7:{latitude_e7}\nlongitude_e7:{longitude_e7}\n}}\nradius:{radius}\n"

        uule_v2_string_encoded = base64.b64encode(uule_v2_string.encode()).decode()

        return "a+" + uule_v2_string_encoded



    @classmethod
    def _normalize_distance(cls, local: Dict) -> Optional[float]:
        distance = local.get("type")
        try:
            if not distance:
                distance = float(local["address"].split("·")[0].strip().split(" ")[0])
            else:
                distance = float(distance.split(" ")[0])
            return distance
        except Exception:
            logger.error(f"Error parsing distance {distance} from {local['address']}")
            return None


    @classmethod
    def _common_parameters(cls, settings: Settings) -> Dict:
        return {
            "api_key": settings.SERPAPI_API_KEY,
            "engine": cls.ENGINE,
            "google_domain": cls.DOMAIN,
            "gl": "es",
            "hl": "en",
            "device": "tablet"
        }

    @classmethod
    def _search(cls, settings: Settings, additional_args: Dict) -> List[Dict]:
        params = cls._common_parameters(settings) | additional_args
        search = GoogleSearch(params)
        results = search.get_dict()
        return results["local_results"]

    @classmethod
    def search_by_uule(cls, settings: Settings, query: str, uule: str) -> List[Dict]:
        """
        Search for local results on Google based on the given query and uule.

        Args:
            query (str): The search query.
            uule (str): The uule parameter for location-based search.

        Returns:
            List[Dict]: A list of dictionaries representing the local search results.
                Each dictionary contains the following keys:
                - "title": The title of the local result.
                - "place_id": The place ID of the local result.
                - "address": The address of the local result.
                - "description": The description of the local result (optional).
                - "distance": The distance of the local result from the specified location.

        """

        local_results = cls._search(settings, {"q": query, "uule": uule})

        locals = []
        for local in local_results:
            distance = cls._normalize_distance(local)
            if distance:
                locals.append(
                    {
                        "title": local.get("title"),
                        "place_id": local.get("place_id"),
                        "address": local["address"][local["address"].find("·") + 2 :],
                        "description": local.get("description"),
                        # 'extra': [local.get('service_options'), local.get('hours')],
                        "distance": distance,
                    }
                )
        return sorted(locals, key=lambda x: x["distance"])

    @classmethod
    def search_by_place_id(cls, settings: Settings, query: str, place_id: str) -> Dict:
        """
        Search for a place by its place ID.

        Args:
            query (str): The search query.
            place_id (str): The place ID of the location.

        Returns:
            dict: A dictionary containing information about the place, including phone number, type, title, and GPS coordinates.
        """
        if place_id is None:
            logger.warning("No place ID provided")
            return {}

        local_results = cls._search(settings, {"q": query, "ludocid": place_id})

        result = {
            "phone": local_results[0].get("phone"),
            "type": local_results[0].get("type"),
            "title": local_results[0].get("title"),
            "gps_coordinates": local_results[0].get("gps_coordinates"),
        }

        return result


class PlacesTool():
    RADIUS = 300

    def __init__(self, settings: Settings):
        self.settings: Settings = settings

    def search(self, image_path: str, query: str, lat: Optional[float], lon: Optional[float]) -> Optional[Dict]:
        """
        Searches for a place based on the given image path and query.

        Args:
            image_path (str): The path to the image.
            query (str): The search query.

        Returns:
            Optional[Dict]: A dictionary representing the found place, or None if no place is found.
        """
        if lat and lon:
            latitude, longitude = lat, lon
        else:
            img = Image.open(image_path)
            latitude, longitude = EXIFHelper.extract_coordinates(img)
            if not latitude or not longitude:
                return None
        uule = SerperHelper.generate_uule_v2(latitude, longitude, self.RADIUS)
        logger.info(f"uule: {uule}")
        locals = SerperHelper.search_by_uule(self.settings, query, uule)
        logger.debug(f"locals:\n{locals}")
        if len(locals) > 0:
            place = locals[0] | SerperHelper.search_by_place_id(self.settings, query, locals[0].get("place_id"))
            logger.info(f"place:{place}")
            return place
