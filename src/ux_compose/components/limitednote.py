"""LimitedNote — Remaining characters are *derived*. Store the text, not the count, as MorphState.

Ported from the ``fields`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    update_with,
    div,
    h2,
    p,
    header,
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty

class LimitedNote(Component):
    """Remaining characters are *derived*. Store the text, not the count, as MorphState."""

    id = "limited"
    text = RefState("")
    dirty = MorphState("idle")
    LIMIT = 80

    def render(self):
        t = str(self.text or "")
        left = max(0, self.LIMIT - len(t))
        over = len(t) > self.LIMIT
        kids = (
            header(
                p("Count is derived", className="kicker"),
                h2("Limited note", className="widget-title"),
            ),
            p(t or "Write a short note for the maker.", className="lede"),
            p(
                f"{left} left" if not over else f"{len(t) - self.LIMIT} over",
                className="error" if over else "muted",
            ),
            form(
                field("text", t, placeholder="Up to 80 characters"),
                button("Hold", type="submit", className="btn-primary", **control("limited.type")),
                method="post",
                action="/act/limited.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ),

            div(
                act("limited.type", "Short line", kind="ghost", text="Please oil the board."),
                act("limited.type", "Over-limit", kind="ghost", text="x" * 90),
                act("limited.clear", "Clear", kind="text"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def type(self, text: str = ""):
        self.text = text
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.text = ""
        mark_dirty(self)
        return update_with(self)


__all__ = ["LimitedNote"]
