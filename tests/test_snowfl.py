import json
from unittest.mock import patch

import pytest

from snowfl.snowfl import ApiError, FetchError, Snowfl


@pytest.fixture
def snowfl_instance():
    return Snowfl()


def test_initialize_with_valid_key(snowfl_instance):
    snowfl_instance.initialize()

    assert snowfl_instance.api_key is not None


@patch("snowfl.snowfl.get_api_key")
def test_initialize_with_none_key(mock_get_api_key, snowfl_instance):
    mock_get_api_key.return_value = None

    with pytest.raises(ApiError, match="Failed to obtain API key."):
        snowfl_instance.initialize()


@patch("requests.get")
def test_parse_with_valid_response(mock_get, snowfl_instance):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = json.dumps({"key": "value"})

    result = snowfl_instance.parse("query")

    assert result == {"status": 200, "message": "OK", "data": {"key": "value"}}


@patch("requests.get")
def test_parse_with_invalid_response(mock_get, snowfl_instance):
    mock_get.return_value.status_code = 404

    with pytest.raises(FetchError, match="Failed to fetch data, HTTP status: 404"):
        snowfl_instance.parse("query")


def test_parse_with_short_query(snowfl_instance):
    with pytest.raises(FetchError, match="Query should be of length >= 3"):
        snowfl_instance.parse("q")


@patch("snowfl.snowfl.Snowfl._fetch_magnet_links")
@patch("requests.get")
def test_parse_with_force_fetch_magnet(
    mock_get, mock_fetch_magnet_links, snowfl_instance
):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = json.dumps([{"key": "value", "magnet": None}])

    mock_fetch_magnet_links.return_value = [{"key": "value", "magnet": "magnet_link"}]

    result = snowfl_instance.parse("query", force_fetch_magnet=True)

    mock_fetch_magnet_links.assert_called_once()

    assert result == {
        "status": 200,
        "message": "OK",
        "data": [{"key": "value", "magnet": "magnet_link"}],
    }


@patch("requests.get")
def test_parse_with_unexpected_error(mock_get, snowfl_instance):
    mock_get.side_effect = Exception("Unexpected error occurred")

    result = snowfl_instance.parse("query")

    assert result == {
        "status": 500,
        "message": "Internal Server Error",
        "data": None,
    }


def test_str(snowfl_instance):
    assert str(snowfl_instance) == "Snowfl API Wrapper"


def test_repr(snowfl_instance):
    assert repr(snowfl_instance) == "Snowfl()"
