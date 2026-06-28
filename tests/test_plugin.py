"""Tests for the generated single-file qBittorrent plugin (engine/snowfl.py).

These run the artifact the way qBittorrent would: with fake `helpers` /
`novaprinter` modules injected, driven by a fake `retrieve_url`. They also guard
that the committed artifact is in sync with its sources.
"""

import importlib.util
import json
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_PATH = os.path.join(ROOT, "engine", "snowfl.py")

HOME_HTML = '<script src="b.min.js?v=1"></script>'
JS_TEXT = 'x findNextItem y "MY_API_KEY"; z'
SEARCH_RESULTS = [
    {
        "name": "Ubuntu 24.04 ISO",
        "size": "3.0 GB",
        "seeder": 42,
        "leecher": 3,
        "site": "linuxtracker",
        "url": "https://example.com/torrent/1",
        "magnet": "magnet:?xt=urn:btih:DEADBEEF",
    }
]


def fake_retrieve_url(url):
    if url == "https://snowfl.com/":
        return HOME_HTML
    if "b.min.js" in url:
        return JS_TEXT
    return json.dumps(SEARCH_RESULTS)


@pytest.fixture
def plugin(monkeypatch):
    """Load engine/snowfl.py with fake qBittorrent modules; returns (module, captured)."""
    captured = []
    helpers = types.ModuleType("helpers")
    helpers.retrieve_url = fake_retrieve_url
    novaprinter = types.ModuleType("novaprinter")
    novaprinter.prettyPrinter = lambda d: captured.append(d)
    monkeypatch.setitem(sys.modules, "helpers", helpers)
    monkeypatch.setitem(sys.modules, "novaprinter", novaprinter)

    spec = importlib.util.spec_from_file_location("snowfl_engine", PLUGIN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, captured


def test_engine_file_exists():
    assert os.path.exists(PLUGIN_PATH), "run `make plugin` to generate engine/snowfl.py"


def test_version_header_first_line():
    with open(PLUGIN_PATH, encoding="utf-8") as f:
        first = f.readline().strip()
    assert first.startswith("# VERSION:"), "qBittorrent needs a `# VERSION:` header on line 1"


def test_no_third_party_imports():
    with open(PLUGIN_PATH, encoding="utf-8") as f:
        src = f.read()
    assert "import requests" not in src
    assert "from snowfl" not in src
    assert "import urllib3" not in src


def test_class_contract(plugin):
    mod, _ = plugin
    assert hasattr(mod, "snowfl")
    engine = mod.snowfl()
    assert engine.name == "Snowfl"
    assert engine.supported_categories == {"all": "0"}
    assert callable(engine.search)
    assert callable(engine.download_torrent)


def test_search_maps_fields_to_prettyprinter(plugin):
    mod, captured = plugin
    mod.snowfl().search("ubuntu")

    assert len(captured) == 1
    row = captured[0]
    assert row == {
        "link": "magnet:?xt=urn:btih:DEADBEEF",
        "name": "Ubuntu 24.04 ISO",
        "size": "3.0 GB",
        "seeds": 42,
        "leech": 3,
        "engine_url": "https://snowfl.com",
        "desc_link": "https://example.com/torrent/1",
    }


def test_download_torrent_magnet_passthrough(plugin, capsys):
    mod, _ = plugin
    mod.snowfl().download_torrent("magnet:?xt=urn:btih:DEADBEEF")
    out = capsys.readouterr().out.strip()
    assert out == "magnet:?xt=urn:btih:DEADBEEF magnet:?xt=urn:btih:DEADBEEF"


def test_generator_output_in_sync():
    """The committed artifact must byte-match a fresh generation."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import build_plugin

    generated = build_plugin.generate()
    with open(PLUGIN_PATH, encoding="utf-8") as f:
        committed = f.read()
    assert generated == committed, "engine/snowfl.py is stale — run `make plugin`"
