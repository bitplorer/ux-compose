"""OptimisticList — Paint first, confirm or roll back. Token is RefState (stale guard).

Ported from the ``lists`` example module (spec §4); this module is canonical and the example imports it.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    header,
    ul,
    li,
)

from ux_compose.author import act, mark_dirty

CATALOG = (("linen", "Work shirt", 48), ("oak", "Serving board", 72), ("wool", "Throw", 96), ("clay", "Pourer", 38))

class OptimisticList(Component):
    """Paint first, confirm or roll back. Token is RefState (stale guard)."""

    id = "optcart"
    lines = RefState(())
    pending = MorphState(False)
    token = RefState("")
    dirty = MorphState("idle")

    def render(self):
        rows = list(self.lines or ())
        lis = [li(x, className="pending" if x.endswith("…") else "") for x in rows] or [
            li("Empty bag.", className="muted")
        ]
        kids = (
            header(
                p("Optimistic paint", className="kicker"),
                h2("Optimistic list", className="widget-title"),
            ),
            ul(*lis, className="bag-lines"),
            div(
                act("optcart.add_optimistic", "Add tee (optimistic)", kind="primary", sku="tee"),
                act("optcart.confirm", "Confirm", kind="secondary"),
                act("optcart.rollback", "Roll back", kind="ghost"),
                className="row-actions",
            ),
        )
        return div(
            *kids,
            id=self.id,
            className="widget" + (" is-pending" if self.pending else ""),
        )

    @action(caps=())
    def add_optimistic(self, sku: str = "item"):
        self.lines = tuple(self.lines or ()) + (f"{sku}…",)
        self.pending = True
        self.token = f"tok-{len(self.lines)}"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(f"optimistic {sku}")])

    @action(caps=())
    def confirm(self, token: str = ""):
        _ = token or self.token
        self.lines = tuple(
            x[:-1] if x.endswith("…") else x for x in (self.lines or ())
        )
        self.pending = False
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("confirmed")])

    @action(caps=())
    def rollback(self, token: str = ""):
        _ = token
        self.lines = tuple(x for x in (self.lines or ()) if not x.endswith("…"))
        self.pending = False
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("rolled back")])


__all__ = ["OptimisticList"]
