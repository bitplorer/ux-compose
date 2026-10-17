"""Palette — Command palette. Query is MorphState (must repaint matches).

Ported from the ``overlays`` example module (spec §4); that example stays as the teaching copy.
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
    div,
    h2,
    p,
    header,
    ul,
    li,
    span,
)

from ux_compose.author import act, mark_dirty, optional_plan, optional_slide, optional_fade

class Palette(Component):
    """Command palette. Query is MorphState (must repaint matches)."""

    id = "palette"
    open = MorphState(False)
    query = MorphState("")
    COMMANDS = (
        ("counter.inc", "Increase the counter"),
        ("tabs.select", "Open the Make tab"),
        ("drawer.open_drawer", "Open filters"),
        ("toasts.push", "Push a toast"),
    )

    def render(self):
        q = str(self.query or "").lower()
        hits = [(a, lab) for a, lab in self.COMMANDS if q in lab.lower() or q in a]
        rows = [
            li(act(a, lab, kind="text"), className="palette-row", id=f"cmd-{i}")
            for i, (a, lab) in enumerate(hits[:6])
        ]
        finder = (
            div(
                act("palette.close", "Close", kind="text"),
                p(f"Filter: {q or 'all'}", className="muted"),
                div(
                    act("palette.type", "All", kind="ghost", q=""),
                    act("palette.type", "Toast", kind="ghost", q="toast"),
                    act("palette.type", "Tab", kind="ghost", q="tab"),
                    className="row-actions",
                ),
                ul(*rows, className="palette-list") if rows else p("No matches.", className="muted"),
                className="palette-panel",
            )
            if self.open
            else act("palette.open_pal", "Open palette", kind="primary")
        )
        kids = (
            header(
                p("Query MorphState", className="kicker"),
                h2("Command palette", className="widget-title"),
            ),
            finder,
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def open_pal(self):
        self.open = True
        self.query = ""
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        return update_with(self)


__all__ = ["Palette"]
