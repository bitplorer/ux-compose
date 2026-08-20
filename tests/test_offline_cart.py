"""Offline Level-1 Cart tests — Progressive Superpower Contract."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ux_compose import App, Component, MorphState, RefState, action, control, notify, update_with


class Cart(Component):
    id = "cart"
    count = MorphState(0)
    last_sku = RefState("")

    def render(self):
        return f"<div id='cart'>Items: {self.count}</div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        self.last_sku = sku
        return update_with(
            self,
            None,
            extra_ops=[notify(f"Added {sku}")],
        )

    @action(caps=("orders.place",))
    def checkout(self):
        return [notify("Checking out…")]


def _is_notify(op) -> bool:
    if isinstance(op, dict):
        return op.get("op") == "notify" or "Added" in str(op) or "message" in op
    # real ux_behavior.Op
    name = getattr(op, "name", None) or ""
    ns = getattr(op, "ns", None) or ""
    payload = getattr(op, "payload", {}) or {}
    return (
        name in ("append", "notify", "toast")
        or ns in ("log", "ui", "notify")
        or "Added" in str(payload)
        or "message" in payload
    )


def _is_morph(op) -> bool:
    if isinstance(op, dict):
        return op.get("op") == "morph"
    name = getattr(op, "name", None) or ""
    ns = getattr(op, "ns", None) or ""
    return name == "morph" or (ns == "ui" and name == "morph")


def test_boot_level1():
    app = App.boot("Shop").use_behavior()
    app.add(Cart)
    assert int(app.level) == 1


def test_offline_dispatch_add():
    app = App.boot("Shop", strict_caps=False).use_behavior()
    app.add(Cart)
    ops = app.dispatch("cart.add", sku="tee")
    assert isinstance(ops, list)
    assert any(_is_notify(o) for o in ops), f"expected notify in {ops}"


def test_public_action_no_cap():
    app = App.boot("Shop", strict_caps=True).use_behavior()
    app.add(Cart)
    ops = app.dispatch("cart.add", sku="tee")
    assert ops  # public succeeds even under strict_caps


def test_protected_action_strict_offline():
    app = App.boot("Shop", strict_caps=True).use_behavior()
    app.add(Cart)
    raised = False
    try:
        app.dispatch("cart.checkout")
    except Exception as e:
        # Real Behavior raises AuthorityError; local shim raises PermissionError
        raised = "Cap" in type(e).__name__ or "Authority" in type(e).__name__ or "Permission" in type(e).__name__ or "Cap" in str(e)
    assert raised, "strict_caps offline must refuse protected action"


def test_control_attrs_offline():
    attrs = control("add", sku="tee")
    assert "data_action" in attrs or "data-ux-action" in attrs or "data-action" in attrs


def test_update_with_produces_morph():
    class C(Component):
        id = "c"
        n = MorphState(0)
        def render(self):
            return f"<div id='c'>{self.n}</div>"
        @action(caps=())
        def inc(self):
            self.n = int(self.n) + 1
            return update_with(self)
    app = App.boot("T", strict_caps=False).use_behavior()
    app.add(C)
    ops = app.dispatch("c.inc")
    assert any(_is_morph(o) for o in ops), f"expected morph in {ops}"


def test_cold_import_surface():
    import ux_compose
    assert hasattr(ux_compose, "Component")
    assert hasattr(ux_compose, "App")
    assert hasattr(ux_compose, "update_with")


if __name__ == "__main__":
    test_boot_level1()
    test_offline_dispatch_add()
    test_public_action_no_cap()
    test_protected_action_strict_offline()
    test_control_attrs_offline()
    test_update_with_produces_morph()
    test_cold_import_surface()
    print("All offline Cart tests passed.")
