"""Navigation — region swap, master/detail, shared-element seat.

The page does not remount. One Component owns ``mode``. Detail payload is
RefState. Motion Plan is exit/enter recipes with no html=.

Run:
  PYTHONPATH=src:. python examples/navigation.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.masterdetail import MasterDetail
from ux_compose.components.shopview import ShopView

PIECES = {
    "linen": ("Work shirt", "Washed flax, open collar."),
    "oak": ("Serving board", "Quarter-sawn oak, oil finish."),
    "wool": ("Throw", "Undyed merino, blanket stitch."),
}


def demo() -> None:
    app = App.boot("Nav")
    app.add(ShopView, MasterDetail)
    print("detail", app.dispatch("shopview.show_detail", sku="oak"))
    print("list", app.dispatch("shopview.show_list"))
    print("split", app.dispatch("split.select", sku="wool"))


if __name__ == "__main__":
    demo()
