"""Drop-in KPI strip — magnitudes silent, stamp dirties.

Host seam: override ``on_tick`` / ``on_reset``. A sale is public.
Zeroing the board spends ``admin.reset``.
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
    p,
    span,
)


def _tick_plan(cid: str = "kpi"):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene("kpi-tick").enter(f"#{cid}-tiles", rise.enter(ms=140))
    except Exception:
        return None


class Kpi(Component):
    """Dashboard numbers from Host DB, never from the session plane.

    ``bag`` / ``held`` / ``placed`` are RefState. ``stamp`` is the dirty tick.
    """

    id = "kpi"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-[44rem] flex-col gap-5 "
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
    class_tiles = "grid grid-cols-3 gap-2"
    class_tile = (
        "flex min-w-0 flex-col gap-2 rounded-2xl bg-stone-900 px-4 py-5 text-stone-50 "
        "dark:bg-stone-100 dark:text-stone-900"
    )
    class_tile_label = (
        "text-xs font-medium uppercase tracking-widest text-stone-400 "
        "dark:text-stone-500"
    )
    class_tile_num = (
        "m-0 font-serif text-4xl font-semibold leading-none tracking-tight tabular-nums"
    )
    class_tile_hint = "m-0 text-xs text-stone-400 dark:text-stone-500"
    class_actions = "flex min-w-0 flex-wrap items-center gap-2"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 "
        "hover:bg-stone-700 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-200 dark:text-stone-900 dark:hover:bg-white"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:hover:bg-stone-900"
    )

    bag = RefState(3)
    held = RefState(48)
    placed = RefState(2)
    stamp = MorphState("idle")

    def on_tick(self) -> str:
        return "sale"

    def on_reset(self) -> str:
        return "zeroed"

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def render(self):
        cells = (
            ("In bag", int(self.bag or 0), "Waiting"),
            ("Held", int(self.held or 0), "On the books"),
            ("Placed", int(self.placed or 0), "Through"),
        )
        tiles = [
            div(
                span(label, className=self.class_tile_label),
                p(str(n), className=self.class_tile_num, id=f"{self.id}-{label.lower().replace(' ', '-')}"),
                p(hint, className=self.class_tile_hint),
                className=self.class_tile,
            )
            for label, n, hint in cells
        ]
        return div(
            span("Floor", className=self.class_kicker),
            h2("The house today", className=self.class_title),
            p("Numbers stay silent. The stamp is what morphs.", className=self.class_lede),
            div(*tiles, id=f"{self.id}-tiles", className=self.class_tiles),
            div(
                button(
                    "A sale lands",
                    type="button",
                    className=self.class_btn_primary,
                    **bind(self.tick_up),
                ),
                button(
                    "Zero the board",
                    type="button",
                    className=self.class_btn_ghost,
                    **bind(self.reset),
                ),
                className=self.class_actions,
            ),
            id=self.id,
            className=self.class_card,
            data_stamp=str(self.stamp or "idle"),
        )

    @action(caps=())
    def tick_up(self):
        self.bag = max(0, int(self.bag or 0) - 1)
        self.placed = int(self.placed or 0) + 1
        self.held = int(self.held or 0) + 12
        self._tick()
        return update_with(
            self,
            _tick_plan(self.id),
            extra_ops=[notify(self.on_tick())],
        )

    @action(caps=("admin.reset",))
    def reset(self):
        self.bag = 0
        self.held = 0
        self.placed = 0
        self._tick()
        return update_with(self, extra_ops=[notify(self.on_reset())])
