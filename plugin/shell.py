# VERSION: __PLUGIN_VERSION__
# qBittorrent search engine plugin for snowfl.com
#
# AUTO-GENERATED — DO NOT EDIT engine/snowfl.py BY HAND.
# Source of truth: src/snowfl/core.py + plugin/shell.py
# Regenerate with `make plugin`. Project: https://github.com/ChocoTonic/snowfl
import json
import re
import time
from urllib.parse import quote

try:
    from helpers import retrieve_url
    from novaprinter import prettyPrinter
except ImportError:
    # Lets this file be imported / unit-tested outside of qBittorrent, where the
    # `helpers` and `novaprinter` modules are not available.
    def retrieve_url(url):
        raise RuntimeError("retrieve_url is only available inside qBittorrent")

    def prettyPrinter(dictionary):
        print(dictionary)

# Bump this whenever generated behavior changes — qBittorrent only pulls an update
# when the `# VERSION:` header above (stamped from this value) increases.
PLUGIN_VERSION = "1.1"

# __SNOWFL_CORE__


class snowfl(object):
    url = "https://snowfl.com"
    name = "Snowfl"
    supported_categories = {"all": "0"}

    def search(self, what, cat="all"):
        api_key = get_api_key(retrieve_url)
        results = fetch_results(
            what,
            api_key,
            retrieve_url,
            sort="MAX_SEED",
            force_fetch_magnet=True,
        )
        now = time.time()
        for item in results:
            # snowfl is an aggregator; surface the originating site in the name,
            # since engine_url must stay "https://snowfl.com" (qBittorrent matches
            # it to route downloads back to this plugin).
            name = item.get("name", "")
            site = item.get("site", "")
            if site:
                name = "%s [%s]" % (name, site)
            prettyPrinter(
                {
                    "link": item.get("magnet") or item.get("url", ""),
                    "name": name,
                    "size": item.get("size", "-1"),
                    "seeds": item.get("seeder", -1),
                    "leech": item.get("leecher", -1),
                    "engine_url": self.url,
                    "desc_link": item.get("url", ""),
                    "pub_date": age_to_pub_date(item.get("age"), now),
                }
            )

    def download_torrent(self, info):
        # Results already carry a magnet (force_fetch_magnet above), so this is the
        # common path; the page-scrape is a fallback for the rare magnet-less link.
        if info.startswith("magnet:"):
            print(info + " " + info)
            return
        page = retrieve_url(info)
        match = re.search(r'"(magnet:[^"]+)"', page)
        if match:
            print(match.group(1) + " " + info)
        else:
            raise RuntimeError("Could not resolve a magnet link for: " + info)
