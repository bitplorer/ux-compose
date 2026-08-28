"""Drop-in progress — pct silent, phase named.

Host seam: override ``on_finish()``. Starting and advancing are public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

Bar width is a named band class (empty/low/mid/full), never a quantity
on MorphState.
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


_WIDTH = {
    "empty": "w-0",
    "low": "w-1/4",
    "mid": "w-3/4",
    "full": "w-full",
}


def _band_of(n: int) -> str:
    if n <= 0:
        return "empty"
    if n < 50:
        return "low"
    if n < 100:
        return "mid"
    return "full"


def _finish_plan(cid: str = "progress"):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene("progress-done").enter(f"#{cid}-face", rise.enter(ms=160))
    except Exception:
        return None


class Progress(Component):
    """A run. Percent is RefState. Phase is idle / run / done.

    ``bump`` advances by ``STEP``. Finish snaps to full.
    """

    id = "progress"

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
    class_face = (
        "flex items-end justify-between gap-4 rounded-2xl bg-stone-900 px-5 py-6 "
        "text-stone-50 dark:bg-stone-100 dark:text-stone-900"
    )
    class_num = "m-0 font-serif text-5xl font-semibold leading-none tracking-tight tabular-nums"
    class_phase = (
        "inline-flex min-h-7 items-center rounded-full bg-white/10 px-3 text-xs "
        "font-semibold uppercase tracking-widest text-stone-200 "
        "dark:bg-stone-900/10 dark:text-stone-700"
    )
    class_track = "h-2.5 overflow-hidden rounded-full bg-stone-200 dark:bg-stone-800"
    class_fill = (
        "h-full rounded-full bg-emerald-700 transition-[width] duration-300 ease-out "
        "dark:bg-emerald-500"
    )
    class_fill_done = (
        "h-full rounded-full bg-emerald-500 transition-[width] duration-300 ease-out "
        "dark:bg-emerald-400"
    )
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

    STEP = 25

    pct = RefState(0)
    phase = MorphState("idle")
    band = MorphState("empty")
    stamp = MorphState("idle")

    def on_finish(self) -> str:
        return "done"

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _n(self) -> int:
        try:
            return max(0, min(100, int(self.pct or 0)))
        except (TypeError, ValueError):
            return 0

    def render(self):
        n = self._n()
        phase = str(self.phase or "idle")
        band = str(self.band or _band_of(n))
        width = _WIDTH.get(band, "w-0")
        fill = self.class_fill_done if phase == "done" else self.class_fill
        copy = {
            "idle": "The bench is quiet. Start when you like.",
            "run": "The pour is moving. Advance keeps it honest.",
            "done": "Held. The run is through.",
        }.get(phase, "")
        return div(
            span("Run", className=self.class_kicker),
            h2("On the bench", className=self.class_title),
            p(copy, className=self.class_lede),
            div(
                p(f"{n}%", className=self.class_num),
                span(phase, className=self.class_phase),
                id=f"{self.id}-face",
                className=self.class_face,
            ),
            div(
                div("", className=f"{fill} {width}", id=f"{self.id}-fill"),
                className=self.class_track,
                role="progressbar",
                aria_valuemin="0",
                aria_valuemax="100",
                aria_valuenow=str(n),
                aria_label="Run",
            ),
            div(
                button(
                    "Start",
                    type="button",
                    className=self.class_btn_ghost,
                    **bind(self.start),
                ),
                button(
                    "Advance",
                    type="button",
                    className=self.class_btn_primary,
                    **bind(self.bump),
                ),
                button(
                    "Finish",
                    type="button",
                    className=self.class_btn_ghost,
                    **bind(self.finish),
                ),
                className=self.class_actions,
            ),
            id=self.id,
            className=self.class_card,
            data_phase=phase,
            data_band=band,
        )

    def _write(self, n: int, phase: str):
        n = max(0, min(100, n))
        self.pct = n
        self.phase = phase
        self.band = _band_of(n)
        self._tick()

    @action(caps=())
    def start(self):
        self._write(10, "run")
        return update_with(self, extra_ops=[notify("run")])

    @action(caps=())
    def bump(self):
        n = min(100, self._n() + int(self.STEP))
        phase = "done" if n >= 100 else "run"
        self._write(n, phase)
        plan = _finish_plan(self.id) if phase == "done" else None
        return update_with(self, plan, extra_ops=[notify(phase)])

    @action(caps=())
    def finish(self):
        self._write(100, "done")
        return update_with(
            self,
            _finish_plan(self.id),
            extra_ops=[notify(self.on_finish())],
        )
