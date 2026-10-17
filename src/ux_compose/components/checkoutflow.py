"""CheckoutFlow — Named steps (who / ship / pay / review). Payload in RefState. Place is a Cap.

Ported from the ``commerce_more`` example module (spec §4); this module is canonical and the example imports it.
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
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty

CATALOG = {
    "linen": ("Work shirt", 48),
    "oak": ("Serving board", 72),
    "wool": ("Throw", 96),
    "clay": ("Pourer", 38),
}

class CheckoutFlow(Component):
    """Named steps (who / ship / pay / review). Payload in RefState. Place is a Cap.

    Same shape as the wizard — specialized so a storefront can copy it whole.
    """

    id = "checkout"
    step = MorphState("who")
    name = RefState("")
    ship = MorphState("house")
    pay = MorphState("cap")
    dirty = MorphState("idle")
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
                ),

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
        return div(*kids, id=self.id, className="widget", data_step=step)

    @action(caps=())
    def next(self, name: str = ""):
        if name:
            self.name = name
        order = list(self.STEPS)
        i = order.index(self.step) if self.step in order else 0
        if self.step == "who" and not str(self.name or "").strip():
            return update_with(self, extra_ops=[notify("name required")])
        self.step = order[min(i + 1, len(order) - 1)]
        mark_dirty(self)
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
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("placed")])


__all__ = ["CheckoutFlow"]
