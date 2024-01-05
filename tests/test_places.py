from typing import Any, Dict, List

import pytest
from pytest_mock import MockerFixture


def test_extract_coordinates(exif_image):
    from src.llm.places import EXIFHelper
    lat, lon = EXIFHelper.extract_coordinates(exif_image)
    assert pytest.approx(lat) == 39.88816388888889
    assert pytest.approx(lon) == 4.265166666666666


def test_search_by_uule(mocker: MockerFixture, serpapi_search_by_uule: List[Dict[str, Any]]):
    mocker.patch("src.llm.places.SerpapiHelper._search", return_value=serpapi_search_by_uule)
    settings = mocker.MagicMock()
    from src.llm.places import SerpapiHelper
    results = SerpapiHelper.search_by_uule(settings, "query", "uule")

    assert len(results) == 5
    assert results[0] == {
        "distance": 2,
        "title": "Bakery One",
        "place_id": "9876543210123456789",
        "type": "Cake Shop",
        "phone": "9876543210",
        "address": "123 Main Street",
        "website": "http://example.com/website_1",
    }


def test_search_by_placeid(mocker: MockerFixture, serpapi_search_by_place_id: List[Dict[str, Any]]):
    mocker.patch("src.llm.places.SerpapiHelper._search", return_value=serpapi_search_by_place_id)
    settings = mocker.MagicMock()
    from src.llm.places import SerpapiHelper
    result = SerpapiHelper.search_by_place_id(settings, "query", "place_id")

    assert result == {
        "phone": "9876543210",
        "type": "Restaurant",
        "address": "Plaça Bastió, 10",
        "gps_coordinates": {"latitude": 39.8890265, "longitude": 4.2626878},
    }


def test_reverse_geocode(mocker: MockerFixture, reverse_geocode_data) -> Dict[str, Any]:
    mock_reverse_geocode = mocker.patch("geobatchpy.Client.reverse_geocode", return_value=reverse_geocode_data)
    settings = mocker.MagicMock()

    from src.llm.places import GeoapifyHelper
    result = GeoapifyHelper.reverse_geocode(settings, 39.8883636, 4.2652852)

    mock_reverse_geocode.assert_called_once_with(4.2653, 39.8884)

    assert result == {
        "country": "Spain",
        "state": "Balearic Islands",
        "county": "Menorca",
        "city": "Ma\\u00f3",
        "postcode": "07703",
    }