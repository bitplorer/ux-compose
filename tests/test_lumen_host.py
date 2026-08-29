"""Lumen: Clock A + kit seams + library runtimes. No app JavaScript."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import HAS_DOM
from apps.lumen.host import PRESS
from apps.lumen.seams import ALL, hydrate

LUMEN = ROOT / "apps" / "lumen"


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def _boot():
    PRESS.reset()
    from apps.lumen.app import app

    hydrate(app)
    return app


def _py_files():
    return [p for p in LUMEN.rglob("*.py") if p.is_file()]


def test_all_kit_seams_registered():
    app = _boot()
    ids = {getattr(cls, "id") for cls in ALL}
    assert len(ids) == 35
    for cid in ids:
        assert app.behavior.get(cid) is not None


def test_no_app_javascript_and_no_act_route():
    js = list(LUMEN.rglob("*.js"))
    assert js == []
    app_src = (LUMEN / "app.py").read_text()
    assert "/act" not in app_src
    assert "HTMLResponse" not in app_src
    doc = (LUMEN / "document.py").read_text()
    assert "floor.js" not in doc
    assert "script(src=" not in doc.replace(" ", "")
    for path in _py_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("ux_channel")
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("ux_channel")


def test_lightbox_reads_host_not_standin():
    app = _boot()
    html = _html(app, "lightbox")
    assert "Press folio" in html
    assert "Steel" in html
    assert "Oak end-grain" not in html
    assert "See the piece" in html
    app.dispatch("lightbox.open_box", key="punch")
    assert any(row.get("kind") == "view" and row.get("sku") == "punch" for row in PRESS.ledger)
    inst = app.behavior.get("lightbox")
    assert str(inst.slide) == "punch"


def test_wishlist_writes_host():
    app = _boot()
    html = _html(app, "wishlist")
    assert "Press folio" in html
    assert "Linen work shirt" not in html
    assert "2 saved" in html
    app.dispatch("wishlist.toggle", sku="punch")
    assert "punch" in PRESS.saved
    html = _html(app, "wishlist")
    assert "3 saved" in html
    app.dispatch("wishlist.toggle", sku="folio")
    assert "folio" not in PRESS.saved


def test_kanban_and_rating_hit_host():
    app = _boot()
    html = _html(app, "kanban")
    assert "Press folio" in html
    assert "Work shirt" not in html
    app.dispatch("kanban.move", sku="folio-01", to="make")
    assert "folio-01" in PRESS.lane("make")
    app.dispatch("rating.set", value="five")
    assert PRESS.rating == "five"
    html = _html(app, "rating")
    assert "Five" in html


def test_kpi_sale_and_login_books():
    app = _boot()
    placed0 = PRESS.placed
    app.dispatch("kpi.tick_up")
    assert PRESS.placed == placed0 + 1
    login = app.behavior.get("login")
    ok = login.authenticate(
        email="you@lumen.test",
        password="pressroom1",
        name="",
        signup=False,
    )
    assert ok.ok
    nope = login.authenticate(
        email="you@lumen.test",
        password="wrong",
        name="",
        signup=False,
    )
    assert not nope.ok
    otp = app.behavior.get("otp")
    assert otp.on_verify("000000") is not None
    assert otp.on_verify("314159") is None


def test_timeline_and_chips_from_host():
    app = _boot()
    html = _html(app, "timeline")
    assert "Folio marked" in html
    assert "Shirt marked" not in html
    html = _html(app, "chips")
    assert "Folio" in html
    app.dispatch("chips.add", tag="punch")
    assert "punch" in PRESS.tags
    app.dispatch("chips.remove", tag="folio")
    assert "folio" not in PRESS.tags


def test_clock_a_pages_and_health_json():
    from apps.lumen.app import asgi

    if asgi is None or not callable(getattr(asgi, "get", None)):
        return
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        return
    PRESS.reset()
    from apps.lumen.app import app
    from apps.lumen.seams import hydrate

    hydrate(app)
    client = TestClient(asgi)
    home = client.get("/")
    assert home.status_code == 200
    assert "text/html" in home.headers.get("content-type", "")
    assert "The press keeps the books" in home.text
    assert "floor.js" not in home.text
    assert "lumen.js" not in home.text
    assert "atelier.js" not in home.text
    assert "pulse.js" not in home.text
    folio = client.get("/folio")
    assert folio.status_code == 200
    assert "Press folio" in folio.text
    assert "Oak end-grain" not in folio.text
    gate = client.get("/gate")
    assert "you@lumen.test" in gate.text
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["app"] == "Lumen"
    assert body["ok"] is True


def test_index_page_composes_host_cards():
    app = _boot()
    page = app.behavior.get("index")
    assert page is not None
    html = _html(app, "index")
    assert "The press keeps the books" in html
    assert "The house today" in html
