"""Wave-2 kit: rating, kanban, timeline, kpi, slider, lightbox, wishlist,
progress, empty, presence, chips, skeleton.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit import (
    Chips,
    Empty,
    Kanban,
    Kpi,
    Lightbox,
    Presence,
    Progress,
    Rating,
    Skeleton,
    Slider,
    Timeline,
    Wishlist,
)


def _boot(*classes, **kwargs):
    app = App.boot("KitWave2", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def test_rating_named_stars():
    app = _boot(Rating, strict_caps=False)
    html = _html(app, "rating")
    assert "How does it sit" in html
    assert 'role="radiogroup"' in html
    assert 'id="rating-star-three"' in html
    assert 'data-stars="three"' in html or "data_stars" in html
    app.dispatch("rating.set", value="five")
    inst = app.behavior.get("rating")
    assert str(inst.stars) == "five"
    html = _html(app, "rating")
    assert "Five" in html
    app.dispatch("rating.set", value="nope")
    inst = app.behavior.get("rating")
    assert str(inst.stars) == "one"


def test_kanban_move_and_archive_cap():
    app = _boot(Kanban, strict_caps=False)
    html = _html(app, "kanban")
    assert "Work shirt" in html
    assert 'id="kanban-card-linen-01"' in html
    app.dispatch("kanban.move", sku="linen-01", to="make")
    inst = app.behavior.get("kanban")
    assert "linen-01" in tuple(inst.make or ())
    assert "linen-01" not in tuple(inst.cut or ())
    html = _html(app, "kanban")
    assert "Work shirt" in html
    app.dispatch("kanban.archive", sku="oak-02")
    inst = app.behavior.get("kanban")
    assert "oak-02" not in tuple(inst.make or ())

    strict = _boot(Kanban, strict_caps=True)
    with pytest.raises(Exception):
        strict.dispatch("kanban.archive", sku="wool-03")


def test_timeline_filter_empty_lane():
    app = _boot(Timeline, strict_caps=False)
    html = _html(app, "timeline")
    assert "Shirt marked" in html
    app.dispatch("timeline.filter", key="cut")
    html = _html(app, "timeline")
    assert "Shirt marked" in html
    assert "Board oiled" not in html
    assert 'data-filt="cut"' in html or "data_filt" in html
    app.dispatch("timeline.filter", key="keep")
    html = _html(app, "timeline")
    assert "Throw folded" in html
    app.dispatch("timeline.filter", key="nope")
    inst = app.behavior.get("timeline")
    assert str(inst.filt) == "all"


def test_kpi_tick_and_reset_cap():
    app = _boot(Kpi, strict_caps=False)
    html = _html(app, "kpi")
    assert "The house today" in html
    inst = app.behavior.get("kpi")
    placed0 = int(inst.placed or 0)
    app.dispatch("kpi.tick_up")
    inst = app.behavior.get("kpi")
    assert int(inst.placed or 0) == placed0 + 1
    app.dispatch("kpi.reset")
    inst = app.behavior.get("kpi")
    assert int(inst.bag or 0) == 0
    assert int(inst.placed or 0) == 0

    strict = _boot(Kpi, strict_caps=True)
    with pytest.raises(Exception):
        strict.dispatch("kpi.reset")


def test_slider_named_band():
    app = _boot(Slider, strict_caps=False)
    html = _html(app, "slider")
    assert "Hold the pour" in html
    assert 'role="meter"' in html
    app.dispatch("slider.set", n="75")
    inst = app.behavior.get("slider")
    assert int(inst.value or 0) == 75
    assert str(inst.band) == "mid"
    html = _html(app, "slider")
    assert "75%" in html
    assert "w-3/4" in html
    app.dispatch("slider.set", n="0")
    inst = app.behavior.get("slider")
    assert str(inst.band) == "empty"
    app.dispatch("slider.set", n="100")
    inst = app.behavior.get("slider")
    assert str(inst.band) == "full"


def test_lightbox_open_named_slide():
    assert "relative" not in Lightbox.class_card
    assert "overflow" not in Lightbox.class_card

    app = _boot(Lightbox, strict_caps=False)
    html = _html(app, "lightbox")
    assert "See the piece" in html
    assert "lightbox-panel" not in html
    app.dispatch("lightbox.open_box", key="oak")
    inst = app.behavior.get("lightbox")
    assert bool(inst.open)
    assert str(inst.slide) == "oak"
    html = _html(app, "lightbox")
    assert "Oak end-grain" in html
    assert 'id="lightbox-panel"' in html
    assert 'id="lightbox-scrim"' in html
    assert 'id="lightbox-prev"' in html
    assert "swipe.right" in html
    assert "swipe.left" in html
    assert 'role="dialog"' in html
    app.dispatch("lightbox.next")
    inst = app.behavior.get("lightbox")
    assert str(inst.slide) == "wool"
    app.dispatch("lightbox.close")
    inst = app.behavior.get("lightbox")
    assert not bool(inst.open)
    html = _html(app, "lightbox")
    assert "lightbox-panel" not in html


def test_wishlist_heart_toggle():
    app = _boot(Wishlist, strict_caps=False)
    html = _html(app, "wishlist")
    assert "Saved to the house" in html
    assert 'id="wishlist-heart-linen"' in html
    inst = app.behavior.get("wishlist")
    assert "linen" in tuple(inst.ids or ())
    app.dispatch("wishlist.toggle", sku="oak")
    inst = app.behavior.get("wishlist")
    assert "oak" in tuple(inst.ids or ())
    html = _html(app, "wishlist")
    assert "2 saved" in html
    app.dispatch("wishlist.toggle", sku="linen")
    inst = app.behavior.get("wishlist")
    assert "linen" not in tuple(inst.ids or ())


def test_progress_phase_and_band():
    app = _boot(Progress, strict_caps=False)
    html = _html(app, "progress")
    assert "On the bench" in html
    assert 'role="progressbar"' in html
    app.dispatch("progress.start")
    inst = app.behavior.get("progress")
    assert str(inst.phase) == "run"
    assert str(inst.band) == "low"
    app.dispatch("progress.bump")
    inst = app.behavior.get("progress")
    assert int(inst.pct or 0) >= 25
    app.dispatch("progress.finish")
    inst = app.behavior.get("progress")
    assert str(inst.phase) == "done"
    assert str(inst.band) == "full"
    html = _html(app, "progress")
    assert "100%" in html
    assert 'data-phase="done"' in html or "data_phase" in html


def test_empty_phases():
    app = _boot(Empty, strict_caps=False)
    html = _html(app, "empty")
    assert "The shelf is quiet" in html
    assert 'data-phase="empty"' in html or "data_phase" in html
    app.dispatch("empty.load")
    html = _html(app, "empty")
    assert "Fetching the table" in html
    assert 'id="empty-s1"' in html
    app.dispatch("empty.fail")
    html = _html(app, "empty")
    assert "could not be reached" in html
    assert 'role="alert"' in html
    app.dispatch("empty.load")
    app.dispatch("empty.ready")
    inst = app.behavior.get("empty")
    assert str(inst.phase) == "ready"
    html = _html(app, "empty")
    assert "Four objects" in html
    app.dispatch("empty.reset")
    inst = app.behavior.get("empty")
    assert str(inst.phase) == "empty"


def test_presence_named_self():
    app = _boot(Presence, strict_caps=False)
    html = _html(app, "presence")
    assert "Who is at the bench" in html
    app.dispatch("presence.set", key="away")
    inst = app.behavior.get("presence")
    assert str(inst.self_state) == "away"
    html = _html(app, "presence")
    assert "Away" in html
    app.dispatch("presence.set", key="focus")
    inst = app.behavior.get("presence")
    assert str(inst.self_state) == "focus"
    app.dispatch("presence.set", key="nope")
    inst = app.behavior.get("presence")
    assert str(inst.self_state) == "here"


def test_chips_add_remove():
    app = _boot(Chips, strict_caps=False)
    html = _html(app, "chips")
    assert "What it is made of" in html
    assert 'id="chips-chip-linen"' in html
    app.dispatch("chips.add", tag="oak")
    inst = app.behavior.get("chips")
    assert "oak" in tuple(inst.tags or ())
    html = _html(app, "chips")
    assert "Oak" in html
    app.dispatch("chips.remove", tag="linen")
    inst = app.behavior.get("chips")
    assert "linen" not in tuple(inst.tags or ())
    app.dispatch("chips.add", tag="oak")
    inst = app.behavior.get("chips")
    assert tuple(inst.tags or ()).count("oak") == 1


def test_skeleton_arrive_reload():
    app = _boot(Skeleton, strict_caps=False)
    html = _html(app, "skeleton")
    assert "Loading the table" in html
    assert 'id="skeleton-hero"' in html
    assert 'data-loading="1"' in html or "data_loading" in html
    app.dispatch("skeleton.arrive")
    inst = app.behavior.get("skeleton")
    assert not bool(inst.loading)
    html = _html(app, "skeleton")
    assert "The table is set" in html
    assert "Quiet pieces" in html
    app.dispatch("skeleton.reload")
    inst = app.behavior.get("skeleton")
    assert bool(inst.loading)
