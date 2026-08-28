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
    class_body = "flex flex-col gap-4"
    class_well = (
        "flex flex-col items-center gap-2 rounded-2xl bg-stone-50 px-6 py-10 text-center "
        "dark:bg-stone-900"
    )
    class_well_error = (
        "flex flex-col items-center gap-2 rounded-2xl bg-rose-50 px-6 py-10 text-center "
        "dark:bg-rose-950/40"
    )
    class_mark = (
        "font-serif text-5xl font-medium leading-none tracking-tight text-stone-300 "
        "dark:text-stone-700"
    )
    class_mark_error = (
        "font-serif text-5xl font-medium leading-none tracking-tight text-rose-300 "
        "dark:text-rose-800"
    )
    class_skel = "flex flex-col gap-2"
    class_bar = (
        "h-3 rounded-full bg-stone-200 animate-pulse dark:bg-stone-800"
    )
    class_ready = (
        "flex flex-col gap-2 rounded-2xl bg-emerald-50 px-5 py-5 "
        "dark:bg-emerald-950/40"
    )
    class_actions = "flex min-w-0 flex-wrap items-center justify-center gap-2"
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
                    div("", className=f"{self.class_bar} w-3/4", id=f"{self.id}-s1"),
                    div("", className=f"{self.class_bar} w-full", id=f"{self.id}-s2"),
                    div("", className=f"{self.class_bar} w-1/2", id=f"{self.id}-s3"),
                    className=self.class_skel,
                    aria_busy="true",
                    aria_label="Loading the table",
                ),
                p("Fetching the table…", className=self.class_lede),
                div(
                    button("Simulate fail", type="button", className=self.class_btn_ghost, **bind(self.fail)),
                    button("Simulate ready", type="button", className=self.class_btn_primary, **bind(self.ready)),
                    className=self.class_actions,
                ),
            ]
        if phase == "error":
            return [
                div(
                    span("!", className=self.class_mark_error, aria_hidden="true"),
                    h2("The table could not be reached", className=self.class_title),
                    p("Retry is public. A billed refetch would take a Cap.", className=self.class_lede),
                    className=self.class_well_error,
                    role="alert",
                ),
                button("Retry", type="button", className=self.class_btn_primary, **bind(self.load)),
            ]
        if phase == "ready":
            return [
                div(
                    span("Ready", className=self.class_kicker),
                    h2("Four objects", className=self.class_title),
                    p(
                        str(self.body or "Linen, oak, wool, clay. Quiet pieces for a working house."),
                        className=self.class_lede,
                    ),
                    className=self.class_ready,
                ),
                button("Clear", type="button", className=self.class_btn_ghost, **bind(self.reset)),
            ]
        return [
            div(
                span("—", className=self.class_mark, aria_hidden="true"),
                h2("The shelf is quiet", className=self.class_title),
                p("Empty is a first-class row. Load the table when you like.", className=self.class_lede),
                className=self.class_well,
            ),
            button("Load the table", type="button", className=self.class_btn_primary, **bind(self.load)),
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
