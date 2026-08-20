"""Morph-then-Play + presence continuity with real ux-motion Plans."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_MOTION = importlib.util.find_spec("ux_motion") is not None
HAS_BEHAVIOR = importlib.util.find_spec("ux_behavior") is not None

pytestmark = pytest.mark.skipif(
    not (HAS_MOTION and HAS_BEHAVIOR), reason="ux-motion + ux-behavior required"
)


def test_morph_then_play_order_with_share():
    """Morph Op precedes transition.play; share is valid Plan shape."""
    from ux_compose import update_with, notify
    from ux_motion import scene, rise, fade

    plan = (
        scene("list-share")
        .exit("#old", fade.exit(ms=80))
        .share("item-1", leave="#old", arrive="#new", recipe=rise.enter(ms=100))
        .enter("#new", rise.enter(ms=120))
    )
    ops = update_with("region", plan, extra_ops=[notify("done")])
    assert len(ops) >= 2

    # First Op should be morph (ui.dom.morph)
    first = ops[0]
    first_name = getattr(first, "name", None) or (first.get("op") if isinstance(first, dict) else "")
    first_ns = getattr(first, "ns", "") or ""
    assert "morph" in str(first_name) or "morph" in str(first_ns) or "morph" in str(first)

    # Somewhere a transition.play
    blob = " ".join(str(o) for o in ops)
    assert "transition" in blob or "play" in blob or "plan" in blob


def test_update_with_enforces_no_html_on_plan_when_morph_present():
    """XOR-safe: plan side must not carry html when morph is present."""
    from ux_compose.helpers import _normalize_plan_ops
    from ux_motion import scene, rise

    plan = scene("x").enter("#a", rise.enter(ms=50))
    plan_ops = _normalize_plan_ops(plan)
    for op in plan_ops:
        payload = getattr(op, "payload", None) or (op if isinstance(op, dict) else {})
        plan_body = payload.get("plan") if isinstance(payload, dict) else None
        # Ensure we didn't inject html into the plan
        if isinstance(plan_body, dict):
            assert "html" not in plan_body


def test_dispatch_morph_then_play_real_behavior():
    """End-to-end: @action returns ordered morph + transition.play under real Behavior stamp."""
    from ux_compose import App, Component, MorphState, action, update_with, notify
    from ux_motion import scene, rise

    class Region(Component):
        id = "region"
        label = MorphState("A")

        def render(self):
            return f'<div id="region">{self.label}</div>'

        @action(caps=())
        def flip(self):
            self.label = "B" if self.label == "A" else "A"
            plan = scene("flip").enter("#region", rise.enter(ms=90))
            return update_with(self, plan, extra_ops=[notify("flipped")])

    app = App.boot("T", strict_caps=False).use_behavior().use_motion()
    app.add(Region)
    ops = app.dispatch("region.flip")
    assert ops
    names = []
    for o in ops:
        if hasattr(o, "fq"):
            names.append(o.fq)
        elif hasattr(o, "name"):
            names.append(f"{getattr(o,'ns','')}.{o.name}")
        else:
            names.append(str(o.get("op", o)))
    # morph before play
    joined = " | ".join(names)
    assert "morph" in joined
    assert "play" in joined or "transition" in joined
    # order: morph index < play index
    morph_i = next(i for i, n in enumerate(names) if "morph" in n)
    play_i = next(i for i, n in enumerate(names) if "play" in n or "transition" in n)
    assert morph_i < play_i


def test_stagger_plan_emits_play():
    from ux_compose import update_with
    from ux_motion import scene, rise

    plan = scene("stagger").stagger_in(["#a", "#b", "#c"], rise.enter(ms=60))
    ops = update_with("list", plan)
    assert ops
    blob = str(ops)
    assert "transition" in blob or "play" in blob or "plan" in blob
