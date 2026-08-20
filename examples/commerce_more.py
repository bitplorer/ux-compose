"""Commerce extras — wishlist, coupon, checkout, stock, compare.

The elevated cart lives in ``apps/atelier_shop/shop.py`` (and ``examples/cart.py``
as the L1 teaching form). These units cover the rest of a storefront:

    wishlist     ids in RefState + stamp; heart is public
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
    form,
    button,
    control,
)

from examples._common import act, field, tick, status


CATALOG = {
    "linen": ("Work shirt", 48),
    "oak": ("Serving board", 72),
    "wool": ("Throw", 96),
    "clay": ("Pourer", 38),
}


class Wishlist(Component):
    """Heart / unheart is public. The bag (checkout) is a different unit with a Cap."""

    id = "wishlist"
    ids = RefState(("linen",))
    stamp = MorphState("idle")

    def render(self):
        have = tuple(self.ids or ())
        lis = []
        for sku, (name, price) in CATALOG.items():
            on = sku in have
            lis.append(
                li(
                    span(name, className="bag-line-name"),
                    span(str(price), className="muted"),
                    act(
                        "wishlist.toggle",
                        "Saved" if on else "Save",
                        kind="primary" if on else "ghost",
                        sku=sku,
                    ),
                    id=f"wish-{sku}",
                    className="bag-line" + (" is-on" if on else ""),
                )
            )
        kids = (
            header(
                p("Ids silent · heart public", className="kicker"),
                h2("Wishlist", className="widget-title"),
            ),
            p(f"{len(have)} saved. Saving is not placing.", className="lede"),
            ul(*lis, className="bag-lines"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def toggle(self, sku: str = ""):
        cur = set(self.ids or ())
        if sku in cur:
            cur.remove(sku)
        elif sku in CATALOG:
            cur.add(sku)
        self.ids = tuple(s for s in CATALOG if s in cur)
        tick(self)
        return update_with(self, extra_ops=[notify(sku)])


class Coupon(Component):
    """Code is a string MorphState (qualitative). Discount amount is RefState.

    Checking a code is public. Redeeming it (changing the payable) is a Cap.
    """

    id = "coupon"
    code = MorphState("")
    applied = MorphState(False)
    off = RefState(0)
    error = MorphState("")
    stamp = MorphState("idle")
    VALID = {"HOUSE10": 10, "LINEN": 8}

    def render(self):
        kids = (
            header(
                p("Code is a name · redeem is a Cap", className="kicker"),
                h2("Coupon", className="widget-title"),
            ),
            p("Try HOUSE10 or LINEN. Checking is public. Redeeming spends authority.", className="lede"),
            form(
                field("code", str(self.code or ""), placeholder="Code"),
                button("Check", type="submit", className="btn-secondary", **control("coupon.check")),
                method="post",
                action="/act/coupon.check",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            div(
                act("coupon.check", "Check HOUSE10", kind="ghost", code="HOUSE10"),
                act("coupon.redeem", "Redeem (Cap)", kind="primary"),
                act("coupon.clear", "Clear", kind="text"),
                className="row-actions",
            ),
            p(str(self.error), className="error", role="alert") if self.error else p(""),
            status(f"Held · {self.off} off." if self.applied else "", kind="ok"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def check(self, code: str = ""):
        code = (code or str(self.code or "")).strip().upper()
        self.code = code
        self.applied = False
        self.off = 0
        if code in self.VALID:
            self.error = ""
        else:
            self.error = "Unknown code"
        tick(self)
        return update_with(self, extra_ops=[notify("checked")])

    @action(caps=())
    def clear(self):
        self.code = ""
        self.applied = False
        self.off = 0
        self.error = ""
        tick(self)
        return update_with(self)

    @action(caps=("coupons.redeem",))
    def redeem(self):
        code = str(self.code or "").upper()
        if code not in self.VALID:
            self.error = "Check a valid code first"
            tick(self)
            return update_with(self, extra_ops=[notify("blocked")])
        self.applied = True
        self.off = self.VALID[code]
        self.error = ""
        tick(self)
        return update_with(self, extra_ops=[notify(f"off {self.off}")])


class CheckoutFlow(Component):
    """Named steps (who / ship / pay / review). Payload in RefState. Place is a Cap.

    Same shape as the wizard — specialized so a storefront can copy it whole.
    """

    id = "checkout"
    step = MorphState("who")
    name = RefState("")
    ship = MorphState("house")
    pay = MorphState("cap")
    stamp = MorphState("idle")
    STEPS = ("who", "ship", "pay", "review")

    def render(self):
        step = str(self.step or "who")
        body = []
        if step == "who":
            body = [
                p("Who is this for?", className="lede"),
                form(
                    field("name", str(self.name or ""), placeholder="Name"),
                    button("Continue", type="submit", className="btn-primary", **control("checkout.next")),
                    method="post",
                    action="/act/checkout.next",
                    data_ux="1",
                    data_target="#stage",
                    className="stack",
                )
                if HAS_DOM
                else p(""),
            ]
        elif step == "ship":
            body = [
                p(f"Hello {self.name or 'friend'}. Where should it sit?", className="lede"),
                div(
                    act("checkout.set_ship", "The house", kind="primary" if self.ship == "house" else "ghost", key="house"),
                    act("checkout.set_ship", "The studio", kind="primary" if self.ship == "studio" else "ghost", key="studio"),
                    className="seg",
                ),
                act("checkout.next", "Continue", kind="primary"),
                act("checkout.back", "Back", kind="text"),
            ]
        elif step == "pay":
            body = [
                p("Payment is a named method. The charge itself is the Cap on Place.", className="lede"),
                div(
                    act("checkout.set_pay", "Minted Cap", kind="primary" if self.pay == "cap" else "ghost", key="cap"),
                    act("checkout.set_pay", "On account", kind="primary" if self.pay == "account" else "ghost", key="account"),
                    className="seg",
                ),
                act("checkout.next", "Review", kind="primary"),
                act("checkout.back", "Back", kind="text"),
            ]
        else:
            body = [
                p(
                    f"{self.name or 'Friend'} · ship {self.ship} · pay {self.pay}. "
                    "Placing spends orders.place.",
                    className="lede",
                ),
                act("checkout.place", "Place order (Cap)", kind="primary"),
                act("checkout.back", "Back", kind="text"),
            ]
        kids = (
            header(
                p(f"Step {step} · names not ints", className="kicker"),
                h2("Checkout", className="widget-title"),
            ),
            p(" · ".join(self.STEPS), className="muted"),
            *body,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_step=step)
        return f'<div id="{self.id}">{step}</div>'

    @action(caps=())
    def next(self, name: str = ""):
        if name:
            self.name = name
        order = list(self.STEPS)
        i = order.index(self.step) if self.step in order else 0
        if self.step == "who" and not str(self.name or "").strip():
            return update_with(self, extra_ops=[notify("name required")])
        self.step = order[min(i + 1, len(order) - 1)]
        tick(self)
        return update_with(self)

    @action(caps=())
    def back(self):
        order = list(self.STEPS)
        i = order.index(self.step) if self.step in order else 0
        self.step = order[max(0, i - 1)]
        return update_with(self)

    @action(caps=())
    def set_ship(self, key: str = "house"):
        self.ship = key if key in {"house", "studio"} else "house"
        return update_with(self)

    @action(caps=())
    def set_pay(self, key: str = "cap"):
        self.pay = key if key in {"cap", "account"} else "cap"
        return update_with(self)

    @action(caps=("orders.place",))
    def place(self):
        self.step = "who"
        self.name = ""
        tick(self)
        return update_with(self, extra_ops=[notify("placed")])


class StockBadge(Component):
    """Qty is RefState. Band is a *derived name* (ok / low / out) stored as MorphState.

    Never MorphState(3). The number is silent; the band is what the session plane
    is allowed to see.
    """

    id = "stock"
    qty = RefState(3)
    band = MorphState("low")
    stamp = MorphState("idle")

    def _band(self, n: int) -> str:
        if n <= 0:
            return "out"
        if n <= 3:
            return "low"
        return "ok"

    def render(self):
        n = int(self.qty or 0)
        band = str(self.band or self._band(n))
        copy = {
            "ok": "On the table.",
            "low": "A few left. The house is holding them.",
            "out": "Restocking. Not for sale.",
        }[band]
        kids = (
            header(
                p("Qty silent · band named", className="kicker"),
                h2("Stock", className="widget-title"),
            ),
            p(
                span(str(n), className="num"),
                span(band, className=f"chip is-on" if band != "ok" else "chip"),
                className="counter-face",
            ),
            p(copy, className="lede"),
            div(
                act("stock.sell", "Sell one", kind="primary"),
                act("stock.restock", "Restock 5", kind="ghost"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_band=band)
        return f'<div id="{self.id}">{n}</div>'

    @action(caps=())
    def sell(self):
        n = max(0, int(self.qty or 0) - 1)
        self.qty = n
        self.band = self._band(n)
        tick(self)
        return update_with(self, extra_ops=[notify(str(n))])

    @action(caps=())
    def restock(self):
        n = int(self.qty or 0) + 5
        self.qty = n
        self.band = self._band(n)
        tick(self)
        return update_with(self)


class CompareTray(Component):
    """Up to three skus. Selection is a list — RefState + stamp. Not MorphState(int)."""

    id = "compare"
    ids = RefState(("linen", "oak"))
    stamp = MorphState("idle")
    LIMIT = 3

    def render(self):
        have = tuple(self.ids or ())
        lis = []
        for sku, (name, price) in CATALOG.items():
            on = sku in have
            lis.append(
                li(
                    span(name, className="bag-line-name"),
                    span(str(price), className="muted"),
                    act(
                        "compare.toggle",
                        "In tray" if on else "Compare",
                        kind="primary" if on else "ghost",
                        sku=sku,
                    ),
                    id=f"cmp-{sku}",
                    className="bag-line" + (" is-on" if on else ""),
                )
            )
        tray = [
            li(span(CATALOG[s][0], className="bag-line-name"), span(str(CATALOG[s][1]), className="num"), className="bag-line")
            for s in have
        ] or [li("Tray empty.", className="muted")]
        kids = (
            header(
                p("Max three ids", className="kicker"),
                h2("Compare", className="widget-title"),
            ),
            p(f"{len(have)} / {self.LIMIT} in the tray.", className="lede"),
            ul(*lis, className="bag-lines"),
            p("Tray", className="kicker"),
            ul(*tray, className="bag-lines"),
            act("compare.clear", "Clear tray", kind="text"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def toggle(self, sku: str = ""):
        cur = list(self.ids or ())
        if sku in cur:
            cur = [s for s in cur if s != sku]
        elif sku in CATALOG and len(cur) < self.LIMIT:
            cur.append(sku)
        self.ids = tuple(cur)
        tick(self)
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.ids = ()
        tick(self)
        return update_with(self)


def demo() -> None:
    app = App.boot("CommerceMore", strict_caps=False)
    app.add(Wishlist, Coupon, CheckoutFlow, StockBadge, CompareTray)
    print("wish", app.dispatch("wishlist.toggle", sku="oak"))
    print("coup", app.dispatch("coupon.check", code="HOUSE10"))
    print("who", app.dispatch("checkout.next", name="Noor"))
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
