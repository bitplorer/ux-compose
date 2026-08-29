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
        className="pointer-events-none block h-4 w-4",
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
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-6 "
        "overflow-x-hidden rounded-[1.85rem] border border-stone-900/[0.07] bg-[#fdfcf8] p-7 text-stone-900 "
        "shadow-[0_0_0_1px_rgba(22,21,19,0.03),0_1px_2px_rgba(22,21,19,0.04),0_28px_56px_-24px_rgba(22,21,19,0.2)] "
        "dark:border-white/10 dark:bg-[#141311] dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-[0.6875rem] font-medium uppercase tracking-[0.22em] text-stone-400 "
        "dark:text-stone-500"
    )
    class_title = (
        "m-0 font-serif text-[1.85rem] font-semibold leading-[1.12] tracking-[-0.03em]"
    )
    class_lede = (
        "m-0 max-w-[36ch] text-[0.9375rem] leading-relaxed text-stone-500 "
        "dark:text-stone-400"
    )
    class_head = "flex items-end justify-between gap-4"
    class_count = (
        "inline-flex min-h-7 shrink-0 items-center rounded-full bg-stone-900 px-3 "
        "text-[0.7rem] font-medium tracking-wide text-stone-50 "
        "dark:bg-stone-100 dark:text-stone-900"
    )
    class_list = "flex flex-col"
    class_row = (
        "flex items-center gap-3.5 rounded-[1.2rem] px-3 py-3 "
        "transition-colors duration-200 hover:bg-stone-900/[0.03] "
        "dark:hover:bg-white/[0.04]"
    )
    class_row_on = (
        "flex items-center gap-3.5 rounded-[1.2rem] px-3 py-3 "
        "bg-rose-50/70 transition-colors duration-200 "
        "dark:bg-rose-950/25"
    )
    class_swatch = "h-12 w-12 shrink-0 rounded-[1rem]"
    class_meta = "flex min-w-0 flex-1 flex-col gap-0.5"
    class_name = (
        "m-0 font-serif text-[1.08rem] font-light tracking-[-0.02em] "
        "text-stone-800 dark:text-stone-100"
    )
    class_price = (
        "w-12 shrink-0 text-right font-mono text-[0.82rem] tabular-nums text-stone-500 "
        "dark:text-stone-400"
    )
    class_heart = (
        "inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-900/10 bg-white/70 p-0 text-stone-400 "
        "transition duration-200 hover:border-rose-300 hover:text-rose-500 "
        "active:scale-95 focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-rose-800/25 "
        "motion-reduce:transition-none dark:border-white/10 dark:bg-white/5 "
        "dark:text-stone-500 dark:hover:text-rose-300"
    )
    class_heart_on = (
        "inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-rose-600 p-0 text-white "
        "shadow-[0_8px_20px_-8px_rgba(225,29,72,0.7)] transition duration-200 "
        "hover:bg-rose-500 active:scale-95 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-800/25 "
        "motion-reduce:transition-none dark:bg-rose-500"
    )
    class_sr = "sr-only"

    ITEMS = (
        ("linen", "Cloth", "Linen work shirt", "48"),
        ("oak", "Wood", "Oak serving board", "72"),
        ("wool", "Cloth", "Wool throw", "96"),
        ("clay", "Earth", "Clay pourer", "38"),
    )
    WASH = {
        "linen": "bg-gradient-to-br from-[#e8dcc8] to-[#c9b89a]",
        "oak": "bg-gradient-to-br from-[#c4a574] to-[#8b6914]",
        "wool": "bg-gradient-to-br from-[#d4c4b0] to-[#9a8470]",
        "clay": "bg-gradient-to-br from-[#c9a882] to-[#a67c52]",
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
                        className=self.class_meta,
                    ),
                    span(f"${price}", className=self.class_price),
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
