"""
Cart + Document SSoT end-to-end (full stack, Python ≥3.14).

Demonstrates the elevated authoring surface in one file:
- Exactly one Document owns the HTML shell
- Unified Component with MorphState + Cap-protected checkout
- update_with for Morph-then-Play (rise enter)
- Progressive unlock: Behavior → Channel → Motion
- Isolation: no product import of ux_channel

Run:
  /tmp/ux314venv/bin/python examples/cart_document.py
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
    control,
    doctor,
)

try:
    from ux_dom import Document
    from ux_dom.dom import div, h1, span, p
    from ux_dom.runtime import XElement, Htmx, Csp
    HAS_DOM = True
except ImportError:
    HAS_DOM = False

try:
    from ux_compose import scene, rise
except Exception:
    scene = rise = None


class Cart(Component):
    id = "cart"
    count = MorphState(0)
    last_sku = RefState("")

    def render(self):
        if HAS_DOM:
            return div(
                h1(f"Cart ({self.count})"),
                p(f"Last: {self.last_sku or '—'}"),
                id=self.id,
                className="cart",
            )
        return (
            f'<div id="{self.id}" class="cart">'
            f"<h1>Cart ({self.count})</h1>"
            f"<p>Last: {self.last_sku or '—'}</p>"
            f"</div>"
        )

    @action(caps=())
    def add(self, sku: str = "item"):
        self.count = int(self.count) + 1
        self.last_sku = sku
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("cart-pop").enter(f"#{self.id}", rise.enter(ms=140))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"Added {sku}")])

    @action(caps=("orders.place",))
    def checkout(self):
        return [notify("Order placed")]


if __name__ == "__main__":
    document = None
    if HAS_DOM:
        document = Document(head=[], body=[], ensure_csrf_token=False).use(
            XElement(),
            Htmx(),
            Csp.auto(),
        )

    app = App.boot("Shop", strict_caps=False)
    if document is not None:
        app.use_dom(document)
    app.use_behavior().use_channel().use_motion()
    app.add(Cart)

    print("Level:", int(app.level), f"({app.level.label})")
    print("Document SSoT:", document is not None and app._document is document)

    ops = app.dispatch("cart.add", sku="tee")
    print("add →")
    for op in ops:
        print(" ", op)

    # Cap Law offline under strict
    strict = App.boot("Shop", strict_caps=True)
    if document is not None:
        strict.use_dom(document)
    strict.use_behavior()
    strict.add(Cart)
    try:
        strict.dispatch("cart.checkout")
        print("UNEXPECTED checkout success")
    except Exception as e:
        print("Cap Law:", type(e).__name__, "— checkout refused offline under strict_caps")

    # Full page render when Document present
    if document is not None:
        inst = Cart()
        inst.count = 1
        inst.last_sku = "tee"
        body = inst.render()
        page = document(body)
        html = str(page)
        print("HTML head snippet:", html[:120].replace("\n", " "))
        print("HTML contains cart:", 'id="cart"' in html or "cart" in html)

    report = doctor([], fail=False)
    print("Doctor ok:", report.ok)
    print("Capabilities:", report.capabilities)
    print("Progressive L" + str(report.level_available))
