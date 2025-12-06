from unittest.mock import patch

import pytest
import requests
from requests.exceptions import RequestException

from snowfl.snowfl import ApiError, FetchError, get_api_key


class MockResponse:
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code


def mock_requests_get(url, headers=None):
    if url == "https://snowfl.com/":
        return MockResponse("<html>Sample HTML</html>", 200)
    elif url.startswith("https://snowfl.com/"):
        return MockResponse('var apiKey = "fake-api-key";', 200)
    else:
        raise RequestException("Fake RequestException")


# Use patch to mock the requests.get method
@pytest.fixture
def mock_requests():
    with patch("requests.get", side_effect=mock_requests_get):
        yield


def test_get_api_key_fetch_error(mock_requests):
    with patch(
        "requests.get",
        side_effect=RequestException("Fake RequestException"),
    ):
        with pytest.raises(FetchError):
            get_api_key()


def test_get_api_key_unexpected_error(mock_requests):
    with patch("requests.get", side_effect=Exception("Fake Exception")):
        with pytest.raises(Exception):
            get_api_key()


def test_get_api_key_js_file_not_found(mock_requests):
    with patch(
        "requests.get", return_value=MockResponse("<html>No JS file here</html>", 200)
    ):
        with pytest.raises(ApiError, match="JS file link not found in homepage"):
            get_api_key()
