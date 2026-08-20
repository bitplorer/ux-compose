"""Collections — filter, keyed list, optimistic paint, pagination, undo.

Encoding rule:
  Open/value/query/window  → MorphState (or stamp + RefState if quantity)
  Tokens / pending ids     → RefState
  One-shot message         → notify
  Domain money/stock       → Host, never the client plane

Keyed item ids (``id="item-linen"``) are presence. Morph-then-Play can
stagger surviving nodes later with zero rewrite.

Run:
  PYTHONPATH=src:. python examples/lists.py
"""
from __future__ import annotations

from ux_compose import (
    HAS_DOM,
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

from examples._common import act, tick, maybe_plan, scene, rise

CATALOG = (("linen", "Work shirt", 48), ("oak", "Serving board", 72), ("wool", "Throw", 96), ("clay", "Pourer", 38))


class Shelf(Component):
    """Filter + sort. Query is MorphState. Rows are RefState. Stamp dirties."""

    id = "shelf"
    query = MorphState("")
    order = MorphState("alpha")
    items = RefState(tuple(s for s, _, _ in CATALOG))
    stamp = MorphState("idle")

    def _visible(self):
        q = str(self.query or "").lower()
        by = {s: (n, p) for s, n, p in CATALOG}
        rows = [s for s in (self.items or ()) if q in s or q in by[s][0].lower()]
        if self.order == "price":
            rows = sorted(rows, key=lambda s: by[s][1])
        else:
            rows = sorted(rows, key=lambda s: by[s][0].lower())
        return rows

    def render(self):
        rows = self._visible()
        lis = [
            li(
                span(dict((s, n) for s, n, _ in CATALOG)[s], className="bag-line-name"),
                span(str(dict((s, p) for s, _, p in CATALOG)[s]), className="num"),
                id=f"item-{s}",
                className="bag-line",
            )
            for s in rows
        ] or [li("No pieces match.", className="muted", id="item-empty")]
        kids = (
            header(
                p("Stable item ids", className="kicker"),
                h2("Shelf", className="widget-title"),
            ),
            div(
                act("shelf.set_query", "All", kind="ghost", q=""),
                act("shelf.set_query", "Oak", kind="ghost", q="oak"),
                act("shelf.sort_price", "By price", kind="secondary"),
                act("shelf.sort_alpha", "By name", kind="secondary"),
                className="row-actions",
            ),
            ul(*lis, className="bag-lines"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<ul id="{self.id}"></ul>'

    def _plan(self):
        if scene is None or rise is None:
            return None
        try:
            return (
                scene("shelf-reorder")
                .stagger_in(
                    '[id^="item-"]',
                    rise.enter(ms=90),
                    gap_ms=40,
                )
            )
        except Exception:
            return None

    @action(caps=())
    def set_query(self, q: str = ""):
        self.query = q
        tick(self)
        return update_with(self, self._plan())

    @action(caps=())
    def sort_price(self):
        self.order = "price"
        tick(self)
        return update_with(self, self._plan(), extra_ops=[notify("price")])

    @action(caps=())
    def sort_alpha(self):
        self.order = "alpha"
        tick(self)
        return update_with(self, self._plan())


class OptimisticList(Component):
    """Paint first, confirm or roll back. Token is RefState (stale guard)."""

    id = "optcart"
    lines = RefState(())
    pending = MorphState(False)
    token = RefState("")
    stamp = MorphState("idle")

    def render(self):
        rows = list(self.lines or ())
        lis = [li(x, className="pending" if x.endswith("…") else "") for x in rows] or [
            li("Empty bag.", className="muted")
        ]
        kids = (
            header(
                p("Optimistic paint", className="kicker"),
                h2("Optimistic list", className="widget-title"),
            ),
            ul(*lis, className="bag-lines"),
            div(
                act("optcart.add_optimistic", "Add tee (optimistic)", kind="primary", sku="tee"),
                act("optcart.confirm", "Confirm", kind="secondary"),
                act("optcart.rollback", "Roll back", kind="ghost"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(
                *kids,
                id=self.id,
                className="widget" + (" is-pending" if self.pending else ""),
            )
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def add_optimistic(self, sku: str = "item"):
        self.lines = tuple(self.lines or ()) + (f"{sku}…",)
        self.pending = True
        self.token = f"tok-{len(self.lines)}"
        tick(self)
        return update_with(self, extra_ops=[notify(f"optimistic {sku}")])

    @action(caps=())
    def confirm(self, token: str = ""):
        _ = token or self.token
        self.lines = tuple(
            x[:-1] if x.endswith("…") else x for x in (self.lines or ())
        )
        self.pending = False
        tick(self)
        return update_with(self, extra_ops=[notify("confirmed")])

    @action(caps=())
    def rollback(self, token: str = ""):
        _ = token
        self.lines = tuple(x for x in (self.lines or ()) if not x.endswith("…"))
        self.pending = False
        tick(self)
        return update_with(self, extra_ops=[notify("rolled back")])


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
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

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


class UndoSnack(Component):
    """Delete now, undo window via follow-up-shaped public action."""

    id = "undo"
    items = RefState(("linen", "oak", "wool"))
    gone = RefState("")
    open = MorphState(False)
    stamp = MorphState("idle")

    def render(self):
        names = dict((s, n) for s, n, _ in CATALOG)
        lis = [
            li(
                span(names.get(s, s)),
                act("undo.remove", "Remove", kind="text", sku=s),
                id=f"undo-{s}",
                className="bag-line",
            )
            for s in (self.items or ())
        ] or [li("Nothing on the shelf.", className="muted")]
        snack = (
            div(
                span(f"Removed {self.gone}."),
                act("undo.restore", "Undo", kind="primary"),
                className="snack",
                role="status",
            )
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Undo is a public reverse of a public delete", className="kicker"),
                h2("Undo", className="widget-title"),
            ),
            ul(*lis, className="bag-lines"),
            snack,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def remove(self, sku: str = ""):
        self.items = tuple(s for s in (self.items or ()) if s != sku)
        self.gone = sku
        self.open = True
        tick(self)
        return update_with(self, extra_ops=[notify(f"removed {sku}")])

    @action(caps=())
    def restore(self):
        if self.gone and self.gone not in (self.items or ()):
            self.items = tuple(self.items or ()) + (self.gone,)
        self.gone = ""
        self.open = False
        tick(self)
        return update_with(self, extra_ops=[notify("restored")])


def demo() -> None:
    app = App.boot("Lists", strict_caps=False)
    app.add(Shelf, OptimisticList, Pages, UndoSnack)
    print("filter", app.dispatch("shelf.set_query", q="oak"))
    print("opt", app.dispatch("optcart.add_optimistic", sku="tee"))
    print("more", app.dispatch("pages.load_more"))
    print("undo", app.dispatch("undo.remove", sku="oak"))


if __name__ == "__main__":
    demo()
