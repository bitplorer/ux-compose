"""Page unit: shop.py → Shop — commerce trees + Cap-gated checkout."""
from __future__ import annotations

from ux_compose import Component, MorphState, RefState, action, control, notify, update_with

try:
    from ux_compose import div, span, h1, h3, p, button, section, article, HAS_DOM
except Exception:
    HAS_DOM = False
    div = span = h1 = h3 = p = button = section = article = None  # type: ignore

CATALOG = (
    {"sku": "linen-throw", "name": "Linen throw", "price": 4800, "blurb": "Stone-washed, heavy drape"},
    {"sku": "oak-tray", "name": "Oak tray", "price": 3200, "blurb": "Hand-finished edge"},
    {"sku": "clay-vessel", "name": "Clay vessel", "price": 5600, "blurb": "Matte glaze, small batch"},
)


def _money(cents: int) -> str:
    return f"${cents / 100:.2f}"


class Shop(Component):
    id = "shop"
    stamp = MorphState("idle")
    notice = RefState("")
    lines = RefState(())
    confirm_open = MorphState(False)

    def _qty(self, sku: str) -> int:
        for s, q in self.lines or ():
            if s == sku:
                return int(q)
        return 0

    def _total(self) -> int:
        price = {p["sku"]: p["price"] for p in CATALOG}
        return sum(price.get(s, 0) * int(q) for s, q in (self.lines or ()))

    def _set_line(self, sku: str, qty: int):
        lines = [(s, q) for s, q in (self.lines or ()) if s != sku]
        if qty > 0:
            lines.append((sku, qty))
        self.lines = tuple(lines)
        self.stamp = "a" if self.stamp == "b" else "b"

    def render(self):
        if not (HAS_DOM and div is not None):
            return f'<section id="shop">cart {_money(self._total())}</section>'

        cards = []
        for prod in CATALOG:
            q = self._qty(prod["sku"])
            cards.append(
                article(
                    h3(prod["name"], className="font-serif text-lg"),
                    p(prod["blurb"], className="mt-1 text-sm text-stone-600 dark:text-stone-400"),
                    div(
                        span(_money(prod["price"]), className="font-mono text-amber-700 dark:text-amber-400"),
                        span(f"qty {q}", className="rounded-full border px-2 py-0.5 text-xs font-mono"),
                        button(
                            "Add", type="button",
                            className="rounded-full bg-stone-900 px-3 py-1.5 text-sm text-stone-50 dark:bg-stone-100 dark:text-stone-900",
                            **control("shop.add", sku=prod["sku"]),
                        ),
                        className="mt-4 flex flex-wrap items-center gap-2",
                    ),
                    className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm dark:border-stone-700 dark:bg-stone-900",
                )
            )
        total = _money(self._total())
        n = sum(int(q) for _, q in (self.lines or ()))
        modal = None
        if self.confirm_open:
            modal = div(
                div(
                    h3("Place order", className="font-serif text-xl"),
                    p(f"{n} piece(s) · {total}. Cap-protected (orders.place).", className="mt-2 text-sm text-stone-600"),
                    div(
                        button("Confirm", type="button", className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50", **control("shop.checkout")),
                        button("Cancel", type="button", className="rounded-full px-4 py-2 text-sm", **control("shop.close_confirm")),
                        className="mt-4 flex gap-2",
                    ),
                    className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-6 shadow-xl dark:border-stone-700 dark:bg-stone-900",
                ),
                className="fixed inset-0 z-30 grid place-items-center bg-black/40 p-4",
                id="confirm",
            )
        notice = p(str(self.notice), className="text-sm text-stone-600") if self.notice else None
        kids = [
            div(
                div(
                    h1("Atelier objects", className="font-serif text-3xl tracking-tight"),
                    p("Commerce · Morph stamp · Cap-gated checkout", className="text-sm text-stone-500"),
                ),
                div(
                    span(total, className="font-serif text-3xl"),
                    span(f"{n} items", className="rounded-full border px-2 py-0.5 text-xs font-mono"),
                    className="flex items-center gap-3",
                ),
                className="flex flex-wrap items-end justify-between gap-4",
            ),
            div(*cards, className="mt-8 grid gap-4 sm:grid-cols-3"),
            div(
                div(notice, span("Offline add works; checkout needs a live Cap at L2.", className="text-xs text-stone-500"), className="space-y-1"),
                div(
                    button("Clear", type="button", className="rounded-full border px-4 py-2 text-sm", **control("shop.clear")),
                    button("Checkout", type="button", className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50", **control("shop.request_checkout")),
                    className="flex gap-2",
                ),
                className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-stone-200 bg-white p-4 dark:border-stone-700 dark:bg-stone-900",
            ),
        ]
        if modal is not None:
            kids.append(modal)
        return section(*kids, id=self.id, className="mx-auto max-w-5xl px-4 py-10")

    @action(caps=())
    def add(self, sku: str = ""):
        if not sku:
            return
        self._set_line(sku, self._qty(sku) + 1)
        self.notice = f"Added {sku}"
        return update_with(self, extra_ops=[notify(f"+ {sku}")])

    @action(caps=())
    def clear(self):
        self.lines = ()
        self.notice = "Cart cleared"
        self.stamp = "a" if self.stamp == "b" else "b"
        return update_with(self)

    @action(caps=())
    def request_checkout(self):
        if not self.lines:
            self.notice = "Cart is empty"
            return update_with(self, extra_ops=[notify("Empty cart")])
        self.confirm_open = True
        return update_with(self)

    @action(caps=())
    def close_confirm(self):
        self.confirm_open = False
        return update_with(self)

    @action(caps=("orders.place",))
    def checkout(self):
        total = _money(self._total())
        self.lines = ()
        self.confirm_open = False
        self.notice = f"Order placed · {total}"
        self.stamp = "a" if self.stamp == "b" else "b"
        return update_with(self, extra_ops=[notify("Order placed")])
