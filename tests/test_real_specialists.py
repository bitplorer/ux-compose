"""Integration against real specialists when installed (behavior, motion, channel)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_BEHAVIOR = importlib.util.find_spec("ux_behavior") is not None
HAS_MOTION = importlib.util.find_spec("ux_motion") is not None
HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None

pytestmark = pytest.mark.skipif(not HAS_BEHAVIOR, reason="ux-behavior not installed")


def test_real_behavior_dispatch_and_ops():
    from ux_compose import App, Component, MorphState, action, update_with, notify

    class Cart(Component):
        id = "cart"
        count = MorphState(0)

        def render(self):
            return f"<div id='cart'>{self.count}</div>"

        @action(caps=())
        def add(self, sku: str = ""):
            self.count = int(self.count) + 1
            return update_with(self, extra_ops=[notify(f"Added {sku}")])

    app = App.boot("Shop", strict_caps=False)
    app.add(Cart)
    ops = app.dispatch("cart.add", sku="tee")
    assert ops
    # Real Behavior returns Op objects
    kinds = []
    for o in ops:
        if hasattr(o, "name"):
            kinds.append(f"{getattr(o, 'ns', '')}.{o.name}")
        elif isinstance(o, dict):
            kinds.append(o.get("op", ""))
    assert any("morph" in k or "log" in k or "notify" in k or "append" in k for k in kinds)


def test_real_behavior_cap_law():
    from ux_compose import App, Component, action, notify

    class Locked(Component):
        id = "locked"

        def render(self):
            return "<div id='locked'></div>"

        @action(caps=("secret.do",))
        def do(self):
            return [notify("done")]

    app = App.boot("S", strict_caps=True)
    app.add(Locked)
    with pytest.raises(Exception) as ei:
        app.dispatch("locked.do")
    assert "Cap" in type(ei.value).__name__ or "Authority" in type(ei.value).__name__ or "Cap" in str(ei.value)


@pytest.mark.skipif(not HAS_MOTION, reason="ux-motion not installed")
def test_motion_scene_plan_and_update_with():
    from ux_compose import update_with, notify
    from ux_motion import scene, fade, rise

    plan_builder = scene("pop").enter("#cart", rise.enter(ms=120))
    ops = update_with("cart", plan_builder, extra_ops=[notify("x")])
    assert len(ops) >= 2
    # Should contain morph-like + transition/plan-like
    blob = str(ops)
    assert "cart" in blob or "morph" in blob.lower() or "transition" in blob.lower() or "plan" in blob.lower()


@pytest.mark.skipif(not HAS_MOTION, reason="ux-motion not installed")
def test_motion_reexport_from_compose():
    from ux_compose import scene, fade, rise
    assert scene is not None
    assert fade is not None
    plan = scene("t").enter("#a", fade.enter()).plan()
    assert isinstance(plan, dict)
    assert "id" in plan or "v" in plan or "root" in plan


@pytest.mark.skipif(not HAS_CHANNEL, reason="ux-channel not installed")
def test_use_channel_elevates_level():
    from ux_compose import App
    app = App.boot("S", strict_caps=False).use_behavior().use_channel()
    assert int(app.level) >= 2


@pytest.mark.skipif(not (HAS_CHANNEL and HAS_MOTION), reason="channel+motion required")
def test_full_progressive_unlock_to_l3():
    from ux_compose import App, Component, MorphState, action, update_with, notify

    class C(Component):
        id = "c"
        n = MorphState(0)
        def render(self):
            return f"<i id='c'>{self.n}</i>"
        @action(caps=())
        def inc(self):
            self.n = int(self.n) + 1
            return update_with(self, extra_ops=[notify("n")])

    app = App.boot("S", strict_caps=False)
    app.add(C)
    app.use_channel()
    app.use_motion()
    assert int(app.level) >= 3
    ops = app.dispatch("c.inc")
    assert ops
