"""Live integration tests that hit snowfl.com."""

import re

import pytest

from snowfl.snowfl import Snowfl


@pytest.mark.live
def test_live_parse_returns_torrents():
    s = Snowfl()
    s.initialize()
    result = s.parse("ubuntu")

    assert result["status"] == 200
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0

    first = result["data"][0]
    for key in ("name", "site", "seeder", "leecher", "size"):
        assert key in first


@pytest.mark.live
def test_live_parse_with_magnet_fetch():
    s = Snowfl()
    s.initialize()
    result = s.parse("ubuntu", force_fetch_magnet=True)

    assert result["status"] == 200
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0
    assert any(
        isinstance(item.get("magnet"), str)
        and item["magnet"].startswith("magnet:?xt=urn:btih:")
        for item in result["data"]
    )


@pytest.mark.live
def test_live_api_key_shape():
    s = Snowfl()
    s.initialize()

    assert s.api_key is not None
    assert re.match(r"^[A-Za-z0-9_-]+$", s.api_key)
    assert len(s.api_key) > 5
