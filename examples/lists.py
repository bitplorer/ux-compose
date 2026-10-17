"""Collections — filter, keyed list, optimistic paint, pagination, undo.

Encoding rule:
  Open/value/query/window  → MorphState (or dirty + RefState if quantity)
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
    App,
)

from ux_compose.components.optimisticlist import OptimisticList
from ux_compose.components.pages import Pages
from ux_compose.components.shelf import Shelf
from ux_compose.components.undosnack import UndoSnack

CATALOG = (("linen", "Work shirt", 48), ("oak", "Serving board", 72), ("wool", "Throw", 96), ("clay", "Pourer", 38))


def demo() -> None:
    app = App.boot("Lists")
    app.add(Shelf, OptimisticList, Pages, UndoSnack)
    print("filter", app.dispatch("shelf.set_query", q="oak"))
    print("opt", app.dispatch("optcart.add_optimistic", sku="tee"))
    print("more", app.dispatch("pages.load_more"))
    print("undo", app.dispatch("undo.remove", sku="oak"))


if __name__ == "__main__":
    demo()
