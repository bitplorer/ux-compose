"""Pages — Load-more / pagination. Cursor is an opaque string, not a quantity.

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

from ux_compose.author import act

CATALOG = (("linen", "Work shirt", 48), ("oak", "Serving board", 72), ("wool", "Throw", 96), ("clay", "Pourer", 38))

class Pages(Component):
    """Load-more / pagination. Cursor is an opaque string, not a quantity."""

    id = "pages"
    shown = RefState(("linen", "oak"))
    cursor = MorphState("p1")
    has_more = MorphState(True)
    loading = MorphState(False)
    ALL = ("linen", "oak", "wool", "clay", "stool", "cap", "lamp", "bowl")

    def render(self):
        names = dict((s, n) for s, n, _ in CATALOG)
        names.update({"stool": "Oak stool", "cap": "Wool cap", "lamp": "Clay lamp", "bowl": "Stone bowl"})
        lis = [li(names.get(s, s), id=f"page-{s}") for s in (self.shown or ())]
        more = (
            act("pages.load_more", "Loading…", kind="ghost")
            if self.loading
            else act("pages.load_more", "Load more", kind="primary")
            if self.has_more
            else p("End of the table.", className="muted")
        )
        kids = (
            header(
                p("Opaque cursor", className="kicker"),
                h2("Pagination", className="widget-title"),
            ),
            ul(*lis, className="bag-lines"),
            more,
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def load_more(self):
        self.loading = True
        have = list(self.shown or ())
        rest = [x for x in self.ALL if x not in have]
        take, rest = rest[:2], rest[2:]
        self.shown = tuple(have + take)
        self.has_more = bool(rest)
        self.cursor = "end" if not rest else "p2"
        self.loading = False
        return update_with(self, extra_ops=[notify("loaded")])


__all__ = ["Pages"]
