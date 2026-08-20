"""
Modal / sheet pattern — elevated surface.

Demonstrates:
- MorphState for open/closed presence
- RefState for silent payload
- Public open + Cap-protected confirm
- update_with for XOR-safe morph (+ optional motion)
- Progressive Superpower: same class at L1–L3
- render() returns ux-dom tags (HTML string fallback without ux-dom)

Run:
  PYTHONPATH=src python examples/modal.py
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
    HAS_DOM,
    div,
    h2,
    p,
    button,
)


class ConfirmModal(Component):
    id = "confirm-modal"
    open = MorphState(False)
    title = RefState("Confirm")
    body = RefState("")

    def render(self):
        if HAS_DOM:
            if not self.open:
                return div(id=self.id, className="modal closed", hidden=True)
            return div(
                h2(str(self.title)),
                p(str(self.body)),
                button("Cancel", **control("close")),
                button("Confirm", **control("confirm")),
                id=self.id,
                className="modal open",
                role="dialog",
            )
        if not self.open:
            return f'<div id="{self.id}" class="modal closed" hidden></div>'
        attrs_close = control("close")
        attrs_ok = control("confirm")

        def fmt(d):
            return " ".join(f'{k}="{v}"' for k, v in d.items())

        return (
            f'<div id="{self.id}" class="modal open" role="dialog">'
            f"<h2>{self.title}</h2>"
            f"<p>{self.body}</p>"
            f'<button {fmt(attrs_close)}>Cancel</button>'
            f'<button {fmt(attrs_ok)}>Confirm</button>'
            f"</div>"
        )

    @action(caps=())
    def open_modal(self, title: str = "Confirm", body: str = ""):
        self.open = True
        self.title = title
        self.body = body
        return update_with(self, extra_ops=[notify(f"Opened: {title}")])

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=("orders.confirm",))
    def confirm(self):
        self.open = False
        return update_with(self, extra_ops=[notify("Confirmed")])


if __name__ == "__main__":
    app = App.boot("Shop", strict_caps=False)
    app.add(ConfirmModal)

    ops = app.dispatch("confirm-modal.open_modal", title="Delete item?", body="This cannot be undone.")
    print("Level:", int(app.level), f"({app.level.label})")
    print("Open ops:")
    for op in ops:
        print(" ", op)

    ops = app.dispatch("confirm-modal.close")
    print("Close ops:", ops)

    # Cap-protected path under strict
    strict = App.boot("Shop", strict_caps=True)
    strict.add(ConfirmModal)
    try:
        strict.dispatch("confirm-modal.confirm")
        print("UNEXPECTED success")
    except Exception as e:
        print("Cap Law:", type(e).__name__, "— confirm refused offline under strict_caps")
