"""Floor app: kit cards read the Host, not the kit stand-in."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import HAS_DOM
from apps.floor.host import HOUSE
from apps.floor.seams import ALL, hydrate


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def _boot():
    HOUSE.reset()
    from apps.floor.app import app

    hydrate(app)
    return app


def test_all_kit_seams_registered():
    app = _boot()
    ids = {getattr(cls, "id") for cls in ALL}
    assert len(ids) == 35
    for cid in ids:
        assert app.behavior.get(cid) is not None


def test_lightbox_reads_host_not_standin():
    app = _boot()
    html = _html(app, "lightbox")
    assert "Flax apron" in html
    assert "Walnut" in html
    assert "Oak end-grain" not in html
    assert "See the piece" in html
    app.dispatch("lightbox.open_box", key="walnut")
    assert any(row.get("kind") == "view" and row.get("sku") == "walnut" for row in HOUSE.ledger)
    inst = app.behavior.get("lightbox")
    assert str(inst.slide) == "walnut"


def test_wishlist_writes_host():
    app = _boot()
    html = _html(app, "wishlist")
    assert "Flax apron" in html
    assert "Linen work shirt" not in html
    assert "2 saved" in html
    app.dispatch("wishlist.toggle", sku="walnut")
    assert "walnut" in HOUSE.saved
    html = _html(app, "wishlist")
    assert "3 saved" in html
    app.dispatch("wishlist.toggle", sku="flax")
    assert "flax" not in HOUSE.saved


def test_kanban_and_rating_hit_host():
    app = _boot()
    html = _html(app, "kanban")
    assert "Flax apron" in html
    assert "Work shirt" not in html
    app.dispatch("kanban.move", sku="flax-01", to="make")
    assert "flax-01" in HOUSE.lane("make")
    app.dispatch("rating.set", value="five")
    assert HOUSE.rating == "five"
    html = _html(app, "rating")
    assert "Five" in html


def test_kpi_sale_and_login_books():
    app = _boot()
    html = _html(app, "kpi")
    assert "The house today" in html
    placed0 = HOUSE.placed
    app.dispatch("kpi.tick_up")
    assert HOUSE.placed == placed0 + 1
    login = app.behavior.get("login")
    ok = login.authenticate(
        email="you@floor.test",
        password="housewood1",
        name="",
        signup=False,
    )
    assert ok.ok
    nope = login.authenticate(
        email="you@floor.test",
        password="wrong",
        name="",
        signup=False,
    )
    assert not nope.ok
    otp = app.behavior.get("otp")
    assert otp.on_verify("000000") is not None
    assert otp.on_verify("246810") is None


def test_timeline_and_chips_from_host():
    app = _boot()
    html = _html(app, "timeline")
    assert "Apron marked" in html
    assert "Shirt marked" not in html
    html = _html(app, "chips")
    assert "Flax" in html
    app.dispatch("chips.add", tag="walnut")
    assert "walnut" in HOUSE.tags
    app.dispatch("chips.remove", tag="flax")
    assert "flax" not in HOUSE.tags


def test_index_page_composes_host_cards():
    app = _boot()
    page = app.behavior.get("index")
    assert page is not None
    html = _html(app, "index")
    assert "The house keeps the books" in html
    assert "Host ledger" in html
    assert "The house today" in html
