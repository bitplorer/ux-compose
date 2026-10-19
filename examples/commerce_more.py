"""Commerce extras — wishlist, coupon, checkout, stock, compare.

The elevated cart lives in ``apps/atelier_shop/shop.py`` (and ``examples/cart.py``
as the L1 teaching form). These units cover the rest of a storefront:

    wishlist     ids in RefState + dirty; heart is public
    coupon       code MorphState (string); redeem is a Cap
    checkout     named steps; place is orders.place
    stock        qty RefState; band is a derived name
    compare      up to three ids in RefState

Money never lives as MorphState(int). Subtotals are derived from Host
catalogs. The verb that charges is Cap-protected.

Run:
  PYTHONPATH=src:. python examples/commerce_more.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.checkoutflow import CheckoutFlow
from ux_compose.components.comparetray import CompareTray
from ux_compose.components.coupon import Coupon
from ux_compose.components.stockbadge import StockBadge
from ux_compose.components.wishlist import Wishlist


CATALOG = {
    "linen": ("Work shirt", 48),
    "oak": ("Serving board", 72),
    "wool": ("Throw", 96),
    "clay": ("Pourer", 38),
}


def demo() -> None:
    app = App.boot("CommerceMore")
    app.add(Wishlist, Coupon, CheckoutFlow, StockBadge, CompareTray)
    print("wish", app.dispatch("wishlist.toggle", sku="oak"))
    print("coup", app.dispatch("coupon.check", code="HOUSE10"))
    print("who", app.dispatch("checkout.next", name="Noor"))
    with app.trust():
        print("stock", app.dispatch("stock.sell"))
    print("cmp", app.dispatch("compare.toggle", sku="wool"))
    strict = App.boot("CommerceMore", strict_caps=True)
    strict.add(Coupon, CheckoutFlow)
    try:
        strict.dispatch("coupon.redeem")
        print("UNEXPECTED redeem")
    except Exception as exc:
        print("Cap Law coupon:", type(exc).__name__)
    try:
        strict.dispatch("checkout.place")
        print("UNEXPECTED place")
    except Exception as exc:
        print("Cap Law checkout:", type(exc).__name__)


if __name__ == "__main__":
    demo()
