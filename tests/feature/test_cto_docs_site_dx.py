"""P1 DX: FastAPI /docs collision + create-app reserved dest ``site``.

P1-1: product GET /docs is a Document page, not Swagger.
P1-2: dest folder ``site`` is rejected (stdlib shadow).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main
from ux_compose.scaffold import create_app

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None

DOCS_PAGE = (
    "class Docs:\n"
    "    def render(self):\n"
    "        return '<div id=\"docs\">product-docs</div>'\n"
)


def test_create_app_rejects_reserved_dest_site(tmp_path, capsys):
    dest = tmp_path / "site"
    code = main(["create-app", str(dest)])
    captured = capsys.readouterr()
    text = captured.out + captured.err
    assert code != 0
    assert "site" in text.lower()
    assert "stdlib" in text.lower() or "standard library" in text.lower()
    assert any(name in text.lower() for name in ("fullsite", "app", "web"))
    assert not dest.exists()


def test_create_app_rejects_reserved_dest_email(tmp_path):
    from ux_compose.scaffold import ReservedDestError, create_app as mk

    dest = tmp_path / "email"
    with pytest.raises(ReservedDestError) as exc:
        mk(dest, name="email")
    msg = str(exc.value).lower()
    assert "email" in msg
    assert "fullsite" in msg or "app" in msg or "web" in msg
    assert not dest.exists()


def test_create_app_rejects_reserved_dest_test(tmp_path):
    from ux_compose.scaffold import ReservedDestError, create_app as mk

    dest = tmp_path / "test"
    with pytest.raises(ReservedDestError) as exc:
        mk(dest, name="test")
    msg = str(exc.value).lower()
    assert "test" in msg
    assert "fullsite" in msg or "app" in msg or "web" in msg
    assert not dest.exists()


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI host")
def test_create_app_docs_page_get_is_document_not_swagger(tmp_path):
    from ux_compose.build import build
    from ux_compose.brand import brand_wrap
    from ux_compose.doctor import doctor, scan_fastapi_docs_collision
    from tests.asgi_http import asgi_get

    root = create_app(tmp_path / "fullsite", name="fullsite", level=1, host="fastapi")
    (root / "routes" / "docs.py").write_text(DOCS_PAGE, encoding="utf-8")

    diags = scan_fastapi_docs_collision([root / "routes" / "docs.py"])
    assert diags, "doctor should warn that /docs collides with FastAPI OpenAPI"
    assert any("/docs" in d and "/about" in d for d in diags)
    report = doctor([root], fail=False)
    assert report.ok is True
    assert any("/docs" in d and "/about" in d for d in report.diagnostics)

    pytest.importorskip("ux_dom")
    from ux_dom import Document
    from ux_dom.runtime import Csp
    from ux_dom.dom import title

    document = Document(
        head=[title("DocsShell")], body=[], ensure_csrf_token=False
    ).use(Csp.auto())
    wrap = brand_wrap(document, brand="AcmeDocs")
    _app, asgi, bundle = build(
        root,
        name="fullsite",
        host="fastapi",
        live="null",
        level=1,
        document=document,
        wrap=wrap,
        cek="off",
    )
    assert asgi is not None
    assert bundle is not None
    paths = [r.get("path") for r in (bundle.route_table or [])]
    assert "/docs" in paths

    r = asgi_get(asgi, "/docs")
    assert r.status_code == 200, r.text[:400]
    assert "text/html" in r.headers.get("content-type", "")
    assert "product-docs" in r.text
    assert "AcmeDocs" in r.text
    blob = r.text.lower()
    assert "swagger" not in blob
    assert "swagger-ui" not in blob
