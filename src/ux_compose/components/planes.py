"""Planes — Side-by-side: mutating only RefState does not morph unless we mark_dirty.

Ported from the ``foundation`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    App,
    Component,
    MorphState,
    RefState,
    action,
    doctor,
    notify,
    update_with,
    div,
    h2,
    p,
    span,
    header,
)

from ux_compose.author import act, optional_plan, mark_dirty

class Planes(Component):
    """Side-by-side: mutating only RefState does not morph unless we mark_dirty."""

    id = "planes"
    shown = MorphState("hello")
    silent = RefState(0)
    dirty = MorphState("idle")

    def render(self):
        kids = (
            header(
                p("MorphState dirties. RefState does not.", className="kicker"),
                h2("Two planes", className="widget-title"),
            ),
            p(
                span(f"shown · {self.shown}", className="chip"),
                span(f"silent · {int(self.silent or 0)}", className="chip"),
                className="chip-row",
            ),
            div(
                act("planes.morph_only", "Change shown", kind="secondary"),
                act("planes.ref_only", "Bump silent (no mark_dirty)", kind="ghost"),
                act("planes.ref_and_mark_dirty", "Bump silent + mark_dirty", kind="primary"),
                className="row-actions",
            ),
            p(
                "Without mark_dirty, RefState memory changes but the patch "
                "may still look like the previous render if you forget to morph.",
                className="muted",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def morph_only(self):
        self.shown = "hello" if self.shown == "there" else "there"
        return update_with(self)

    @action(caps=())
    def ref_only(self):
        self.silent = int(self.silent or 0) + 1
        # Intentionally no mark_dirty — teaching: view will not change.
        return update_with(self)

    @action(caps=())
    def ref_and_mark_dirty(self):
        self.silent = int(self.silent or 0) + 1
        mark_dirty(self)
        return update_with(self)


__all__ = ["Planes"]
