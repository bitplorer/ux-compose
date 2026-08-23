"""Integration: create-app emits product path files."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app


def test_create_app_layout(tmp_path):
    dest = tmp_path / "demo"
    root = create_app(dest, name="demo", level="auto", host="auto")
    assert (root / "app.py").is_file()
    assert (root / "routes" / "hello.py").is_file()
    assert (root / "README.md").is_file()
    text = (root / "app.py").read_text(encoding="utf-8")
    assert "build(" in text
    assert "asgi" in text
