"""Integration: build() with live=null does not require channel."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app
from ux_compose.build import build


def test_build_null_live(tmp_path):
    root = create_app(tmp_path / "app", name="t", level=1, host="asgi")
    app, asgi, bundle = build(root, name="t", host="asgi", live="null", level=1)
    assert app is not None
    assert bundle is not None
