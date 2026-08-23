"""Unit: tunnel provider parsing and health probe host."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.tunnel import local_probe_host, parse_provider, provider_available


def test_parse_provider_aliases():
    assert parse_provider("none") == "none"
    assert parse_provider("off") == "none"
    assert parse_provider("ngrok") == "ngrok"
    assert parse_provider("cf") == "cloudflare"
    assert parse_provider("cloudflared") == "cloudflare"


def test_parse_provider_bad():
    with pytest.raises(ValueError):
        parse_provider("wireguard")


def test_local_probe_host_wildcard():
    assert local_probe_host("0.0.0.0") == "127.0.0.1"
    assert local_probe_host("::") == "127.0.0.1"
    assert local_probe_host("127.0.0.1") == "127.0.0.1"


def test_provider_available_none():
    assert provider_available("none") is True
