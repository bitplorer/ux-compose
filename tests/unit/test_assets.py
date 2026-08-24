"""Unit: product asset layout lives on ux-compose."""
from __future__ import annotations

import asyncio
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


def test_discover_css_io_none_without_input(tmp_path):
    root = tmp_path / "empty"
    root.mkdir()
    (root / "app.py").write_text("# no css\n", encoding="utf-8")
    (root / "app").mkdir()
    (root / "app" / "tailwindcss.py").write_text("# leftover showcase compiler\n", encoding="utf-8")
    assert discover_css_io(root) is None


def test_scaffold_settings_imports_compose_webassets(tmp_path):
    root = create_app(tmp_path / "p", name="p")
    settings = (root / "settings.py").read_text(encoding="utf-8")
    document = (root / "document.py").read_text(encoding="utf-8")
    app = (root / "app.py").read_text(encoding="utf-8")
    assert "from ux_compose import WebAssets" in settings
    assert "from ux_dom import WebAssets" not in settings
    assert "webassets=" not in document
    assert "/css/{OUTPUT_CSS}" in document
    assert "from document import document" in app
    assert "from settings import webassets" in app
    # independent tries — Document import must not zero WebAssets
    assert app.count("except Exception:") >= 2


def test_mount_css_requires_asgi(tmp_path):
    wa = WebAssets(base_dir=tmp_path / "assets", dry_run=False)
    try:
        wa.mount_css(None)
        raise AssertionError("expected TypeError")
    except TypeError as e:
        assert "ASGI" in str(e)


def test_mount_css_wraps_plain_asgi(tmp_path):
    wa = WebAssets(base_dir=tmp_path / "assets", dry_run=False)
    wa.output_css.write_text("body{color:red}", encoding="utf-8")

    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    wrapped = wa.mount_css(inner)
    assert wrapped is not inner

    captured = []

    async def send(msg):
        captured.append(msg)

    async def receive():
        return {"type": "http.disconnect"}

    asyncio.run(
        wrapped({"type": "http", "path": "/css/output.css", "method": "GET"}, receive, send)
    )
    start = next(m for m in captured if m["type"] == "http.response.start")
    body = next(m for m in captured if m["type"] == "http.response.body")
    assert start["status"] == 200
    assert b"text/css" in dict(start["headers"]).get(b"content-type", b"")
    assert b"body{color:red}" == body["body"]


def test_mount_css_rejects_traversal(tmp_path):
    wa = WebAssets(base_dir=tmp_path / "assets", dry_run=False)
    secret = tmp_path / "secret.txt"
    secret.write_text("nope", encoding="utf-8")

    async def inner(scope, receive, send):
        raise AssertionError("must not fall through for /css")

    wrapped = wa.mount_css(inner)
    captured = []

    async def send(msg):
        captured.append(msg)

    async def receive():
        return {"type": "http.disconnect"}

    asyncio.run(
        wrapped({"type": "http", "path": "/css/../secret.txt", "method": "GET"}, receive, send)
    )
    start = next(m for m in captured if m["type"] == "http.response.start")
    assert start["status"] == 404
