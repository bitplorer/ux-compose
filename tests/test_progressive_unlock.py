"""Progressive unlock is additive and never breaks Level-1 offline."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ux_compose import App, Component, MorphState, action, update_with, notify, Level

HAS_CHANNEL = importlib.util.find_spec("ux_channel") is not None
HAS_MOTION = importlib.util.find_spec("ux_motion") is not None


class Counter(Component):
    id = "c"
    n = MorphState(0)

    def render(self):
        return f"<span id='c'>{self.n}</span>"

    @action(caps=())
    def inc(self):
        self.n = int(self.n) + 1
        return update_with(self, extra_ops=[notify("inc")])


def test_boot_default_is_l1():
    app = App.boot("T")
    assert int(app.level) >= 1


def test_use_channel_absent_or_present_stays_usable():
    """use_channel never breaks L1 dispatch (degrades or elevates honestly)."""
    app = App.boot("T", strict_caps=False).use_behavior()
    app.add(Counter)
    app.use_channel()
    ops = app.dispatch("c.inc")
    assert isinstance(ops, list) and len(ops) >= 1
    if HAS_CHANNEL:
        assert int(app.level) >= 2
    else:
        assert int(app.level) == 1


def test_use_motion_absent_or_present_stays_usable():
    app = App.boot("T", strict_caps=False).use_behavior()
    app.add(Counter)
    app.use_motion()
    ops = app.dispatch("c.inc")
    assert isinstance(ops, list) and len(ops) >= 1
    if HAS_MOTION:
        assert int(app.level) >= 3
    else:
        assert int(app.level) == 1


def test_level_enum_labels():
    assert Level.L1.label == "offline interactive"
    assert Level.L2.label
    assert Level.L3.label


def test_zero_rewrite_same_component_across_unlocks():
    """Same Counter class works before and after unlock attempts."""
    app = App.boot("T", strict_caps=False)
    app.add(Counter)
    ops1 = app.dispatch("c.inc")
    app.use_channel()
    app.use_motion()
    ops2 = app.dispatch("c.inc")
    assert ops1 and ops2
    # Level reflects what actually attached
    if HAS_MOTION:
        assert int(app.level) >= 3
    elif HAS_CHANNEL:
        assert int(app.level) >= 2
    else:
        assert int(app.level) == 1
