"""ShareSeat — Shared-element seat: leave #from-sku, arrive #to-sku, same share id.

Ported from the ``motion_xor`` example module (spec §4); this module is canonical and the example imports it.
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
    span,
)

from ux_compose.author import act
from ux_compose import scene, rise

class ShareSeat(Component):
    """Shared-element seat: leave #from-sku, arrive #to-sku, same share id."""

    id = "share"
    place = MorphState("shelf")
    sku = RefState("linen")

    def render(self):
        on_shelf = self.place != "bag"
        kids = (
            header(
                p("scene.share continuity id", className="kicker"),
                h2("Shared element", className="widget-title"),
            ),
            div(
                span("Shelf", id="from-linen", className="chip" + (" is-on" if on_shelf else "")),
                span("Bag", id="to-linen", className="chip" + ("" if on_shelf else " is-on")),
                className="chip-row",
            ),
            act(
                "share.fly",
                "Shelf → bag" if on_shelf else "Bag → shelf",
                kind="primary",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def fly(self):
        going_to_bag = self.place != "bag"
        self.place = "bag" if going_to_bag else "shelf"
        leave, arrive = (
            ("#from-linen", "#to-linen") if going_to_bag else ("#to-linen", "#from-linen")
        )
        plan = (
            scene("line-to-bag")
            .share("sku-linen", leave=leave, arrive=arrive, recipe=rise.enter(ms=120))
            .enter(f"#{self.id}", rise.enter(ms=140))
        )
        return update_with(self, plan, extra_ops=[notify(self.place)])


__all__ = ["ShareSeat"]
