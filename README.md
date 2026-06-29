# Snowfl API Python Wrapper

This is an unofficial Python wrapper for the [Snowfl](https://snowfl.com/) API, inspired by the work of [c0dysharma](https://github.com/c0dysharma/snowfl-api). Snowfl is a platform for searching and accessing torrent files.

From a single codebase, it can be used two ways:

- **As a Python library** — `pip install snowfl`, then search programmatically. See [Usage](#usage).
- **As a qBittorrent search plugin** — a self-contained, dependency-free `engine/snowfl.py` generated from the same core. See [Install as a qBittorrent search plugin](#install-as-a-qbittorrent-search-plugin).

The shared scraping logic lives in `src/snowfl/core.py`; the library and the plugin are thin layers over it (see [Development](#development)).

## Installation

To use this Snowfl API Python wrapper, you can install it using pip:

```bash
pip install snowfl
```

## Install as a qBittorrent search plugin

The same code also ships as a self-contained [qBittorrent search plugin](https://github.com/qbittorrent/search-plugins/wiki/How-to-install-search-plugins)
(`snowfl.py`) — no `pip`, no dependencies, just one file.

In qBittorrent: **View → Search Engine** (enable it), then **Search plugins… →
Install a new one → Web link**, and paste:

```
https://github.com/ChocoTonic/snowfl/releases/latest/download/snowfl.py
```

That URL always points at the newest published release, so qBittorrent's **Check
for updates** pulls new versions automatically as they are released. (You can also
pick **Local file** and select a downloaded copy.)

The plugin maps each result to qBittorrent's fields (`link`, `name`, `size`,
`seeds`, `leech`, `engine_url`, `desc_link`, `pub_date`), sorts by seeders, and
resolves magnet links up front. Because snowfl is an aggregator, the originating
site is appended to the name (e.g. `… [limetorrents]`) — `engine_url` must stay
`https://snowfl.com` so qBittorrent can route downloads back to this plugin. The
"Published On" column is derived from snowfl's relative age (e.g. "2 weeks"), so
it is approximate. `engine/snowfl.py` is generated — see
[Development](#development) before changing it.

## Usage

### Initializing Snowfl

Before making API requests, you need to initialize the Snowfl instance by fetching the API key. This key is required to access the Snowfl API.

```python
from snowfl import Snowfl, ApiError, FetchError

snowfl = Snowfl()
try:
    snowfl.initialize()
except ApiError as e:
    print(f"Error initializing Snowfl: {e}")
```

### Searching Snowfl

You can use the `parse` method to search the Snowfl site for torrents. You need to provide a search query, and you can optionally specify various parameters to customize your search.

```python
from pprint import pprint


try:
    query = "JoJo"
    sort = "MAX_SEED"  # Sorting by maximum seeders
    include_nsfw = False  # Exclude NSFW content

    result = snowfl.parse(query, sort=sort, include_nsfw=include_nsfw)
    pprint(result)
except FetchError as e:
    print(f"Error searching Snowfl: {e}")
```

### Configuration

You can customize your search by specifying the following parameters:

- `query`: The search query you want to use.
- `sort`: Sorting method for the search results. Available options:
  - `MAX_SEED`: Sort by decreasing number of seed counts (default).
  - `MAX_LEECH`: Sort by decreasing number of leech counts.
  - `SIZE_ASC`: Sort by increasing size per file.
  - `SIZE_DSC`: Sort by decreasing size per file.
  - `RECENT`: Sort by recent torrents first.
  - `NONE`: No sorting (Snowfl default).
- `include_nsfw`: Include NSFW (Not Safe For Work) content in the search results. Set to `True` to include NSFW content; `False` by default.

### Return Value

The `parse` method returns a dictionary with the following structure:

```python
{
    "status": <HTTP status code>,
    "message": <status message>,
    "data": [<array of objects>]
}
```

### Example Responses

#### Found Something

```python
{
    "status": 200,
    "message": "OK",
    "data": [
        {
            "magnet": "magnet:?xt=urn:btih:F3B5014A2E048E9286163B3A6A9D95942F3D8F3B&tr=udp%3A%2F%2Ftracker",
            "age": "12 months",
            "name": "John Coltrane - Ole Coltrane [V0](Big Papi) Jazz Music",
            "size": "86.92 MB",
            "seeder": 2,
            "leecher": 1,
            "type": "Music",
            "site": "****",
            "url": "https://www.*****.info/John-Coltrane--Ole-Coltrane-[V0](Big-Papi)-Jazz-Music-torrent-4500787.html",
            "trusted": False,
            "nsfw": False
        },
        {
            "magnet": "magnet:?xt=urn:btih:6f1fe981ab6624ef5c235278128c00d1c7ff534e&dn",
            "age": "6 years",
            "name": "John Newman Ft. Calvin Harris Ole MP3 Download, 2016",
            "size": "9.41 MB",
            "seeder": 1,
            "leecher": 0,
            "type": "Music",
            "site": "****",
            "url": "https://www.****.com/file/2742569/john-newman-ft.-calvin-harris-ole-mp3-download-2016/",
            "trusted": False,
            "nsfw": False
        }
    ]
}
```

#### Nothing Found

```python
{
    "status": 200,
    "message": "OK",
    "data": []
}
```

## Advanced Usage

### Force Fetch Magnet Links

The `parse` method includes an optional parameter `force_fetch_magnet`. When set to `True`, this forces the wrapper to fetch magnet links for all items, even if they are not available by default. This can be useful when you need complete magnet link data for your search results.

```python
try:
    query = "JoJo"
    result = snowfl.parse(query, force_fetch_magnet=True)
    pprint(result)
except FetchError as e:
    print(f"Error searching Snowfl: {e}")
```

## Development

The scraping logic has a single source of truth; the library and the qBittorrent
plugin are generated/derived from it, so there are no hand-maintained duplicates.

```
src/snowfl/core.py     Transport-agnostic core: API-key scraping, URL builders,
                       sort options, exceptions. Stdlib only — all HTTP goes through
                       an injected fetch(url) -> str, so it has no requests dependency.
src/snowfl/            The requests-based library layer (Snowfl.parse / initialize).
plugin/shell.py        qBittorrent plugin template (class snowfl + VERSION header).
tools/build_plugin.py  Deterministic generator that inlines core.py into the template.
engine/snowfl.py       Generated plugin — NOT committed (gitignored); built for tests
                       and published to GitHub Releases by CI.
tests/                 Library tests, live integration tests, and plugin tests.
```

Common tasks (see the `Makefile`):

```bash
make install     # uv sync --extra dev
make test        # unit tests + coverage
make test-live   # live tests that hit snowfl.com
make plugin      # regenerate engine/snowfl.py from core.py + plugin/shell.py
make build       # build the wheel/sdist
```

### Changing the plugin

`engine/snowfl.py` is generated and **not committed** — just edit the sources:

1. Edit `src/snowfl/core.py` and/or `plugin/shell.py`.
2. Open a PR. CI regenerates the plugin, compiles it as stdlib-only, and runs the
   plugin tests (including the real qBittorrent-loader contract test).
3. On merge to `master`, the **plugin release** workflow regenerates the plugin,
   stamps a fresh monotonic version (`# VERSION:` header), and publishes it to
   GitHub Releases — only when the plugin body actually changed.

You never bump the version or commit the artifact by hand; the release workflow owns
both. Run `make plugin` locally if you want to inspect the generated file (it lands
at the gitignored `engine/snowfl.py` with a `0.0` dev version).

## Conclusion

This Python wrapper allows you to interact with the Snowfl API easily, making it convenient to search for torrents and customize your search preferences. Remember to handle exceptions and errors gracefully when using this wrapper in your applications.
