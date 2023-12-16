import base64
import time
from typing import Optional
from serpapi import GoogleSearch
from loguru import logger
from PIL import Image
import piexif
from fractions import Fraction

from src.settings import get_settings

ENGINE = "google_local"
DOMAIN = "google.es"
RADIUS = 300
settings = get_settings()

def extract_coordinates(img: Image.Image) -> tuple[Optional[float], Optional[float]]:
    exif_img = img.info.get('exif') # img.getexif()
    if not exif_img:
        return None, None
    exif_data = piexif.load(exif_img)
    # logger.debug(f"exif_data: {exif_data}")
    gps_info = exif_data.get('GPS')
    if not gps_info:
        return None, None
    def convert_to_degrees(value):
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

    latitude = convert_to_degrees(gps_info[piexif.GPSIFD.GPSLatitude])
    longitude = convert_to_degrees(gps_info[piexif.GPSIFD.GPSLongitude])
    if gps_info[piexif.GPSIFD.GPSLatitudeRef] == 'S':
        latitude = -latitude
    if gps_info[piexif.GPSIFD.GPSLongitudeRef] == 'W':
        longitude = -longitude
    return (latitude, longitude)

def generate_uule_v2(latitude, longitude, radius):
    latitude_e7 = int(latitude * 1e7)
    longitude_e7 = int(longitude * 1e7)
    radius = int(radius * 620)

    timestamp = int(time.time() * 1000000)

    uule_v2_string = f"role:1\nproducer:12\nprovenance:6\ntimestamp:{timestamp}\nlatlng{{\nlatitude_e7:{latitude_e7}\nlongitude_e7:{longitude_e7}\n}}\nradius:{radius}\n"

    uule_v2_string_encoded = base64.b64encode(uule_v2_string.encode()).decode()

    return "a+" + uule_v2_string_encoded

def search_by_uule(query, uule) -> list[dict]:
    def _normalize_distance(local):
        distance = local.get('type')
        if not distance:
            distance = float(local['address'].split('·')[0].strip().split(' ')[0])
        else:
            distance = float(distance.split(' ')[0])
        return distance

    params = {
    "api_key": settings.SERPAPI_API_KEY,
    "engine": ENGINE,
    "google_domain": DOMAIN,
    "gl": "es",
    "hl": "en",
    "q": query,
    "device": "tablet",
    "uule": uule
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    locals = []
    for local in results['local_results']:
        distance = _normalize_distance(local)
        locals.append({
            'title': local['title'],
            'place_id': local['place_id'],
            'address': local['address'][local['address'].find('·')+2:],
            'description': local.get('description'),
            # 'extra': [local.get('service_options'), local.get('hours')],
            'distance': distance,
        })
    return sorted(locals, key=lambda x: x['distance'])

def search_by_place_id(query, place_id) -> dict:
    params = {
        "api_key": settings.SERPAPI_API_KEY,
        "engine": ENGINE,
        "google_domain": DOMAIN,
        "q": query,
        "gl": "es",
        "hl": "en",
        "ludocid": place_id,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    logger.debug(f"local_results: {results['local_results']}")

    result =  {
        'phone': results['local_results'][0]['phone'],
        'type': results['local_results'][0]['type'],
        'title': results['local_results'][0]['title'],
        'gps_coordinates': results['local_results'][0]['gps_coordinates'],
    }

    return result

def search(image_path, query):
    img = Image.open(image_path)
    latitude, longitude = extract_coordinates(img)
    uule = generate_uule_v2(latitude, longitude, RADIUS)
    logger.info(f"uule: {uule}")
    locals = search_by_uule(query, uule)
    logger.info(f"locals:\n{locals}")
    if len(locals) > 0:
        place = locals[0] | search_by_place_id(query, locals[0]['place_id'])
        logger.info(f"place:{place}")
        return place
