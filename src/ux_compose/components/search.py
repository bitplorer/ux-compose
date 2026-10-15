"""Search — Typeahead / debounced search. Query MorphState; hits RefState; token RefState.

Ported from the ``forms`` example module (spec §4); that example stays as the teaching copy.
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
    form,
    button,
    control,
    span,
)

from ux_compose.author import act, field, mark_dirty

class Search(Component):
    """Typeahead / debounced search. Query MorphState; hits RefState; token RefState.

    Stale responses: bump ``req`` on every type. Ignore results whose token
    no longer matches (Host async). Offline we filter a local catalog.
    """

    id = "search"
    query = MorphState("")
    hits = RefState(())
    req = RefState(0)
    dirty = MorphState("idle")
    CATALOG = ("Work shirt", "Serving board", "Throw", "Pourer", "Oak stool", "Wool cap")

    def render(self):
        q = str(self.query or "")
        rows = list(self.hits or ())
        lis = [li(x, className="hit") for x in rows] or [
            li("Type to filter the table.", className="muted")
        ]
        kids = (
            header(
                p("Stale-token guard on RefState", className="kicker"),
                h2("Search", className="widget-title"),
            ),
            form(
                field("q", q, placeholder="Filter pieces"),
                button("Search", type="submit", className="btn-primary", **control("search.type")),
                method="post",
                action="/act/search.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ),

            ul(*lis, className="hit-list"),
            div(
                act("search.type", "Oak", kind="ghost", q="oak"),
                act("search.type", "Wool", kind="ghost", q="wool"),
                act("search.type", "Clear", kind="text", q=""),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def type(self, q: str = ""):
        self.req = int(self.req or 0) + 1
        token = self.req
        self.query = q
        qn = q.lower()
        found = tuple(x for x in self.CATALOG if qn in x.lower()) if qn else ()
        if token != self.req:
            return []
        self.hits = found
        mark_dirty(self)
        return update_with(self)


__all__ = ["Search"]
