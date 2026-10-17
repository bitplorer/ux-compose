"""ProgressMeter — Percent is RefState. Phase is a name (idle / run / done).

Ported from the ``ops`` example module (spec §4); this module is canonical and the example imports it.
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
    span,
)

from ux_compose.author import act, mark_dirty

class ProgressMeter(Component):
    """Percent is RefState. Phase is a name (idle / run / done)."""

    id = "progress"
    pct = RefState(0)
    phase = MorphState("idle")
    dirty = MorphState("idle")

    def render(self):
        n = int(self.pct or 0)
        phase = str(self.phase or "idle")
        band = "empty" if n == 0 else "low" if n < 50 else "mid" if n < 100 else "full"
        kids = (
            header(
                p("Pct silent · phase named", className="kicker"),
                h2("Progress", className="widget-title"),
            ),
            p(
                span(f"{n}%", className="num"),
                span(phase, className="chip"),
                className="counter-face",
            ),
            div(className=f"bar bar-{band}"),
            div(
                act("progress.start", "Start", kind="secondary"),
                act("progress.bump", "Advance", kind="primary"),
                act("progress.finish", "Finish", kind="ghost"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget", data_phase=phase)

    @action(caps=())
    def start(self):
        self.phase = "run"
        self.pct = 10
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def bump(self):
        n = min(100, int(self.pct or 0) + 25)
        self.pct = n
        self.phase = "done" if n >= 100 else "run"
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def finish(self):
        self.pct = 100
        self.phase = "done"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("done")])


__all__ = ["ProgressMeter"]
