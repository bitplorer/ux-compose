"""DataTable — DataTable

Ported from the ``table_board`` example module (spec §4); this module is canonical and the example imports it.
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
    span,
)

from ux_compose.author import act, mark_dirty

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
    dirty = MorphState("idle")

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
        return div(*kids, id=self.id, className="widget")

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
        mark_dirty(self)
        return update_with(self)

    @action(caps=("records.archive",))
    def bulk_archive(self):
        n = len(self.selected or ())
        self.selected = ()
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(f"archived {n}")])


__all__ = ["DataTable"]
