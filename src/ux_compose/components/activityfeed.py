"""ActivityFeed — Infinite-ish feed. Cursor is an opaque string MorphState. Items RefState.

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
    ul,
    li,
)

from ux_compose.author import act, mark_dirty

class ActivityFeed(Component):
    """Infinite-ish feed. Cursor is an opaque string MorphState. Items RefState."""

    id = "actfeed"
    items = RefState(("Reserved the throw.", "Oiled the oak board."))
    cursor = MorphState("p1")
    has_more = MorphState(True)
    dirty = MorphState("idle")
    REST = ("Minted a Cap for checkout.", "Marked the work shirt.", "Folded the linen.")

    def render(self):
        rows = list(self.items or ())
        lis = [li(x, className="hit", id=f"act-{i}") for i, x in enumerate(rows)]
        more = (
            act("actfeed.more", "Load earlier", kind="primary")
            if self.has_more
            else p("Beginning of the house.", className="muted")
        )
        kids = (
            header(
                p("Opaque cursor · items silent", className="kicker"),
                h2("Activity", className="widget-title"),
            ),
            ul(*lis, className="hit-list"),
            more,
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def more(self):
        have = list(self.items or ())
        rest = [x for x in self.REST if x not in have]
        take, rest = rest[:2], rest[2:]
        self.items = tuple(have + take)
        self.has_more = bool(rest)
        self.cursor = "end" if not rest else "p2"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("more")])


__all__ = ["ActivityFeed"]
