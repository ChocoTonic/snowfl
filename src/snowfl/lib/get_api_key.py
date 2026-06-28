import logging

import requests

from ..core import BASE_URL, HEADERS, get_api_key as _scrape_api_key
from .errors import FetchError

logger = logging.getLogger(__name__)


def _fetch(url):
    """`requests`-based transport for the library's key-scraping path."""
    try:
        res = requests.get(url=url, headers=HEADERS)
    except requests.exceptions.RequestException as e:
        logger.error("HTTP error occurred", exc_info=e)
        raise FetchError("Error during HTTP request") from e
    if res.status_code != 200:
        raise FetchError("Error in fetching: Status {0}".format(res.status_code))
    return res.text


def get_api_key():
    """Fetch the Snowfl API key using ``requests`` (library entry point).

    Delegates the scraping logic to :func:`snowfl.core.get_api_key`.
    """
    return _scrape_api_key(_fetch)
