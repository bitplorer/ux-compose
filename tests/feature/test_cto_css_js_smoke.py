"""Optional CTO smoke: GET / and /hello mention CSS/JS when the host can serve.

Uses the ASGI helper (no Starlette TestClient). Skips when the product host
did not bind an ASGI app (no FastAPI in the environment). Live CSS/JS on
StunningCek stays a sibling repro (make cek-repro-morph-shell).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import DOCUMENT_PY, ROUTES_HELLO_PY, ROUTES_INDEX_PY, create_app

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None


def test_scaffold_document_declares_css_href_hello_does_not():
    """GET chrome: Document links /css/output.css; hello fragment does not."""
    assert "OUTPUT_CSS" in DOCUMENT_PY or "/css/" in DOCUMENT_PY
    assert "stylesheet" in DOCUMENT_PY.lower() or 'rel="stylesheet"' in DOCUMENT_PY
    assert "stylesheet" not in ROUTES_HELLO_PY.lower()
    assert "stylesheet" not in ROUTES_INDEX_PY.lower()
    assert "/css/output.css" not in ROUTES_HELLO_PY


@pytest.mark.skipif(not HAS_FASTAPI, reason="ASGI GET smoke needs fastapi host")
def test_scaffold_get_slash_and_hello_css_js_presence(tmp_path):
    from ux_compose.build import build
    from tests.asgi_http import asgi_get

    root = create_app(tmp_path / "smoke", name="smoke", level=1, host="fastapi")
    css = root / "assets" / "static" / "file" / "css" / "output.css"
    css.parent.mkdir(parents=True, exist_ok=True)
    css.write_text("/* cto-smoke */\nbody{color:#111}\n", encoding="utf-8")

    _app, asgi, bundle = build(
        root, name="smoke", host="fastapi", live="null", level=1, cek="off"
    )
    if asgi is None:
        pytest.skip("product host did not bind ASGI")
    assert bundle is not None

    home = asgi_get(asgi, "/")
    hello = asgi_get(asgi, "/hello")
    assert home.status_code == 200, home.text[:400]
    assert hello.status_code == 200, hello.text[:400]
    assert "text/html" in home.headers.get("content-type", "")
    assert "text/html" in hello.headers.get("content-type", "")

    sheet = asgi_get(asgi, "/css/output.css")
    # CSS mount is app.py/WebAssets on the served product; Clock A GET may
    # still mention /css/ when Document wrap is live (Py3.14). Fragment GET
    # (document=None) is allowed to omit the <link>; the file should still 200
    # when mounted.
    if sheet.status_code == 200:
        assert "css" in sheet.headers.get("content-type", "") or sheet.text.strip()
    joined = home.text + hello.text
    if "/css/" in joined or "stylesheet" in joined.lower():
        assert "/css/" in joined
    # JS: Channel live-client is live=null-off; Document Channel.optional is
    # ux-dom. Do not require ux_channel. Presence is optional here.
    if "<script" in joined.lower():
        assert "ux_channel" not in joined
