"""
Elevated Cart example — demonstrates the frozen mental model.

Progressive Superpower Contract:
  Level 1 offline path works without Channel or Motion.
  Unlocking L2/L3 is pure additive (zero rewrite of this Cart class).

Run:
  PYTHONPATH=src python examples/cart.py
"""
from __future__ import annotations

from ux_compose import (
    App,
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    control,
    doctor,
)

# Optional motion (graceful if not installed)
try:
    from ux_compose import scene, rise
except Exception:
    scene = rise = None


class Cart(Component):
    """One class. One mental model. Works at every progressive level."""

    id = "cart"
    count = MorphState(0)
    last_sku = RefState("")

    def render(self):
        # Pure w.r.t. MorphState / RefState values at dispatch / SSR time.
        attrs = control("add", sku="tee")
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        last = self.last_sku or ""
        return (
            f'<div id="cart" class="cart">'
            f"<h1>Items: {self.count}</h1>"
            f'<span class="last">{last}</span>'
            f"<button {attr_str}>+ tee</button>"
            f"</div>"
        )

    @action(caps=())  # public
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        self.last_sku = sku
        # Prefer update_with when combining state + (optional) motion.
        # Offline: produces morph + notify. Live+Motion: same call, XOR-safe.
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("cart-pop").enter(f"#{self.id}", rise.enter(ms=160))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"Added {sku}")])

    @action(caps=("orders.place",))  # Cap required when live / strict
    def checkout(self):
        return [notify("Checkout started")]


if __name__ == "__main__":
    # Level 1 — offline interactive (no Channel required)
    app = App.boot("Shop", strict_caps=False)
    app.add(Cart)

    ops = app.dispatch("cart.add", sku="tee")
    print("Level:", int(app.level), f"({app.level.label})")
    print("Ops after add:")
    for op in ops:
        print(" ", op)

    # Cap Law: protected action under strict_caps fails closed offline
    app_strict = App.boot("Shop", strict_caps=True)
    app_strict.add(Cart)
    try:
        app_strict.dispatch("cart.checkout")
        print("UNEXPECTED: protected action succeeded offline under strict_caps")
    except Exception as e:
        print(
            "Cap Law (offline strict):",
            type(e).__name__,
            "— protected action refused (fail-closed)",
        )

    # Doctor — protective coach
    report = doctor([], fail=False)
    print("Doctor ok:", report.ok)
    print("Capabilities:", report.capabilities)
    print("Progressive level available: L" + str(report.level_available))

    # Progressive unlock (zero rewrite of Cart)
    # app.use_channel()   # Level 2 when Channel available
    # app.use_motion()    # Level 3 when Motion available
