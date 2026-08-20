"""Data table + Kanban.

Sort/select/bulk are MorphState keys (qualitative). Row ids in RefState.
Moving a card is public; *archiving* would take a Cap.

Run:
  PYTHONPATH=src:. python examples/table_board.py
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

from examples._common import act, tick

ROWS = (
    ("linen-01", "Work shirt", "cut", "48"),
    ("oak-02", "Serving board", "make", "72"),
    ("wool-03", "Throw", "keep", "96"),
    ("clay-04", "Pourer", "cut", "38"),
)


class DataTable(Component):
    id = "table"
    sort = MorphState("name")
    selected = RefState(())
    stamp = MorphState("idle")

    def _rows(self):
        idx = {"name": 1, "stage": 2, "price": 3}.get(str(self.sort or "name"), 1)
        return tuple(sorted(ROWS, key=lambda r: r[idx]))

    def render(self):
        sel = set(self.selected or ())
        body = []
        for sku, name, stage, price in self._rows():
            on = sku in sel
            body.append(
                li(
                    span(name, className="bag-line-name"),
                    span(stage, className="chip"),
                    span(price, className="num"),
                    act(
                        "table.toggle_row",
                        "Deselect" if on else "Select",
                        kind="text",
                        sku=sku,
                    ),
                    id=f"row-{sku}",
                    className="bag-line" + (" is-on" if on else ""),
                )
            )
        kids = (
            header(
                p("Sort key MorphState · selection RefState", className="kicker"),
                h2("Data table", className="widget-title"),
            ),
            div(
                act("table.sort_by", "Name", kind="ghost", key="name"),
                act("table.sort_by", "Stage", kind="ghost", key="stage"),
                act("table.sort_by", "Price", kind="ghost", key="price"),
                act("table.bulk_archive", "Archive selected (Cap)", kind="secondary"),
                className="row-actions",
            ),
            ul(*body, className="bag-lines"),
            p(f"{len(sel)} selected", className="muted"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def sort_by(self, key: str = "name"):
        self.sort = key
        return update_with(self)

    @action(caps=())
    def toggle_row(self, sku: str = ""):
        cur = set(self.selected or ())
        if sku in cur:
            cur.remove(sku)
        elif sku:
            cur.add(sku)
        self.selected = tuple(sorted(cur))
        tick(self)
        return update_with(self)

    @action(caps=("records.archive",))
    def bulk_archive(self):
        n = len(self.selected or ())
        self.selected = ()
        tick(self)
        return update_with(self, extra_ops=[notify(f"archived {n}")])


class Kanban(Component):
    id = "kanban"
    cut = RefState(("linen-01", "clay-04"))
    make = RefState(("oak-02",))
    keep = RefState(("wool-03",))
    stamp = MorphState("idle")
    COLS = ("cut", "make", "keep")

    def _col(self, name: str):
        return list(getattr(self, name) or ())

    def render(self):
        names = {s: n for s, n, _, _ in ROWS}
        cols = []
        for col in self.COLS:
            cards = []
            for sku in self._col(col):
                nxt = self.COLS[(self.COLS.index(col) + 1) % 3]
                cards.append(
                    li(
                        span(names.get(sku, sku)),
                        act("kanban.move", f"To {nxt}", kind="text", sku=sku, to=nxt),
                        id=f"card-{sku}",
                        className="card-mini",
                    )
                )
            cols.append(
                div(
                    h2(col.title()),
                    ul(*cards, className="kanban-col"),
                    className="kanban-lane",
                )
            )
        kids = (
            header(
                p("Three RefState columns, one stamp", className="kicker"),
                h2("Kanban", className="widget-title"),
            ),
            div(*cols, className="kanban"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def move(self, sku: str = "", to: str = "make"):
        if to not in self.COLS:
            return update_with(self)
        for col in self.COLS:
            setattr(self, col, tuple(x for x in self._col(col) if x != sku))
        setattr(self, to, tuple(self._col(to) + [sku]))
        tick(self)
        return update_with(self, extra_ops=[notify(f"{sku} → {to}")])


def demo() -> None:
    app = App.boot("Board", strict_caps=False)
    app.add(DataTable, Kanban)
    print("sort", app.dispatch("table.sort_by", key="price"))
    print("sel", app.dispatch("table.toggle_row", sku="oak-02"))
    print("move", app.dispatch("kanban.move", sku="linen-01", to="make"))
    strict = App.boot("Board", strict_caps=True)
    strict.add(DataTable)
    try:
        strict.dispatch("table.bulk_archive")
        print("UNEXPECTED")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
