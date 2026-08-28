"""Drop-in wishlist — ids silent, heart public.

Host seam: override ``ITEMS`` and ``on_toggle(sku, on)``. Saving is not placing.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    h3,
    p,
    path,
    span,
    svg,
)


def _heart(on: bool):
    return svg(
        path(
            d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.6-7 10-7 10z",
            fill="currentColor" if on else "none",
            stroke="currentColor",
            **{
                "stroke-width": "1.7",
                "stroke-linejoin": "round",
                "stroke-linecap": "round",
            },
        ),
        **{
            "viewBox": "0 0 24 24",
            "aria-hidden": "true",
            "focusable": "false",
        },
        className="pointer-events-none block h-5 w-5",
    )


def _toggle_plan(cid: str, sku: str):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene("wish-toggle").enter(f"#{cid}-row-{sku}", rise.enter(ms=120))
    except Exception:
        return None


class Wishlist(Component):
    """Heart / unheart a catalog. Ids live in RefState. Stamp dirties.

    ``ITEMS`` is ``(sku, kind, title, price)``. Checkout stays on the cart unit.
    """

    id = "wishlist"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-5 "
        "overflow-x-hidden rounded-[1.75rem] border border-stone-200/90 bg-white p-6 text-stone-900 "
        "shadow-[0_1px_0_rgba(22,21,19,0.04),0_24px_48px_-28px_rgba(22,21,19,0.4)] "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-xs font-medium uppercase tracking-[0.2em] text-stone-500 "
        "dark:text-stone-400"
    )
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_head = "flex items-end justify-between gap-4"
    class_count = (
        "inline-flex min-h-11 items-center rounded-full bg-stone-900 px-4 "
        "text-sm font-semibold tabular-nums text-stone-50 "
        "dark:bg-stone-100 dark:text-stone-900"
    )
    class_list = "flex flex-col gap-2"
    class_row = (
        "flex items-center gap-4 rounded-2xl border border-stone-200/80 bg-stone-50 px-4 py-3 "
        "dark:border-stone-800 dark:bg-stone-900"
    )
    class_row_on = (
        "flex items-center gap-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 "
        "dark:border-rose-900 dark:bg-rose-950/40"
    )
    class_swatch = "h-12 w-12 shrink-0 rounded-xl"
    class_meta = "flex min-w-0 flex-1 flex-col gap-0.5"
    class_name = "m-0 font-serif text-lg font-medium tracking-tight"
    class_price = "m-0 text-sm tabular-nums text-stone-500 dark:text-stone-400"
    class_heart = (
        "inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent p-0 text-stone-400 transition "
        "hover:text-rose-700 hover:scale-105 active:scale-95 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-800/25 "
        "dark:text-stone-500 dark:hover:text-rose-300"
    )
    class_heart_on = (
        "inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent p-0 text-rose-800 transition "
        "hover:text-rose-700 hover:scale-105 active:scale-95 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-800/25 "
        "dark:text-rose-300"
    )
    class_sr = "sr-only"

    ITEMS = (
        ("linen", "Cloth", "Linen work shirt", "48"),
        ("oak", "Wood", "Oak serving board", "72"),
        ("wool", "Cloth", "Wool throw", "96"),
        ("clay", "Earth", "Clay pourer", "38"),
    )
    WASH = {
        "linen": "bg-gradient-to-br from-stone-200 to-amber-100",
        "oak": "bg-gradient-to-br from-amber-800 to-stone-900",
        "wool": "bg-gradient-to-br from-stone-400 to-stone-700",
        "clay": "bg-gradient-to-br from-rose-300 to-amber-200",
    }

    ids = RefState(("linen",))
    stamp = MorphState("idle")

    def on_toggle(self, sku: str, on: bool) -> str:
        return sku

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _items(self):
        return tuple(self.ITEMS)

    def render(self):
        have = tuple(self.ids or ())
        have_set = set(have)
        rows = []
        for sku, kind, title, price in self._items():
            on = sku in have_set
            wash = self.WASH.get(sku, "bg-stone-200")
            rows.append(
                div(
                    span("", className=f"{self.class_swatch} {wash}", aria_hidden="true"),
                    div(
                        span(kind, className=self.class_kicker),
                        h3(title, className=self.class_name),
                        p(f"${price}", className=self.class_price),
                        className=self.class_meta,
                    ),
                    button(
                        span("Saved" if on else "Save", className=self.class_sr),
                        _heart(on),
                        type="button",
                        id=f"{self.id}-heart-{sku}",
                        className=self.class_heart_on if on else self.class_heart,
                        aria_pressed="true" if on else "false",
                        aria_label=f"{'Unsave' if on else 'Save'} {title}",
                        **bind(self.toggle, sku=sku),
                    ),
                    id=f"{self.id}-row-{sku}",
                    className=self.class_row_on if on else self.class_row,
                )
            )
        n = len(have)
        return div(
            div(
                div(
                    span("Keep", className=self.class_kicker),
                    h2("Saved to the house", className=self.class_title),
                ),
                span(f"{n} saved", className=self.class_count),
                className=self.class_head,
            ),
            p("Saving is not placing. The bag still spends a Cap.", className=self.class_lede),
            div(*rows, className=self.class_list),
            id=self.id,
            className=self.class_card,
            data_count=str(n),
        )

    @action(caps=())
    def toggle(self, sku: str = ""):
        catalog = {row[0] for row in self._items()}
        cur = set(self.ids or ())
        if sku in cur:
            cur.remove(sku)
            on = False
        elif sku in catalog:
            cur.add(sku)
            on = True
        else:
            return update_with(self)
        self.ids = tuple(s for s, *_ in self._items() if s in cur)
        self._tick()
        return update_with(
            self,
            _toggle_plan(self.id, sku),
            extra_ops=[notify(self.on_toggle(sku, on))],
        )
