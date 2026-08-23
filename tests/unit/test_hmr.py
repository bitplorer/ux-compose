"""Unit: HMR client stub and hub."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.hmr import CLIENT_JS, HMR_PATH, HmrHub, client_script_tag


def test_hmr_path():
    assert HMR_PATH.startswith("/")
    assert "hmr" in HMR_PATH


def test_client_script_contains_path():
    tag = client_script_tag()
    assert "<script" in tag
    assert HMR_PATH in tag or HMR_PATH in CLIENT_JS
    assert "WebSocket" in tag or "WebSocket" in CLIENT_JS


def test_hub_add_discard():
    hub = HmrHub()
    class W:
        async def send_text(self, data):
            self.last = data
    w = W()
    hub.add(w)
    hub.discard(w)
