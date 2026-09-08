"""Kit Batch C marketing leftovers: pricingsection, logocloud, timeline, rating.

Isolation: this file never imports ux_channel. No Cap kernel / cek-runtime / law.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit.catalog import CATALOG, resolve
from ux_compose.kit.copy import copy_component


MARKET_C = ("pricingsection", "logocloud", "timeline", "rating")


def _boot(*classes, **kwargs):
    app = App.boot("KitMarketC", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def _cls(stem: str):
    meta = CATALOG[stem]
    mod = __import__(meta["module"], fromlist=[meta["name"]])
    return getattr(mod, meta["name"])


def test_market_c_resolve():
    for stem in MARKET_C:
        meta = resolve(stem)
        assert meta["stem"] == stem
        assert meta["css"] is False
        assert meta["page"] is True
    assert resolve("pricing-section")["stem"] == "pricingsection"
    assert resolve("logo-cloud")["stem"] == "logocloud"


def test_market_c_document_trees():
    from ux_compose.helpers import _serialize_tree

    for stem in MARKET_C:
        cls = _cls(stem)
        tree = cls().render()
        assert not isinstance(tree, str), stem
        html = _serialize_tree(tree)
        assert f'id="{cls.id}"' in html, stem
        assert "ux_channel" not in html


def test_pricingsection_table_not_plans_radio():
    PricingSection = _cls("pricingsection")
    app = _boot(PricingSection, strict_caps=False)
    html = _html(app, "pricingsection")
    assert "<table" in html
    assert 'scope="col"' in html
    assert 'role="radiogroup"' not in html
    row_start = html.find("<tr")
    row_tag = html[row_start:html.find(">", row_start)]
    assert "pricingsection.choose" not in row_tag

    app.dispatch("pricingsection.choose", key="atelier")
    inst = app.behavior.get("pricingsection")
    assert str(inst.value) == "atelier"
    html = _html(app, "pricingsection")
    assert 'data-value="atelier"' in html


def test_logocloud_named_press():
    LogoCloud = _cls("logocloud")
    app = _boot(LogoCloud, strict_caps=False)
    html = _html(app, "logocloud")
    assert "aria-label" in html
    assert "alt=" in html
    app.dispatch("logocloud.choose", key="oak")
    inst = app.behavior.get("logocloud")
    assert str(inst.value) == "oak"
    html = _html(app, "logocloud")
    assert 'aria-pressed="true"' in html
    assert 'data-value="oak"' in html


def test_timeline_named_filter():
    Timeline = _cls("timeline")
    app = _boot(Timeline, strict_caps=False)
    html = _html(app, "timeline")
    assert 'role="list"' in html or "<ul" in html
    assert 'role="radiogroup"' in html
    app.dispatch("timeline.choose", key="make")
    inst = app.behavior.get("timeline")
    assert str(inst.which) == "make"
    html = _html(app, "timeline")
    assert "Board oiled" in html
    assert "Shirt marked" not in html


def test_rating_named_not_int_morph():
    Rating = _cls("rating")
    app = _boot(Rating, strict_caps=False)
    html = _html(app, "rating")
    assert 'role="radiogroup"' in html
    assert 'role="radio"' in html
    assert "aria-checked" in html
    app.dispatch("rating.choose", key="five")
    inst = app.behavior.get("rating")
    assert str(inst.value) == "five"
    html = _html(app, "rating")
    assert 'data-value="five"' in html


def test_a11y_smoke_market_c():
    app = _boot(*[_cls(s) for s in MARKET_C], strict_caps=False)
    price = _html(app, "pricingsection")
    assert 'scope="col"' in price
    logos = _html(app, "logocloud")
    assert "alt=" in logos
    time = _html(app, "timeline")
    assert 'role="radiogroup"' in time
    rate = _html(app, "rating")
    assert 'role="radio"' in rate


def test_market_c_caps_empty():
    kit = ROOT / "src" / "ux_compose" / "kit"
    for stem in MARKET_C:
        src = (kit / f"{stem}.py").read_text(encoding="utf-8")
        assert "form.submit" not in src
        assert "items.delete" not in src
        assert "auth." not in src


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_copy_market_c(tmp_path: Path):
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    for stem in MARKET_C:
        written = copy_component(stem, root=tmp_path)
        ast.parse(written["py"].read_text(encoding="utf-8"))
