"""Drop-in empty / error / retry — named phase, never a blank stage.

Host seam: override ``on_ready()``. Retry is public; a billed refetch would take a Cap.
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


def _phase_plan(cid: str = "empty"):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene("empty-phase").enter(f"#{cid}-body", rise.enter(ms=150))
    except Exception:
        return None


class Empty(Component):
    """empty | loading | error | ready. Phase is MorphState.

    Body copy is RefState. Skeleton chrome reuses pulse bars, not a second unit.
    """

    id = "empty"

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
        "m-0 max-w-[32ch] text-[0.9375rem] leading-relaxed text-stone-500 "
        "dark:text-stone-400"
    )
    class_body = "flex flex-col gap-4"
    class_well = (
        "flex min-h-[13.5rem] flex-col items-center justify-center gap-3 "
        "rounded-[1.4rem] bg-white/35 px-6 py-8 text-center dark:bg-white/[0.03]"
    )
    class_well_load = (
        "flex min-h-[13.5rem] flex-col items-center justify-center gap-3 "
        "rounded-[1.4rem] bg-amber-50/50 px-6 py-8 text-center dark:bg-amber-950/20"
    )
    class_well_error = (
        "flex min-h-[13.5rem] flex-col items-center justify-center gap-3 "
        "rounded-[1.4rem] bg-rose-50/80 px-6 py-8 text-center dark:bg-rose-950/25"
    )
    class_well_ready = (
        "flex min-h-[13.5rem] flex-col items-center justify-center gap-3 "
        "rounded-[1.4rem] bg-emerald-50/50 px-6 py-8 text-center dark:bg-emerald-950/15"
    )
    class_mark = (
        "flex h-16 w-16 items-center justify-center rounded-full "
        "border border-dashed border-stone-300 font-serif text-3xl font-light "
        "text-stone-300 dark:border-stone-600 dark:text-stone-600"
    )
    class_mark_error = (
        "flex h-12 w-12 items-center justify-center rounded-full bg-rose-600 "
        "font-serif text-[1.35rem] font-light text-white"
    )
    class_spin = (
        "h-10 w-10 rounded-full border-2 border-stone-200 border-t-stone-800 "
        "animate-spin dark:border-stone-700 dark:border-t-stone-100"
    )
    class_skel = "flex w-full max-w-[16rem] flex-col gap-2"
    class_bar = "h-3 rounded-full bg-stone-200/90 animate-pulse dark:bg-stone-800"
    class_bar_lg = (
        "h-16 rounded-[1.05rem] bg-stone-200/90 animate-pulse dark:bg-stone-800"
    )
    class_swatch_row = "mb-1 grid w-full max-w-[16rem] grid-cols-4 gap-2"
    class_swatch = "h-10 rounded-lg"
    class_actions = "flex min-w-0 flex-wrap items-center justify-center gap-2"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-900 px-5 text-sm font-medium text-stone-50 "
        "transition hover:bg-stone-800 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-white"
    )
    class_btn_danger = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-rose-600 px-5 text-sm font-medium text-white "
        "transition hover:bg-rose-700 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-800/25"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent px-4 text-sm font-medium text-stone-500 "
        "transition hover:text-stone-800 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:text-stone-400 dark:hover:text-stone-50"
    )

    phase = MorphState("empty")
    body = RefState("")
    stamp = MorphState("idle")

    def on_ready(self) -> str:
        return "ready"

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _inner(self, phase: str):
        if phase == "loading":
            return [
                div(
                    span("", className=self.class_spin, aria_hidden="true"),
                    div(
                        div("", className=self.class_bar_lg, id=f"{self.id}-s1"),
                        div("", className=f"{self.class_bar} w-full", id=f"{self.id}-s2"),
                        div("", className=f"{self.class_bar} w-1/2", id=f"{self.id}-s3"),
                        className=self.class_skel,
                    ),
                    p("Fetching the table…", className=self.class_lede),
                    className=self.class_well_load,
                    aria_busy="true",
                    aria_label="Loading the table",
                ),
                div(
                    button(
                        "Simulate fail",
                        type="button",
                        className=self.class_btn_ghost,
                        **bind(self.fail),
                    ),
                    button(
                        "Simulate ready",
                        type="button",
                        className=self.class_btn_primary,
                        **bind(self.ready),
                    ),
                    className=self.class_actions,
                ),
            ]
        if phase == "error":
            return [
                div(
                    span("!", className=self.class_mark_error, aria_hidden="true"),
                    h2("The table could not be reached", className=self.class_title),
                    p(
                        "Retry is public. A billed refetch would take a Cap.",
                        className=self.class_lede,
                    ),
                    className=self.class_well_error,
                    role="alert",
                ),
                button(
                    "Retry",
                    type="button",
                    className=self.class_btn_danger,
                    **bind(self.load),
                ),
            ]
        if phase == "ready":
            washes = (
                "bg-gradient-to-br from-[#e8dcc8] to-[#c9b89a]",
                "bg-gradient-to-br from-[#c4a574] to-[#8b6914]",
                "bg-gradient-to-br from-[#d4c4b0] to-[#9a8470]",
                "bg-gradient-to-br from-[#c9a882] to-[#a67c52]",
            )
            return [
                div(
                    div(
                        *(
                            span("", className=f"{self.class_swatch} {wash}", aria_hidden="true")
                            for wash in washes
                        ),
                        className=self.class_swatch_row,
                    ),
                    span("Ready", className=self.class_kicker),
                    h2("Four objects", className=self.class_title),
                    p(
                        str(
                            self.body
                            or "Linen, oak, wool, clay. Quiet pieces for a working house."
                        ),
                        className=self.class_lede,
                    ),
                    className=self.class_well_ready,
                ),
                button(
                    "Clear",
                    type="button",
                    className=self.class_btn_ghost,
                    **bind(self.reset),
                ),
            ]
        return [
            div(
                span("—", className=self.class_mark, aria_hidden="true"),
                h2("The shelf is quiet", className=self.class_title),
                p(
                    "Empty is a first-class row. Load the table when you like.",
                    className=self.class_lede,
                ),
                className=self.class_well,
            ),
            button(
                "Load the table",
                type="button",
                className=self.class_btn_primary,
                **bind(self.load),
            ),
        ]

    def render(self):
        phase = str(self.phase or "empty")
        if phase not in {"empty", "loading", "error", "ready"}:
            phase = "empty"
        return div(
            span("Shelf", className=self.class_kicker),
            div(*self._inner(phase), id=f"{self.id}-body", className=self.class_body),
            id=self.id,
            className=self.class_card,
            data_phase=phase,
        )

    @action(caps=())
    def load(self):
        self.phase = "loading"
        self.body = ""
        self._tick()
        return update_with(self, _phase_plan(self.id), extra_ops=[notify("loading")])

    @action(caps=())
    def fail(self):
        self.phase = "error"
        self._tick()
        return update_with(self, _phase_plan(self.id), extra_ops=[notify("error")])

    @action(caps=())
    def ready(self):
        self.phase = "ready"
        self.body = "Quiet pieces for a working house."
        self._tick()
        return update_with(
            self,
            _phase_plan(self.id),
            extra_ops=[notify(self.on_ready())],
        )

    @action(caps=())
    def reset(self):
        self.phase = "empty"
        self.body = ""
        self._tick()
        return update_with(self, extra_ops=[notify("empty")])
