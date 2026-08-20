"""Atelier shop Components — Level 1 author surface.

render() returns ux-dom tag trees. The same Cart class is valid at L1–L3.
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
    HAS_DOM,
    div,
    span,
    h2,
    p,
    header,
    aside,
    section,
    article,
    ul,
    li,
    form,
    input_,
    button,
    svg,
    path,
    rect,
    circle,
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


def _mark(kind: str):
    """Sparse monochrome SVG — no emoji."""
    if not HAS_DOM:
        return ""
    if kind == "board":
        return svg(
            rect(x="8", y="18", width="48", height="28", rx="4", fill="none", stroke="currentColor", stroke_width="1.5"),
            circle(cx="20", cy="32", r="3", fill="none", stroke="currentColor", stroke_width="1.5"),
            viewBox="0 0 64 64",
            width="64",
            height="64",
        )
    if kind == "throw":
        return svg(
            rect(x="14", y="12", width="36", height="40", rx="2", fill="none", stroke="currentColor", stroke_width="1.5"),
            path(d="M14 20h36M14 44h36", fill="none", stroke="currentColor", stroke_width="1.2"),
            viewBox="0 0 64 64",
            width="64",
            height="64",
        )
    if kind == "pourer":
        return svg(
            path(d="M22 18h16l4 10v20a8 8 0 0 1-8 8H26a8 8 0 0 1-8-8V28z", fill="none", stroke="currentColor", stroke_width="1.5"),
            path(d="M42 24h8l2 8", fill="none", stroke="currentColor", stroke_width="1.5"),
            viewBox="0 0 64 64",
            width="64",
            height="64",
        )
    return svg(
        path(d="M20 18h24v8H20zM18 26h28v24a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4z", fill="none", stroke="currentColor", stroke_width="1.5"),
        path(d="M32 18v-6", fill="none", stroke="currentColor", stroke_width="1.5"),
        viewBox="0 0 64 64",
        width="64",
        height="64",
    )


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

    def render(self):
        rows = self._rows()
        count = sum(q for _, q in rows)
        notice = str(self.notice or "")
        kids: list[Any] = [
            header(h2("Bag"), span(str(count), className="bag-count"), className="bag-head"),
        ]
        if notice:
            kids.append(p(notice, className="bag-notice", role="status"))
        if not rows:
            kids.append(
                div(
                    p("The bag is empty", className="bag-empty-title"),
                    p(
                        "Choose a piece from the table. Nothing is held until you place the order.",
                        className="bag-empty-copy",
                    ),
                    className="bag-empty",
                )
            )
        else:
            items = []
            for sku, qty in rows:
                prod = _product(sku)
                line_total = prod["price"] * qty
                items.append(
                    li(
                        span(prod["name"], className="bag-line-name"),
                        span(f"× {qty} · {_money(prod['price'])}", className="bag-line-meta"),
                        span(_money(line_total), className="bag-line-sum"),
                        form(
                            input_(type="hidden", name="sku", value=sku),
                            button("Remove", type="submit", className="text-btn", **control("cart.remove", sku=sku)),
                            className="inline",
                            method="post",
                            action="/act/cart.remove",
                            data_ux="1",
                            data_target="#cart",
                        ),
                        className="bag-line",
                        id=f"bag-{sku}",
                    )
                )
            kids.append(ul(*items, className="bag-lines"))
            kids.append(
                div(
                    span("Subtotal", className="bag-label"),
                    span(_money(self.subtotal()), className="bag-sum"),
                    className="bag-foot",
                )
            )
            kids.append(
                form(
                    button(
                        "Review order",
                        type="submit",
                        className="btn-primary",
                        **control("cart.open_checkout"),
                    ),
                    method="post",
                    action="/act/cart.open_checkout",
                    data_ux="1",
                    data_target="#stage",
                )
            )
        return aside(*kids, id="cart", className="bag", data_count=str(count))

    @action(caps=())
    def add(self, sku: str = "linen-01"):
        prod = _product(sku)
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
        self.notice = f"Added {prod['name']}"
        self.stamp = "bag"
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("bag-pop").enter("#cart", rise.enter(ms=140))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"Added {prod['name']}")])

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

    def render(self):
        if not self.open:
            return div(id=self.id, className="modal", hidden=True, data_open="0")
        return div(
            div(className="modal-scrim"),
            div(
                p("Order", className="kicker"),
                h2(str(self.title), id="confirm-title"),
                p(str(self.body), className="modal-copy"),
                div(
                    form(
                        button(
                            "Keep looking",
                            type="submit",
                            className="btn-ghost",
                            **control("confirm-modal.close"),
                        ),
                        method="post",
                        action="/act/confirm-modal.close",
                        data_ux="1",
                        data_target="#stage",
                    ),
                    form(
                        button(
                            "Place order",
                            type="submit",
                            className="btn-primary",
                            **control("cart.checkout"),
                        ),
                        method="post",
                        action="/act/cart.checkout",
                        data_ux="1",
                        data_target="#stage",
                    ),
                    className="modal-actions",
                ),
                className="modal-panel",
            ),
            id=self.id,
            className="modal",
            data_open="1",
            role="dialog",
            aria_modal="true",
            aria_labelledby="confirm-title",
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


def catalog_grid():
    cards = []
    for prod in CATALOG:
        cards.append(
            article(
                div(_mark(prod["mark"]), className="card-mark", aria_hidden="true"),
                header(
                    h2(prod["name"]),
                    p(_money(prod["price"]), className="price"),
                    className="card-head",
                ),
                p(prod["line"], className="card-line"),
                form(
                    input_(type="hidden", name="sku", value=prod["sku"]),
                    button(
                        "Add to bag",
                        type="submit",
                        className="btn-secondary",
                        **control("cart.add", sku=prod["sku"]),
                    ),
                    method="post",
                    action="/act/cart.add",
                    data_ux="1",
                    data_target="#cart",
                ),
                className=f"card tone-{prod['tone']}",
                id=f"item-{prod['sku']}",
            )
        )
    return section(*cards, className="grid", aria_label="Pieces")
