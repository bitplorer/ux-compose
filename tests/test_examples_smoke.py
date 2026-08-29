"""Smoke: every catalog Component adds, renders, and a public verb dispatches."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from ux_compose import App, HAS_DOM


def test_catalog_loads():
    from examples.catalog import PATTERNS, all_components, GROUPS

    assert len(PATTERNS) >= 60
    assert "Foundation" in GROUPS
    comps = all_components()
    ids = [getattr(c, "id", "") for c in comps]
    assert len(ids) == len(set(ids)), f"duplicate Component.id: {ids}"
    slugs = [p["slug"] for p in PATTERNS]
    assert len(slugs) == len(set(slugs)), f"duplicate slug: {slugs}"


def test_each_pattern_renders_and_public_dispatch():
    from examples.catalog import PATTERNS

    app = App.boot("Ex", strict_caps=False)
    classes = []
    for row in PATTERNS:
        classes.append(row["component"])
        classes.extend(row.get("companions") or ())
    app.add(*classes)

    for row in PATTERNS:
        inst = None
        b = app.behavior
        get = getattr(b, "get", None)
        cid = getattr(row["component"], "id", "")
        if callable(get):
            try:
                inst = get(cid)
            except Exception:
                inst = None
        if inst is None:
            inst = row["component"]()
        if HAS_DOM:
            tree = inst.render()
            assert tree is not None
            html = inst.__render__(pretty=False)
            assert cid in html

    # A handful of public verbs — must return a list of Ops.
    for action, kwargs in (
        ("counter.inc", {"sku": "tick"}),
        ("toggle.flip", {}),
        ("tabs.select", {"tab": "make"}),
        ("shelf.set_query", {"q": "oak"}),
        ("search.type", {"q": "wool"}),
        ("stepper.inc", {}),
        ("motionbox.hop", {}),
        ("appshell.go", {"key": "bag"}),
        ("choices.set_finish", {"key": "wax"}),
        ("carousel.next", {}),
        ("wishlist.toggle", {"sku": "oak"}),
        ("progress.bump", {}),
        ("calendar.pick", {"n": "21"}),
        ("rating.set", {"value": "five"}),
        ("kanban.move", {"sku": "linen-01", "to": "make"}),
        ("empty.load", {}),
    ):
        ops = app.dispatch(action, **kwargs)
        assert isinstance(ops, list)


def test_examples_never_import_channel():
    root = ROOT / "examples"
    forbidden = {"ux_channel", "cek", "cek_host"}
    violations = []
    for p in root.rglob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in forbidden:
                        violations.append(f"{p}: import {a.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.split(".")[0] in forbidden:
                    violations.append(f"{p}: from {mod}")
    assert violations == [], violations


def test_protected_actions_fail_closed_offline():
    from examples.foundation import Counter
    from examples.live_caps import LiveOrder

    app = App.boot("Ex", strict_caps=True)
    app.add(Counter, LiveOrder)
    with pytest.raises(Exception):
        app.dispatch("counter.reset")
    with pytest.raises(Exception):
        app.dispatch("liveorder.place")

    from examples.fields import OtpGate
    from examples.commerce_more import Coupon
    from examples.ops import Calendar

    app.add(OtpGate, Coupon, Calendar)
    with pytest.raises(Exception):
        app.dispatch("otpgate.verify")
    with pytest.raises(Exception):
        app.dispatch("coupon.redeem")
    with pytest.raises(Exception):
        app.dispatch("calendar.book")
