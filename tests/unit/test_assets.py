"""Unit: product asset layout lives on ux-compose."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.assets import CSS_URL_PREFIX, OUTPUT_CSS_NAME, WebAssets
from ux_compose.scaffold import create_app
from ux_compose.tailwind import discover_css_io


def test_layout_paths(tmp_path):
    wa = WebAssets(base_dir=tmp_path / "assets", dry_run=True)
    assert wa.static.css == (tmp_path / "assets" / "static" / "file" / "css").resolve()
    assert wa.output_css.name == OUTPUT_CSS_NAME
    assert wa.css_href == f"{CSS_URL_PREFIX}/{OUTPUT_CSS_NAME}"
    assert not wa.static.css.exists()


def test_ensure_creates_css_js_not_database(tmp_path):
    wa = WebAssets(base_dir=tmp_path / "assets", dry_run=False)
    assert wa.static.css.is_dir()
    assert wa.static.js.is_dir()
    assert not (wa.dir / "database").exists()
    assert not (wa.dir / "upload").exists()
    assert not (wa.dir / "cache").exists()
    assert not (wa.dir / "templates").exists()


def test_discover_css_io_uses_compose_layout(tmp_path):
    root = create_app(tmp_path / "shop", name="shop")
    io = discover_css_io(root)
    assert io is not None
    inp, out = io
    wa = WebAssets.from_app_root(root, dry_run=True)
    assert inp == wa.input_css
    assert out == wa.output_css
    assert out == root / "assets" / "static" / "file" / "css" / "output.css"


def test_scaffold_settings_imports_compose_webassets(tmp_path):
    root = create_app(tmp_path / "p", name="p")
    settings = (root / "settings.py").read_text(encoding="utf-8")
    document = (root / "document.py").read_text(encoding="utf-8")
    assert "from ux_compose import WebAssets" in settings
    assert "from ux_dom import WebAssets" not in settings
    assert "webassets=" not in document
    assert "/css/{OUTPUT_CSS}" in document
