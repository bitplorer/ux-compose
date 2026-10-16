"""StockBadge — Qty is RefState. Band is a *derived name* (ok / low / out) stored as MorphState.

Ported from the ``commerce_more`` example module (spec §4); that example stays as the teaching copy.
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
    span,
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty, status

CATALOG = {
    "linen": ("Work shirt", 48),
    "oak": ("Serving board", 72),
    "wool": ("Throw", 96),
    "clay": ("Pourer", 38),
}

class StockBadge(Component):
    """Qty is RefState. Band is a *derived name* (ok / low / out) stored as MorphState.

    Never MorphState(3). The number is silent; the band is what the session plane
    is allowed to see.
    """

    id = "stock"
    qty = RefState(3)
    band = MorphState("low")
    dirty = MorphState("idle")

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
        return div(*kids, id=self.id, className="widget", data_band=band)

    @action(caps=("stock.adjust",))
    def sell(self):
        n = max(0, int(self.qty or 0) - 1)
        self.qty = n
        self.band = self._band(n)
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(str(n))])

    @action(caps=("stock.adjust",))
    def restock(self):
        n = int(self.qty or 0) + 5
        self.qty = n
        self.band = self._band(n)
        mark_dirty(self)
        return update_with(self)


__all__ = ["StockBadge"]
