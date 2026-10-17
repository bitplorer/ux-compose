"""
Modal / sheet pattern — elevated surface.

Demonstrates:
- MorphState for open/closed presence
- RefState for silent payload
- Public open + Cap-protected confirm
- update_with for XOR-safe morph (+ motion Plan)
- Progressive Superpower: same class at L1–L3
- render() returns ux-dom tag trees only (no HTML-string fallback)

Id is ``demomodal`` so it does not collide with the product shop's confirm-modal.

Run:
  PYTHONPATH=src:. python examples/modal.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.confirmmodal import ConfirmModal


if __name__ == "__main__":
    app = App.boot("Shop")
    app.add(ConfirmModal)

    ops = app.dispatch(
        "demomodal.open_modal",
        title="Delete item?",
        body="This cannot be undone.",
    )
    print("Level:", int(app.level), f"({app.level.label})")
    print("Open ops:")
    for op in ops:
        print(" ", op)

    ops = app.dispatch("demomodal.close")
    print("Close ops:", ops)

    strict = App.boot("Shop", strict_caps=True)
    strict.add(ConfirmModal)
    try:
        strict.dispatch("demomodal.confirm")
        print("UNEXPECTED success")
    except Exception as e:
        print("Cap Law:", type(e).__name__, "— confirm refused offline under strict_caps")
