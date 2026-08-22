"""Page unit: shop.py → Shop — commerce + Cap-protected checkout."""
from __future__ import annotations

from ux_compose import Component, MorphState, RefState, action, control, notify, update_with

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
    lines = RefState(())  # tuple of (sku, qty)
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
        cards = []
        for p in CATALOG:
            q = self._qty(p["sku"])
            add = control("shop.add", sku=p["sku"])
            add_s = " ".join(f'{k}="{v}"' for k, v in add.items())
            cards.append(f'''
<article class="card product">
  <h3>{p["name"]}</h3>
  <p class="muted">{p["blurb"]}</p>
  <div class="row">
    <span class="price">{_money(p["price"])}</span>
    <span class="pill">qty {q}</span>
    <button class="btn primary" {add_s}>Add</button>
  </div>
</article>''')
        total = _money(self._total())
        n = sum(int(q) for _, q in (self.lines or ()))
        place = control("shop.request_checkout")
        place_s = " ".join(f'{k}="{v}"' for k, v in place.items())
        clear = control("shop.clear")
        clear_s = " ".join(f'{k}="{v}"' for k, v in clear.items())
        notice = f'<p class="muted">{self.notice}</p>' if self.notice else ""
        modal = ""
        if self.confirm_open:
            yes = control("shop.checkout")
            no = control("shop.close_confirm")
            yes_s = " ".join(f'{k}="{v}"' for k, v in yes.items())
            no_s = " ".join(f'{k}="{v}"' for k, v in no.items())
            modal = f'''
<div class="modal-backdrop" id="confirm">
  <div class="modal stack">
    <h3>Place order</h3>
    <p class="muted">{n} piece(s) · {total}. Checkout is Cap-protected (<span class="mono">orders.place</span>).</p>
    <div class="row">
      <button class="btn primary" {yes_s}>Confirm</button>
      <button class="btn ghost" {no_s}>Cancel</button>
    </div>
  </div>
</div>'''
        return f'''
<section id="shop" class="stack" style="padding:var(--space-6) 0">
  <div class="row" style="justify-content:space-between">
    <div>
      <h1 style="font-family:var(--font-display);font-size:var(--text-xl);margin:0">Atelier objects</h1>
      <p class="muted">Commerce unit · Morph stamp · Cap-gated checkout</p>
    </div>
    <div class="row">
      <span class="kpi">{total}</span>
      <span class="pill">{n} items</span>
    </div>
  </div>
  <div class="grid">{''.join(cards)}</div>
  <div class="card row" style="justify-content:space-between">
    <div>{notice}<span class="subtle">Offline add works; checkout needs a live Cap at L2.</span></div>
    <div class="row">
      <button class="btn ghost" {clear_s}>Clear</button>
      <button class="btn primary" {place_s}>Checkout</button>
    </div>
  </div>
</section>
{modal}
'''

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
