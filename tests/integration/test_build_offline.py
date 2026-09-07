"""Integration: build() with live=null does not require channel."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app
from ux_compose.build import build


def test_build_cek_default_is_require():
    assert inspect.signature(build).parameters["cek"].default == "require"


def test_build_null_live(tmp_path):
    root = create_app(tmp_path / "app", name="t", level=1, host="asgi")
    app, asgi, bundle = build(root, name="t", host="asgi", live="null", level=1)
    assert app is not None
    assert bundle is not None
    assert getattr(app, "_channel", None) is None
    assert getattr(app, "_cek", None) is None


def test_build_source_does_not_import_ux_channel():
    """Isolation: composition root talks Cap through App.use_cek, not ux_channel."""
    src = (ROOT / "src" / "ux_compose" / "build.py").read_text(encoding="utf-8")
    assert "import ux_channel" not in src
    assert "from ux_channel" not in src
    scaffold = (ROOT / "src" / "ux_compose" / "scaffold.py").read_text(encoding="utf-8")
    assert "import ux_channel" not in scaffold
    assert "from ux_channel" not in scaffold
