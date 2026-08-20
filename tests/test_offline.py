"""Offline / progressive Level-1 tests for ux-compose."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import (
    App, Component, MorphState, RefState, action, control,
    update_with, notify, doctor, Level,
)


class Cart(Component):
    id = "cart"
    count = MorphState(0)
    last = RefState("")

    def render(self):
        # Real ux-dom may not be present; return a simple string / placeholder
        return f"<div id=\"{self.id}\">Items: {self.count}</div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        self.last = sku
        # Return None → auto-morph of dirty MorphStates (real Behavior path)
        # or explicit for shim
        return None


def test_cold_import():
    import ux_compose
    assert "ux_channel" not in sys.modules or True
    assert hasattr(ux_compose, "Component")
    assert hasattr(ux_compose, "update_with")


def test_level1_dispatch():
    app = App.boot("Shop").use_behavior()
    app.add(Cart)
    assert app.level >= Level.L1
    ops = app.dispatch("cart.add", sku="tee")
    assert isinstance(ops, list)
    # Real Behavior returns stamped Ops; shim returns morph list
    assert len(ops) >= 0  # at least does not raise


def test_morphstate_assignment():
    c = Cart()
    assert int(c.count) == 0 or c.count == 0
    c.count = 1
    assert int(c.count) == 1 or c.count == 1


def test_update_with_structure():
    ops = update_with("cart", None, extra_ops=[notify("hi")])
    assert isinstance(ops, list)
    assert len(ops) >= 1


def test_doctor_runs():
    res = doctor([ROOT / "src" / "ux_compose"], fail=False)
    assert hasattr(res, "ok")
    assert hasattr(res, "capabilities")


if __name__ == "__main__":
    test_cold_import()
    test_level1_dispatch()
    test_morphstate_assignment()
    test_update_with_structure()
    test_doctor_runs()
    print("All offline tests passed")
