"""Atelier shop Components — Level 1 author surface.

Progressive Superpower: this module is valid at L1, L2, and L3 unchanged.
Isolation: never imports ux_channel or CEK.
"""
from __future__ import annotations

from typing import Any

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    control,
)

try:
    from ux_compose import scene, rise, fade
except Exception:
    scene = rise = fade = None


CATALOG: list[dict[str, Any]] = [
    {
        "sku": "linen-01",
        "name": "Work shirt",
        "line": "Washed flax, open collar",
        "price": 48,
        "tone": "flax",
        "mark": "shirt",
    },
    {
        "sku": "oak-02",
        "name": "Serving board",
        "line": "Quarter-sawn oak, oil finish",
        "price": 72,
        "tone": "oak",
        "mark": "board",
    },
    {
        "sku": "wool-03",
        "name": "Throw",
        "line": "Undyed merino, blanket stitch",
        "price": 96,
        "tone": "wool",
        "mark": "throw",
    },
    {
        "sku": "clay-04",
        "name": "Pourer",
        "line": "Stoneware, unglazed lip",
        "price": 38,
        "tone": "clay",
        "mark": "pourer",
    },
]

BY_SKU = {p["sku"]: p for p in CATALOG}


def _money(n: int) -> str:
    return f"{int(n)}"


def _product(sku: str) -> dict[str, Any]:
    return BY_SKU.get(sku) or {
        "sku": sku,
        "name": sku,
        "line": "",
        "price": 0,
        "tone": "flax",
        "mark": "shirt",
    }


class Cart(Component):
    """Bag + checkout. checkout is Cap-protected (orders.place)."""

    id = "cart"
    # MorphState default plane is session — Channel refuses quantity values there.
    # Stamp is a non-quantity dirty tick so auto-morph still fires.
    stamp = MorphState("idle")
    notice = RefState("")
    lines = RefState(())  # tuple of (sku, qty)

    def _rows(self) -> list[tuple[str, int]]:
        raw = self.lines or ()
        return [(str(s), int(q)) for s, q in raw]

    def subtotal(self) -> int:
        return sum(_product(s)["price"] * q for s, q in self._rows())

    def render(self) -> str:
        rows = self._rows()
        count = sum(q for _, q in rows)
        notice = str(self.notice or "")
        if not rows:
            body = (
                '<div class="bag-empty">'
                "<p class='bag-empty-title'>The bag is empty</p>"
                "<p class='bag-empty-copy'>Choose a piece from the table. "
                "Nothing is held until you place the order.</p>"
                "</div>"
            )
        else:
            items = []
            for sku, qty in rows:
                p = _product(sku)
                line_total = p["price"] * qty
                rm = control("cart.remove", sku=sku)
                rm_attrs = " ".join(f'{k}="{v}"' for k, v in rm.items())
                items.append(
                    f'<li class="bag-line" id="bag-{sku}">'
                    f'<span class="bag-line-name">{p["name"]}</span>'
                    f'<span class="bag-line-meta">× {qty} · {_money(p["price"])}</span>'
                    f'<span class="bag-line-sum">{_money(line_total)}</span>'
                    f'<form class="inline" method="post" action="/act/cart.remove" data-ux="1" data-target="#cart">'
                    f'<input type="hidden" name="sku" value="{sku}"/>'
                    f'<button type="submit" class="text-btn" {rm_attrs}>Remove</button>'
                    f"</form>"
                    f"</li>"
                )
            co = control("cart.open_checkout")
            co_attrs = " ".join(f'{k}="{v}"' for k, v in co.items())
            body = (
                f'<ul class="bag-lines">{"".join(items)}</ul>'
                f'<div class="bag-foot">'
                f'<span class="bag-label">Subtotal</span>'
                f'<span class="bag-sum">{_money(self.subtotal())}</span>'
                f"</div>"
                f'<form method="post" action="/act/cart.open_checkout" data-ux="1" data-target="#stage">'
                f'<button type="submit" class="btn-primary" {co_attrs}>Review order</button>'
                f"</form>"
            )
        note = f'<p class="bag-notice" role="status">{notice}</p>' if notice else ""
        return (
            f'<aside id="cart" class="bag" data-count="{count}">'
            f'<header class="bag-head">'
            f"<h2>Bag</h2>"
            f'<span class="bag-count">{count}</span>'
            f"</header>"
            f"{note}{body}"
            f"</aside>"
        )

    @action(caps=())
    def add(self, sku: str = "linen-01"):
        p = _product(sku)
        rows = self._rows()
        found = False
        next_rows = []
        for s, q in rows:
            if s == sku:
                next_rows.append((s, q + 1))
                found = True
            else:
                next_rows.append((s, q))
        if not found:
            next_rows.append((sku, 1))
        self.lines = tuple(next_rows)
        self.notice = f"Added {p['name']}"
        self.stamp = "bag"
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("bag-pop").enter("#cart", rise.enter(ms=140))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"Added {p['name']}")])

    @action(caps=())
    def remove(self, sku: str = ""):
        rows = [(s, q) for s, q in self._rows() if s != sku]
        self.lines = tuple(rows)
        self.notice = "Removed"
        self.stamp = "bag" if rows else "idle"
        return update_with(self, extra_ops=[notify("Removed")])

    @action(caps=())
    def open_checkout(self):
        if not self._rows():
            self.notice = "Bag is empty"
            return update_with(self, extra_ops=[notify("Bag is empty")])
        # Modal is a sibling component — Host will also dispatch confirm-modal.open_modal
        return update_with(self)

    @action(caps=("orders.place",))
    def checkout(self):
        if not self._rows():
            self.notice = "Bag is empty"
            return update_with(self, extra_ops=[notify("Bag is empty")])
        total = self.subtotal()
        self.lines = ()
        self.notice = f"Order placed · {_money(total)}"
        self.stamp = "placed"
        plan = None
        if scene is not None and fade is not None:
            try:
                plan = scene("order-placed").enter("#cart", fade.enter(ms=160))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify("Order placed")])


class ConfirmModal(Component):
    id = "confirm-modal"
    open = MorphState(False)
    title = RefState("Place this order")
    body = RefState("")

    def render(self) -> str:
        if not self.open:
            return (
                f'<div id="{self.id}" class="modal" hidden data-open="0"></div>'
            )
        close = control("confirm-modal.close")
        # Checkout is the Cap-protected action on Cart
        ok = control("cart.checkout")
        def fmt(d):
            return " ".join(f'{k}="{v}"' for k, v in d.items())
        return (
            f'<div id="{self.id}" class="modal" data-open="1" role="dialog" '
            f'aria-modal="true" aria-labelledby="confirm-title">'
            f'<div class="modal-scrim"></div>'
            f'<div class="modal-panel">'
            f'<p class="kicker">Order</p>'
            f'<h2 id="confirm-title">{self.title}</h2>'
            f'<p class="modal-copy">{self.body}</p>'
            f'<div class="modal-actions">'
            f'<form method="post" action="/act/confirm-modal.close" data-ux="1" data-target="#stage">'
            f'<button type="submit" class="btn-ghost" {fmt(close)}>Keep looking</button>'
            f"</form>"
            f'<form method="post" action="/act/cart.checkout" data-ux="1" data-target="#stage">'
            f'<button type="submit" class="btn-primary" {fmt(ok)}>Place order</button>'
            f"</form>"
            f"</div>"
            f"</div>"
            f"</div>"
        )

    @action(caps=())
    def open_modal(self, title: str = "Place this order", body: str = ""):
        self.open = True
        self.title = title
        self.body = body
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)


def catalog_grid() -> str:
    cards = []
    for p in CATALOG:
        attrs = control("cart.add", sku=p["sku"])
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        cards.append(
            f'<article class="card tone-{p["tone"]}" id="item-{p["sku"]}">'
            f'<div class="card-mark" aria-hidden="true">{_mark(p["mark"])}</div>'
            f'<header class="card-head">'
            f'<h2>{p["name"]}</h2>'
            f'<p class="price">{_money(p["price"])}</p>'
            f"</header>"
            f'<p class="card-line">{p["line"]}</p>'
            f'<form method="post" action="/act/cart.add" data-ux="1" data-target="#cart">'
            f'<input type="hidden" name="sku" value="{p["sku"]}"/>'
            f'<button type="submit" class="btn-secondary" {attr_str}>Add to bag</button>'
            f"</form>"
            f"</article>"
        )
    return f'<section class="grid" aria-label="Pieces">{"".join(cards)}</section>'


def _mark(kind: str) -> str:
    # Sparse monochrome SVG — no emoji
    if kind == "board":
        return (
            '<svg viewBox="0 0 64 64" width="64" height="64">'
            '<rect x="8" y="18" width="48" height="28" rx="4" fill="none" stroke="currentColor" stroke-width="1.5"/>'
            '<circle cx="20" cy="32" r="3" fill="none" stroke="currentColor" stroke-width="1.5"/>'
            "</svg>"
        )
    if kind == "throw":
        return (
            '<svg viewBox="0 0 64 64" width="64" height="64">'
            '<rect x="14" y="12" width="36" height="40" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/>'
            '<path d="M14 20h36M14 44h36" fill="none" stroke="currentColor" stroke-width="1.2"/>'
            "</svg>"
        )
    if kind == "pourer":
        return (
            '<svg viewBox="0 0 64 64" width="64" height="64">'
            '<path d="M22 18h16l4 10v20a8 8 0 0 1-8 8H26a8 8 0 0 1-8-8V28z" fill="none" stroke="currentColor" stroke-width="1.5"/>'
            '<path d="M42 24h8l2 8" fill="none" stroke="currentColor" stroke-width="1.5"/>'
            "</svg>"
        )
    return (
        '<svg viewBox="0 0 64 64" width="64" height="64">'
        '<path d="M20 18h24v8H20zM18 26h28v24a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4z" '
        'fill="none" stroke="currentColor" stroke-width="1.5"/>'
        '<path d="M32 18v-6" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        "</svg>"
    )
