"""DateField — Dates are not ints. Window is a name; ISO lives in RefState.

Ported from the ``fields`` example module (spec §4); that example stays as the teaching copy.
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

from ux_compose.author import act, mark_dirty

class DateField(Component):
    """Dates are not ints. Window is a name; ISO lives in RefState.

    Channel would refuse MorphState(20260820). Named windows survive.
    """

    id = "datefield"
    window = MorphState("today")
    iso = RefState("2026-08-20")
    dirty = MorphState("idle")
    WINDOWS = (
        ("today", "Today", "2026-08-20"),
        ("tomorrow", "Tomorrow", "2026-08-21"),
        ("week", "Next week", "2026-08-27"),
    )

    def render(self):
        win = str(self.window or "today")
        segs = [
            act(
                "datefield.set_window",
                lab,
                kind="primary" if key == win else "ghost",
                key=key,
            )
            for key, lab, _ in self.WINDOWS
        ]
        kids = (
            header(
                p("Named window · ISO silent", className="kicker"),
                h2("Date", className="widget-title"),
            ),
            p(f"ISO on the Host plane · {self.iso}", className="lede"),
            div(*segs, className="seg"),
        )
        return div(*kids, id=self.id, className="widget", data_window=win)

    @action(caps=())
    def set_window(self, key: str = "today"):
        row = {k: iso for k, _, iso in self.WINDOWS}.get(key)
        if row is None:
            key, row = "today", "2026-08-20"
        self.window = key
        self.iso = row
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(row)])


__all__ = ["DateField"]
