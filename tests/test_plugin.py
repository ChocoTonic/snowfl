"""Tests for the generated single-file qBittorrent plugin (engine/snowfl.py).

These run the artifact the way qBittorrent would: with fake `helpers` /
`novaprinter` modules injected, driven by a fake `retrieve_url`. They also guard
that the committed artifact is in sync with its sources.
"""

import importlib.util
import json
import os
import sys
import time
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
        "age": "2 weeks",
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
    # Source aggregator ("site") is appended to the name; engine_url stays snowfl.
    assert row["link"] == "magnet:?xt=urn:btih:DEADBEEF"
    assert row["name"] == "Ubuntu 24.04 ISO [linuxtracker]"
    assert row["size"] == "3.0 GB"
    assert row["seeds"] == 42
    assert row["leech"] == 3
    assert row["engine_url"] == "https://snowfl.com"
    assert row["desc_link"] == "https://example.com/torrent/1"
    # "2 weeks" ago -> a positive Unix timestamp ~14 days before now.
    assert isinstance(row["pub_date"], int)
    assert abs(row["pub_date"] - (int(time.time()) - 14 * 86400)) < 120


def test_pub_date_derived_from_age(plugin):
    # age_to_pub_date is inlined into the shipped plugin; test it directly.
    mod, _ = plugin
    now = 1_000_000
    assert mod.age_to_pub_date("2 weeks", now) == now - 14 * 86400
    assert mod.age_to_pub_date("6 days", now) == now - 6 * 86400
    assert mod.age_to_pub_date("1 year", now) == now - 31536000
    assert mod.age_to_pub_date("bogus", now) == -1
    assert mod.age_to_pub_date("", now) == -1
    assert mod.age_to_pub_date(None, now) == -1


def test_name_unchanged_when_site_missing(plugin, monkeypatch):
    # A result with no "site" must not get a "[...]" suffix.
    mod, captured = plugin
    no_site = [{"name": "Some Release", "size": "1 GB", "seeder": 1,
                "leecher": 0, "url": "https://x/1", "magnet": "magnet:?xt=urn:btih:AB"}]
    monkeypatch.setattr(mod, "retrieve_url", lambda url: (
        HOME_HTML if url == "https://snowfl.com/"
        else JS_TEXT if "b.min.js" in url
        else json.dumps(no_site)))
    mod.snowfl().search("xyz")
    assert captured[-1]["name"] == "Some Release"


def test_download_torrent_magnet_passthrough(plugin, capsys):
    mod, _ = plugin
    mod.snowfl().download_torrent("magnet:?xt=urn:btih:DEADBEEF")
    out = capsys.readouterr().out.strip()
    assert out == "magnet:?xt=urn:btih:DEADBEEF magnet:?xt=urn:btih:DEADBEEF"


def test_generator_is_deterministic_and_valid():
    """The generator is pure/deterministic and emits valid Python.

    (The artifact is no longer committed — it's generated and published via
    Releases — so there's nothing to byte-compare against; instead pin the
    properties the release pipeline relies on.)
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import build_plugin

    first = build_plugin.generate()
    second = build_plugin.generate()
    assert first == second, "generator must be deterministic"
    compile(first, "<engine/snowfl.py>", "exec")  # must be valid Python


QBT_REF = "release-5.2.0"
QBT_NOVA_RAW = (
    "https://raw.githubusercontent.com/qbittorrent/qBittorrent/"
    "%s/src/searchengine/nova3/%s"
)
QBT_NOVA_FILES = ("nova2.py", "helpers.py", "novaprinter.py", "socks.py")


def test_qbittorrent_loader_contract(tmp_path):
    """Run qBittorrent's real (pinned) nova framework against the generated plugin.

    This is qBittorrent's actual acceptance gate: on install it runs
    ``nova2.py --capabilities`` and registers the engine only if it appears in the
    output, else it reports "Plugin is not supported". We fetch the nova3 framework
    pinned to ``QBT_REF``, drop the generated ``engine/snowfl.py`` into an
    ``engines/`` dir, and run that exact command — so a change that would make the
    plugin unsupported fails here against qBittorrent's own loader.

    Skips (rather than fails) only when the framework can't be downloaded, so a
    network/GitHub outage doesn't masquerade as a plugin regression.
    """
    import subprocess
    import urllib.error
    import urllib.request

    nova_dir = tmp_path / "nova3"
    (nova_dir / "engines").mkdir(parents=True)
    for pkg in (nova_dir, nova_dir / "engines"):
        (pkg / "__init__.py").write_text("", encoding="utf-8")

    try:
        for fname in QBT_NOVA_FILES:
            with urllib.request.urlopen(QBT_NOVA_RAW % (QBT_REF, fname), timeout=30) as resp:
                (nova_dir / fname).write_bytes(resp.read())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip("could not fetch qBittorrent nova framework (%s): %s" % (QBT_REF, exc))

    with open(PLUGIN_PATH, encoding="utf-8") as f:
        (nova_dir / "engines" / "snowfl.py").write_text(f.read(), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(nova_dir / "nova2.py"), "--capabilities"],
        cwd=str(nova_dir),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert "<snowfl>" in proc.stdout, (
        "qBittorrent nova2 (%s) did not register the plugin -> would be "
        "'Plugin is not supported'.\nstdout:\n%s\nstderr:\n%s"
        % (QBT_REF, proc.stdout, proc.stderr)
    )
