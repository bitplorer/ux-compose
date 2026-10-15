"""Shortcuts — Keyboard overlay. Same encoding as the command palette — query MorphState.

Ported from the ``ops`` example module (spec §4); that example stays as the teaching copy.
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
    section,
)

from ux_compose.author import act, mark_dirty, status

class Shortcuts(Component):
    """Keyboard overlay. Same encoding as the command palette — query MorphState."""

    id = "shortcuts"
    open = MorphState(False)
    query = MorphState("")
    KEYS = (
        ("g t", "Go to table"),
        ("g b", "Go to bag"),
        ("n", "New note"),
        ("/", "Search"),
        ("?", "Open this overlay"),
    )

    def render(self):
        q = str(self.query or "").lower()
        hits = [(k, lab) for k, lab in self.KEYS if q in k or q in lab.lower()]
        rows = [
            li(
                span(k, className="chip"),
                span(lab),
                className="palette-row",
            )
            for k, lab in hits
        ]
        panel = (
            div(
                p(f"Filter · {q or 'all'}", className="muted"),
                div(
                    act("shortcuts.type", "All", kind="ghost", q=""),
                    act("shortcuts.type", "Go", kind="ghost", q="go"),
                    act("shortcuts.type", "New", kind="ghost", q="new"),
                    className="row-actions",
                ),
                ul(*rows, className="palette-list") if rows else p("No matches.", className="muted"),
                act("shortcuts.close", "Close", kind="ghost"),
                className="palette-panel",
            )
            if self.open
            else act("shortcuts.open_keys", "Open shortcuts", kind="primary")
        )
        kids = (
            header(
                p("Query MorphState", className="kicker"),
                h2("Shortcuts", className="widget-title"),
            ),
            panel,
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def open_keys(self):
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
        self.open = True
        return update_with(self)


__all__ = ["Shortcuts"]
