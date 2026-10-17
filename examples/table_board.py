"""Data table + Kanban.

Sort/select/bulk are MorphState keys (qualitative). Row ids in RefState.
Moving a card is public; *archiving* would take a Cap.

Run:
  PYTHONPATH=src:. python examples/table_board.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.datatable import DataTable
from ux_compose.components.kanban import Kanban

ROWS = (
    ("linen-01", "Work shirt", "cut", "48"),
    ("oak-02", "Serving board", "make", "72"),
    ("wool-03", "Throw", "keep", "96"),
    ("clay-04", "Pourer", "cut", "38"),
)


def demo() -> None:
    app = App.boot("Board")
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
