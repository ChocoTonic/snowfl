import json
from unittest.mock import patch

import pytest

from snowfl.snowfl import ApiError, FetchError, Snowfl, BASE_URL, HEADERS


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


@patch("snowfl.snowfl.Snowfl._get_magnet_url")
def test_fetch_magnet_links(mock_get_magnet_url, snowfl_instance):
    mock_get_magnet_url.return_value = "magnet:?xt=urn:btih:dummyhash"

    data = [
        {"key": "value1", "magnet": None},
        {"key": "value2"},
    ]

    result = snowfl_instance._fetch_magnet_links(data)

    assert mock_get_magnet_url.call_count == 2

    assert result == [
        {"key": "value1", "magnet": "magnet:?xt=urn:btih:dummyhash"},
        {"key": "value2", "magnet": "magnet:?xt=urn:btih:dummyhash"},
    ]


@patch("snowfl.snowfl.Snowfl._get_magnet_url")
def test_fetch_magnet_links_with_fetch_error(
    mock_get_magnet_url, snowfl_instance, caplog
):
    mock_get_magnet_url.side_effect = FetchError("Failed to fetch magnet link")

    data = [
        {"key": "value1", "magnet": None},
        {"key": "value2"},
    ]

    result = snowfl_instance._fetch_magnet_links(data)

    assert any(
        "Failed to fetch magnet link for item" in record.message
        for record in caplog.records
    )

    assert result == [
        {"key": "value1", "magnet": None},
        {"key": "value2"},
    ]


@patch("requests.get")
def test_get_magnet_url_with_non_200_status(mock_get, snowfl_instance):
    # Mock the requests.get method to return a response with a non-200 status code
    mock_get.return_value.status_code = 404

    # Sample item data
    item = {"url": "http://example.com", "site": "example"}

    # Assert that a FetchError is raised
    with pytest.raises(FetchError, match="Couldn't get Magnet URL"):
        snowfl_instance._get_magnet_url(item)


@patch("requests.get")
def test_get_magnet_url_with_exception(mock_get, snowfl_instance):
    # Mock the requests.get method to raise an exception
    mock_get.side_effect = Exception("Unexpected error")

    # Sample item data
    item = {"url": "http://example.com", "site": "example"}

    # Assert that a FetchError is raised
    with pytest.raises(FetchError, match="Error fetching magnet URL: Unexpected error"):
        snowfl_instance._get_magnet_url(item)


@patch("requests.get")
@patch("requests.utils.quote")
def test_get_magnet_url_api_url_construction(mock_quote, mock_get, snowfl_instance):
    # Mock the quote function to return an encoded URL
    mock_quote.return_value = "encoded_url"

    # Mock the requests.get method to return a valid response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"url": "magnet:?xt=urn:btih:dummyhash"}

    # Sample item data
    item = {"url": "http://example.com", "site": "example"}

    # Call the _get_magnet_url method
    result = snowfl_instance._get_magnet_url(item)

    # Assert that the quote function was called with the correct URL
    mock_quote.assert_called_once_with("http://example.com")

    # Assert that the constructed API URL is correct
    expected_api_url = f"{BASE_URL}{snowfl_instance.api_key}/example/encoded_url"
    mock_get.assert_called_once_with(expected_api_url, headers=HEADERS)

    # Assert that the result is the expected magnet URL
    assert result == "magnet:?xt=urn:btih:dummyhash"
