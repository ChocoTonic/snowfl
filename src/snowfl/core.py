"""Transport-agnostic core for snowfl.com scraping.

Pure and dependency-free (stdlib only) so the exact same logic can be both:

* imported by the ``requests``-based library layer (:mod:`snowfl.snowfl`), and
* inlined verbatim into the single-file qBittorrent search plugin
  (see ``plugin/shell.py`` and ``tools/build_plugin.py``).

All HTTP is performed through an injected ``fetch(url) -> str`` callable, so this
module never imports ``requests`` (which is unavailable inside qBittorrent).

Everything below the ``BEGIN PLUGIN INLINE`` marker is copied as-is into the
generated plugin, so keep it stdlib-only and conservative (no 3.10+ only syntax).
"""

import json
import re
from urllib.parse import quote

# === BEGIN PLUGIN INLINE ===
BASE_URL = "https://snowfl.com/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

REGEX_FOR_JS = re.compile(r'((?:b.min.js).*)(?=")')
REGEX_FOR_KEY = re.compile(r'findNextItem.*?"(.*?)"')

SORT_ENUM = {
    "MAX_SEED": "/DH5kKsJw/0/SEED/NONE/",
    "MAX_LEECH": "/DH5kKsJw/0/LEECH/NONE/",
    "SIZE_ASC": "/DH5kKsJw/0/SIZE_ASC/NONE/",
    "SIZE_DSC": "/DH5kKsJw/0/SIZE/NONE/",
    "RECENT": "/DH5kKsJw/0/DATE/NONE/",
    "NONE": "/DH5kKsJw/0/NONE/NONE/",
}


class ApiError(Exception):
    """Raised when the Snowfl API key cannot be located."""

    def __init__(self, message="API error occurred"):
        super().__init__(message)


class FetchError(Exception):
    """Raised for errors while fetching data from Snowfl."""

    def __init__(self, message="Fetch error occurred", status_code=None):
        super().__init__(message)
        self.status_code = status_code

    def __str__(self):
        return "{0}: {1} (Status Code: {2})".format(
            self.__class__.__name__, self.args[0], self.status_code
        )


def get_api_key(fetch):
    """Scrape the per-session API key. ``fetch(url) -> str`` performs the HTTP GET.

    Raises :class:`ApiError` if the homepage JS link or the key cannot be found;
    transport errors are surfaced by ``fetch`` itself.
    """
    home_text = fetch(BASE_URL)
    js_match = REGEX_FOR_JS.search(home_text)
    if not js_match:
        raise ApiError("JS file link not found in homepage")

    js_text = fetch(BASE_URL + js_match.group(0))
    key_match = REGEX_FOR_KEY.search(js_text)
    if not key_match:
        raise ApiError("API key not found in JS file")

    return key_match.group(1)


def build_search_url(api_key, query, sort="NONE", include_nsfw=False):
    """Build the Snowfl search URL for a query."""
    sort_option = SORT_ENUM.get(sort, SORT_ENUM["NONE"])
    flag = 1 if include_nsfw else 0
    return "{0}{1}/{2}{3}{4}".format(BASE_URL, api_key, query, sort_option, flag)


def build_magnet_url(api_key, item):
    """Build the Snowfl magnet-resolution URL for a single result item."""
    encoded_url = quote(item.get("url", ""))
    return "{0}{1}/{2}/{3}".format(
        BASE_URL, api_key, item.get("site", ""), encoded_url
    )


def fill_magnets(api_key, data, fetch):
    """Resolve magnet links for items that lack one, via the magnet endpoint.

    Failures per item are swallowed so one bad result never sinks the search.
    """
    results = []
    for item in data:
        if not item.get("magnet"):
            try:
                resolved = json.loads(fetch(build_magnet_url(api_key, item)))
                item["magnet"] = resolved.get("url", "")
            except Exception:
                pass
        results.append(item)
    return results


def fetch_results(
    query,
    api_key,
    fetch,
    sort="NONE",
    include_nsfw=False,
    force_fetch_magnet=False,
):
    """Run a search and return the raw Snowfl result list.

    When ``force_fetch_magnet`` is true, items missing a magnet are resolved via
    :func:`fill_magnets`.
    """
    if len(query) <= 2:
        raise FetchError("Query should be of length >= 3")

    data = json.loads(fetch(build_search_url(api_key, query, sort, include_nsfw)))
    if force_fetch_magnet and data:
        data = fill_magnets(api_key, data, fetch)
    return data
