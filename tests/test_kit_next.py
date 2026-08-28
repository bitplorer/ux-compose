"""Next-round kit: sidebar, breadcrumb, stepper, carousel, calendar, select, otp, plans."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit import (
    Breadcrumb,
    Calendar,
    Carousel,
    Otp,
    Plans,
    Select,
    Sidebar,
    Stepper,
)


def _boot(*classes, **kwargs):
    app = App.boot("KitNext", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def test_sidebar_select_and_fold():
    app = _boot(Sidebar, strict_caps=False)
    html = _html(app, "sidebar")
    assert "A quiet desk" in html
    app.dispatch("sidebar.select", key="catalog")
    html = _html(app, "sidebar")
    assert "Winter list" in html
    assert 'data-active="catalog"' in html
    app.dispatch("sidebar.toggle")
    inst = app.behavior.get("sidebar")
    assert bool(inst.collapsed)
    html = _html(app, "sidebar")
    assert 'data-collapsed="1"' in html
    assert "Open" in html


def test_breadcrumb_walks_back():
    app = _boot(Breadcrumb, strict_caps=False)
    html = _html(app, "breadcrumb")
    assert "Oak board" in html
    assert 'aria-current="page"' in html
    app.dispatch("breadcrumb.goto", key="catalog")
    inst = app.behavior.get("breadcrumb")
    assert str(inst.here) == "catalog"
    html = _html(app, "breadcrumb")
    assert "Oak board" not in html or html.count("Oak board") == 0
    assert "Catalog" in html
    assert 'data-here="catalog"' in html


def test_stepper_next_finish_cap():
    app = _boot(Stepper, strict_caps=False)
    html = _html(app, "stepper")
    assert "Account" in html
    app.dispatch("stepper.next")
    html = _html(app, "stepper")
    assert "Plan" in html
    app.dispatch("stepper.next")
    html = _html(app, "stepper")
    assert "Review" in html
    assert "Finish" in html
    app.dispatch("stepper.finish")
    html = _html(app, "stepper")
    assert "You're through" in html
    assert 'data-done="1"' in html

    strict = _boot(Stepper, strict_caps=True)
    with pytest.raises(Exception):
        strict.dispatch("stepper.finish")


def test_carousel_wraps():
    app = _boot(Carousel, strict_caps=False)
    app.dispatch("carousel.next")
    inst = app.behavior.get("carousel")
    assert str(inst.slide) == "oak"
    html = _html(app, "carousel")
    assert "Oak serving board" in html
    assert "Previous slide" in html
    assert "Next slide" in html
    if HAS_DOM:
        assert 'data-channel-id="carousel"' in html
        assert 'id="carousel-next"' in html
        assert 'id="carousel-dot-oak"' in html
        assert 'id="carousel-thumb"' in html
        assert "translate3d(1.5rem" in html
        assert "transition-transform" in html
        assert "aria-roledescription" in html
        assert "h-72" in Carousel.class_stage
        assert "min-h-" not in Carousel.class_stage
        assert "absolute" in Carousel.class_dots_row
        assert "inset-x-0" in html
    app.dispatch("carousel.goto", key="clay")
    app.dispatch("carousel.next")
    inst = app.behavior.get("carousel")
    assert str(inst.slide) == "linen"


def test_calendar_month_and_pick():
    app = _boot(Calendar, strict_caps=False)
    html = _html(app, "calendar")
    assert "August 2026" in html
    assert "26" in html
    app.dispatch("calendar.next")
    html = _html(app, "calendar")
    assert "September 2026" in html
    assert 'data-month="2026-09"' in html
    app.dispatch("calendar.pick", day="2026-09-03")
    inst = app.behavior.get("calendar")
    assert str(inst.day) == "2026-09-03"
    html = _html(app, "calendar")
    assert "2026-09-03" in html


def test_select_grouped_choose():
    app = _boot(Select, strict_caps=False)
    html = _html(app, "select")
    assert "Choose a material" in html
    app.dispatch("select.toggle")
    html = _html(app, "select")
    assert "Cloth" in html
    assert "Oak" in html
    app.dispatch("select.choose", key="oak")
    inst = app.behavior.get("select")
    assert str(inst.value) == "oak"
    assert not bool(inst.open)
    html = _html(app, "select")
    assert "Oak" in html
    assert 'data-value="oak"' in html


def test_otp_attach_and_verify():
    app = _boot(Otp, strict_caps=False)
    app.dispatch("otp.verify", code="12")
    html = _html(app, "otp")
    assert "six digits" in html.lower() or "Enter all six" in html
    inst = app.behavior.get("otp")
    assert not bool(inst.ok)
    app.dispatch("otp.verify", code="000000")
    inst = app.behavior.get("otp")
    assert not bool(inst.ok)
    assert "not valid" in str(inst.err)
    app.dispatch("otp.verify", code="123456")
    inst = app.behavior.get("otp")
    assert bool(inst.ok)
    assert str(inst.code or "") == ""
    html = _html(app, "otp")
    assert "Code accepted" in html

    strict = _boot(Otp, strict_caps=True)
    with pytest.raises(Exception):
        strict.dispatch("otp.verify", code="123456")


def test_plans_choose():
    app = _boot(Plans, strict_caps=False)
    html = _html(app, "plans")
    assert "Atelier" in html
    assert "$96" in html
    app.dispatch("plans.choose", key="house")
    inst = app.behavior.get("plans")
    assert str(inst.value) == "house"
    html = _html(app, "plans")
    assert "Selected · House" in html
    assert 'data-value="house"' in html
