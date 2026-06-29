import json
import logging

import requests

from .core import BASE_URL, HEADERS, build_search_url
from .lib import ApiError, FetchError, get_api_key

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Snowfl:
    def __init__(self):
        self.api_key = None

    def initialize(self):
        """
        Initialize the Snowfl instance by fetching the API key.
        """
        self.api_key = get_api_key()
        if self.api_key is None:
            raise ApiError("Failed to obtain API key.")

    def parse(
        self,
        query,
        sort="NONE",
        include_nsfw=False,
        force_fetch_magnet=False,
    ):
        """
        Parse the given query using the Snowfl API.
        """
        if len(query) <= 2:
            raise FetchError("Query should be of length >= 3")

        url = build_search_url(self.api_key, query, sort, include_nsfw)
        logger.info(f"URL: {url}")

        try:
            res = requests.get(url=url, headers=HEADERS)
            if res.status_code != 200:
                raise FetchError(
                    f"Failed to fetch data, HTTP status: {res.status_code}"
                )

            data = json.loads(res.text)

            if force_fetch_magnet and data:
                updated_data = self._fetch_magnet_links(data)
                return {"status": 200, "message": "OK", "data": updated_data}

            return {"status": 200, "message": "OK", "data": data}

        except FetchError as e:
            logger.error(f"FetchError: {e}")
            raise  # Re-raise the FetchError exception
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"status": 500, "message": "Internal Server Error", "data": None}

    def _fetch_magnet_links(self, data):
        """
        Fetch magnet links for items without them.
        """
        updated_data = []
        for item in data:
            if "magnet" not in item or not item["magnet"]:
                try:
                    magnet = self._get_magnet_url(item)
                    item["magnet"] = magnet
                except FetchError as e:
                    logger.warning(
                        f"Failed to fetch magnet link for item: {item}. Error: {e}"
                    )
            updated_data.append(item)
        return updated_data

    def _get_magnet_url(self, item):
        """
        Fetch the magnet URL for a specific item.
        """
        try:
            encoded_url = requests.utils.quote(item.get("url", ""))
            api_url = f"{BASE_URL}{self.api_key}/{item.get('site', '')}/{encoded_url}"
            res = requests.get(api_url, headers=HEADERS)
            if res.status_code != 200:
                raise FetchError("Couldn't get Magnet URL")
            return res.json().get("url", "")
        except Exception as e:
            raise FetchError(f"Error fetching magnet URL: {e}")

    def __str__(self):
        return f"Snowfl API Wrapper"

    def __repr__(self):
        return "Snowfl()"
