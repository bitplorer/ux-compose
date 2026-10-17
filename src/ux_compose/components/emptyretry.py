"""EmptyRetry — Empty / loading / error / ready are first-class phases — named MorphState.

Ported from the ``feeds`` example module (spec §4); that example stays as the teaching copy.
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
)

from ux_compose.author import act, mark_dirty, status

class EmptyRetry(Component):
    """Empty / loading / error / ready are first-class phases — named MorphState.

    Never ship a blank stage. Retry is public; a billed refetch would take a Cap.
    """

    id = "emptyretry"
    phase = MorphState("empty")
    body = RefState("")
    dirty = MorphState("idle")

    def render(self):
        phase = str(self.phase or "empty")
        if phase == "empty":
            inner = (
                p("The shelf is quiet.", className="lede"),
                act("emptyretry.load", "Load the table", kind="primary"),
            )
        elif phase == "loading":
            inner = (
                p("Fetching the table…", className="muted"),
                div(className="skel"),
                act("emptyretry.fail", "Simulate fail", kind="ghost"),
                act("emptyretry.ready", "Simulate ready", kind="secondary"),
            )
        elif phase == "error":
            inner = (
                p("The table could not be reached.", className="error", role="alert"),
                act("emptyretry.load", "Retry", kind="primary"),
            )
        else:
            inner = (
                p(str(self.body or "Four objects. Linen, oak, wool, clay."), className="lede"),
                status("Ready.", kind="ok"),
                act("emptyretry.reset", "Clear", kind="text"),
            )
        kids = (
            header(
                p("Named phase, never a blank stage", className="kicker"),
                h2("Empty / error / retry", className="widget-title"),
            ),
            *inner,
        )
        return div(*kids, id=self.id, className="widget", data_phase=phase)

    @action(caps=())
    def load(self):
        self.phase = "loading"
        self.body = ""
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def fail(self):
        self.phase = "error"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("error")])

    @action(caps=())
    def ready(self):
        self.phase = "ready"
        self.body = "Quiet pieces for a working house."
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def reset(self):
        self.phase = "empty"
        self.body = ""
        mark_dirty(self)
        return update_with(self)


__all__ = ["EmptyRetry"]
