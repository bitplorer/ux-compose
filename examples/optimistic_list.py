"""
Optimistic list pattern — elevated surface.

Demonstrates:
- MorphState list + pending flag (optimistic paint before confirm)
- RefState for silent request token / last error
- Public add (optimistic) + confirm/rollback style Ops via update_with
- Progressive Superpower: same class at every level

When live (L2), a follow_up / continuation would confirm or roll back.
Offline we simulate both paths with plain actions.

Run:
  PYTHONPATH=src python examples/optimistic_list.py
  # or after: pip install -e .
  python -m examples...  (from package root with PYTHONPATH)
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
)


class OptimisticCart(Component):
    id = "opt-cart"
    lines = MorphState(None)       # list[str]
    pending = MorphState(False)
    last_token = RefState("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.lines is None:
            self.lines = []

    def render(self):
        items = self.lines or []
        rows = "".join(f"<li>{x}</li>" for x in items)
        pending = " pending" if self.pending else ""
        attrs = control("add_optimistic", sku="tee")
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return (
            f'<div id="{self.id}" class="cart{pending}">'
            f"<ul>{rows or '<li>Empty</li>'}</ul>"
            f"<button {attr_str}>Add tee (optimistic)</button>"
            f"</div>"
        )

    @action(caps=())
    def add_optimistic(self, sku: str = "item"):
        """Paint immediately; token stored for later confirm/rollback."""
        cur = list(self.lines or [])
        cur.append(f"{sku}…")  # optimistic marker
        self.lines = cur
        self.pending = True
        self.last_token = f"tok-{len(cur)}"
        return update_with(self, extra_ops=[notify(f"Optimistic add {sku}")])

    @action(caps=())
    def confirm(self, token: str = ""):
        """Server confirmed — drop ellipsis marker."""
        tok = token or self.last_token
        cur = [x.replace("…", "") if x.endswith("…") else x for x in (self.lines or [])]
        self.lines = cur
        self.pending = False
        return update_with(self, extra_ops=[notify(f"Confirmed {tok}")])

    @action(caps=())
    def rollback(self, token: str = ""):
        """Server rejected — remove optimistic row."""
        cur = [x for x in (self.lines or []) if not x.endswith("…")]
        self.lines = cur
        self.pending = False
        return update_with(self, extra_ops=[notify("Rolled back")])


if __name__ == "__main__":
    app = App.boot("Shop", strict_caps=False)
    app.add(OptimisticCart)

    print("Level:", int(app.level), f"({app.level.label})")
    print("Optimistic:", app.dispatch("opt-cart.add_optimistic", sku="tee"))
    print("Confirm:", app.dispatch("opt-cart.confirm"))
    print("Optimistic2:", app.dispatch("opt-cart.add_optimistic", sku="hoodie"))
    print("Rollback:", app.dispatch("opt-cart.rollback"))
