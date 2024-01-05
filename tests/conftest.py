from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest
from PIL import Image


@pytest.fixture(scope='session')
def serpapi_search_by_uule() -> List[Dict[str, Any]]:
    return [
        {
            "position": 1,
            "place_id": "9876543210987654321",
            "place_id_search": "http://example.com/search_url_2",
            "lsig": "CD456ABC789",
            "gps_coordinates": {"latitude": 39.8652281, "longitude": 4.2252228},
            "service_options": {"in_store_shopping": True},
            "links": {"directions": "http://example.com/directions_2"},
            "title": "Bakery Two",
            "address": "4.3 km · 456 Oak Avenue",
            "type": "Bakery",
        },
        {
            "position": 2,
            "place_id": "9876543210123456789",
            "place_id_search": "http://example.com/search_url_1",
            "lsig": "AB123XYZ456",
            "gps_coordinates": {"latitude": 39.8883636, "longitude": 4.2652852},
            "service_options": {"in_store_shopping": True},
            "links": {"website": "http://example.com/website_1", "directions": "http://example.com/directions_1"},
            "title": "Bakery One",
            "address": "2 m · 123 Main Street",
            "type": "Cake Shop",
            "phone": "9876543210",
            "hours": "Mon-Fri: 8:00 AM - 6:00 PM",
            "extensions": [""],
        },
        {
            "position": 3,
            "place_id": "9876543219876543210",
            "place_id_search": "http://example.com/search_url_3",
            "lsig": "EF789MNO012",
            "gps_coordinates": {"latitude": 39.5708491, "longitude": 2.6512442},
            "service_options": {"dine_in": True, "takeaway": True},
            "links": {"website": "http://example.com/website_3", "directions": "http://example.com/directions_3"},
            "title": "Bakery Three",
            "address": "142.5 km · 789 Pine Lane",
            "type": "Pastry Shop",
            "phone": "1234567890",
            "hours": "Tue-Sat: 9:00 AM - 7:00 PM",
            "extensions": [""],
        },
        {
            "position": 4,
            "place_id": "9876543212345678901",
            "place_id_search": "http://example.com/search_url_4",
            "lsig": "GH012PQR345",
            "gps_coordinates": {"latitude": 39.5740302, "longitude": 2.652053},
            "service_options": {"dine_in": True, "takeaway": True, "delivery": True},
            "links": {"website": "http://example.com/website_4", "directions": "http://example.com/directions_4"},
            "title": "Bakery Four",
            "address": "142.3 km · 101 Maple Drive",
            "type": "Cake Shop",
            "phone": "8765432109",
            "hours": "Mon-Sun: 8:00 AM - 8:00 PM",
            "extensions": [""],
        },
        {
            "position": 5,
            "place_id": "98765432109876543210",
            "place_id_search": "http://example.com/search_url_5",
            "lsig": "IJ678STU901",
            "gps_coordinates": {"latitude": 39.5513984, "longitude": 2.6209165},
            "service_options": {"in_store_shopping": True},
            "links": {"website": "http://example.com/website_5", "directions": "http://example.com/directions_5"},
            "title": "Bakery Five",
            "address": "145.5 km · 555 Cedar Street",
            "type": "Bakery",
            "phone": "5678901234",
            "hours": "Mon-Fri: 7:00 AM - 5:00 PM",
            "extensions": [""],
        },
    ]

@pytest.fixture(scope='session')
def serpapi_search_by_place_id() -> List[Dict[str, Any]]:
    return [
        {
            "position": 1,
            "rating": 4.3,
            "reviews_original": "(732)",
            "reviews": 732,
            "price": "€€",
            "place_id": "11639818899667161410",
            "place_id_search": "http://example.com/search_url_1",
            "lsig": "AB86z5XaIC1-iQ1MPedRZWGKzjXR",
            "gps_coordinates": {"latitude": 39.8890265, "longitude": 4.2626878},
            "links": {"directions": "http://example.com/directions_1"},
            # "title": "Restaurant One",
            "type": "Restaurant",
            "address": "17.79 m · Plaça Bastió, 10",
            "phone": "9876543210",
            "hours": "Temporarily closed",
        }
    ]

@pytest.fixture(scope='session')
def vision_venue_data() -> str:
    return """```json\n{\n  "venue_name": "Forn del St. Cristo",\n  "venue_type": "Bakery"\n}\n```"""

@pytest.fixture(scope='session')
def reverse_geocode_data() -> Dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "datasource": {
                        "sourcename": "openstreetmap",
                        "attribution": "\\u00a9 OpenStreetMap contributors",
                        "license": "Open Database License",
                        "url": "https://www.openstreetmap.org/copyright",
                    },
                    "country": "Spain",
                    "country_code": "es",
                    "state": "Balearic Islands",
                    "county": "Menorca",
                    "city": "Ma\\u00f3",
                    "postcode": "07703",
                    "street": "Pla\\u00e7a Basti\\u00f3",
                    "housenumber": "11",
                    "lon": 4.2628651,
                    "lat": 39.8891023,
                    "district": "Ma\\u00f3",
                    "distance": 17.788732778761872,
                    "result_type": "building",
                    "formatted": "Pla\\u00e7a Basti\\u00f3, 11, 07703 Ma\\u00f3, Spain",
                    "address_line1": "Pla\\u00e7a Basti\\u00f3, 11",
                    "address_line2": "07703 Ma\\u00f3, Spain",
                    "timezone": {
                        "name": "Europe/Madrid",
                        "offset_STD": "+01:00",
                        "offset_STD_seconds": 3600,
                        "offset_DST": "+02:00",
                        "offset_DST_seconds": 7200,
                        "abbreviation_STD": "CET",
                        "abbreviation_DST": "CEST",
                    },
                    "plus_code": "8FF6V7Q7+J4",
                    "plus_code_short": "Q7+J4 Ma\\u00f3, Menorca, Spain",
                    "rank": {"importance": 9.99999999995449e-06, "popularity": 4.142446133499272},
                    "place_id": "51010a3f822c0d11405931a6aa1acef14340f00103f9016e58fd7501000000c00203e203256f70656e7374726565746d61703a616464726573733a6e6f64652f36323734353034383134",
                },
                "geometry": {"type": "Point", "coordinates": [4.2628651, 39.8891023]},
                "bbox": [4.2628151, 39.8890523, 4.2629151, 39.8891523],
            }
        ],
        "query": {"lat": 39.8892, "lon": 4.2627, "plus_code": "8FF6V7Q7+M3"},
    }

def card_data() -> str:
    return """
BEGIN:VCARD
VERSION:3.0
PRODID:-//Apple Inc.//iOS 14.3//EN
N:Parra Martós;Ana;;;
FN:Ana Parra Martós
TEL;type=CELL;type=VOICE;type=pref:+34111222333
REV:2021-01-04T21:17:21Z
END:VCARD
"""

@pytest.fixture(scope='session')
def exif_image(exif_image_path) -> Image.Image:
    return Image.open(exif_image_path)

@pytest.fixture(scope='session')
def exif_image_path() -> str:
    return "tests/data/exif.jpg"


@pytest.fixture()
def mocked_client_ainvoke(mocker) -> AsyncMock:
    # async def async_magic():  # monkey patch MagicMock to support async calls
    #     pass
    # MagicMock.__await__ = lambda x: async_magic().__await__()
    async_mock = AsyncMock()
    mock = mocker.patch("langchain.chat_models.AzureChatOpenAI")
    mock.return_value.openai_api_key = "test"
    mocker.patch.object(mock.return_value, "ainvoke", side_effect=async_mock)
    return async_mock
