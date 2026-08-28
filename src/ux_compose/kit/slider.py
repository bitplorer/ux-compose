"""Drop-in slider — magnitude silent, named band MorphState.

Host seam: override ``STEPS`` and ``on_set(n)``. Stepping is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

Native range still posts a quantity — the action writes RefState, not
MorphState. Studio uses stepped buttons so Channel session stays legal.
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
    0: "w-0",
    25: "w-1/4",
    50: "w-1/2",
    75: "w-3/4",
    100: "w-full",
}


def _band_of(n: int) -> str:
    if n <= 0:
        return "empty"
    if n < 50:
        return "low"
    if n < 100:
        return "mid"
    return "full"


class Slider(Component):
    """Percent is RefState. Band is a name (empty / low / mid / full).

    ``STEPS`` is a tuple of percents posted as action args, never MorphState(int).
    """

    id = "slider"

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
        "flex items-end justify-between gap-4 rounded-2xl bg-stone-900 px-5 py-5 "
        "text-stone-50 dark:bg-stone-100 dark:text-stone-900"
    )
    class_num = "m-0 font-serif text-5xl font-semibold leading-none tracking-tight tabular-nums"
    class_band = (
        "inline-flex min-h-7 items-center rounded-full bg-white/10 px-3 text-xs "
        "font-semibold uppercase tracking-widest text-stone-200 "
        "dark:bg-stone-900/10 dark:text-stone-700"
    )
    class_track = "h-2 overflow-hidden rounded-full bg-stone-200 dark:bg-stone-800"
    class_fill = "h-full rounded-full bg-stone-900 transition-[width] duration-300 ease-out dark:bg-stone-100"
    class_seg = "flex min-w-0 flex-wrap gap-1"
    class_step = (
        "min-h-11 min-w-11 flex-1 cursor-pointer rounded-full border border-stone-200 "
        "bg-white px-3 text-sm font-medium tabular-nums text-stone-600 "
        "hover:bg-stone-100 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-300 dark:hover:bg-stone-900"
    )
    class_step_on = (
        "min-h-11 min-w-11 flex-1 cursor-pointer rounded-full border-0 "
        "bg-stone-800 px-3 text-sm font-semibold tabular-nums text-stone-50 "
        "active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-200 dark:text-stone-900"
    )

    STEPS = (0, 25, 50, 75, 100)

    value = RefState(50)
    band = MorphState("mid")
    stamp = MorphState("idle")

    def on_set(self, n: int) -> str:
        return f"{n}"

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _steps(self):
        return tuple(self.STEPS)

    def _n(self) -> int:
        try:
            return int(self.value or 0)
        except (TypeError, ValueError):
            return 0

    def render(self):
        n = self._n()
        band = str(self.band or _band_of(n))
        width = _WIDTH.get(n, "w-1/2")
        segs = [
            button(
                str(step),
                type="button",
                id=f"{self.id}-step-{step}",
                className=self.class_step_on if step == n else self.class_step,
                aria_pressed="true" if step == n else "false",
                **bind(self.set, n=str(step)),
            )
            for step in self._steps()
        ]
        return div(
            span("Fill", className=self.class_kicker),
            h2("Hold the pour", className=self.class_title),
            p("The percent is silent. The band is a name.", className=self.class_lede),
            div(
                p(f"{n}%", className=self.class_num),
                span(band, className=self.class_band),
                id=f"{self.id}-face",
                className=self.class_face,
            ),
            div(
                div("", className=f"{self.class_fill} {width}", id=f"{self.id}-fill"),
                className=self.class_track,
                role="meter",
                aria_valuemin="0",
                aria_valuemax="100",
                aria_valuenow=str(n),
                aria_label="Fill",
            ),
            div(*segs, className=self.class_seg, role="group", aria_label="Fill steps"),
            id=self.id,
            className=self.class_card,
            data_band=band,
        )

    @action(caps=())
    def set(self, n: str = "50"):
        try:
            raw = int(n)
        except (TypeError, ValueError):
            raw = 40
        steps = self._steps()
        if raw not in steps:
            raw = min(steps, key=lambda s: abs(s - raw))
        self.value = raw
        self.band = _band_of(raw)
        self._tick()
        return update_with(self, extra_ops=[notify(self.on_set(raw))])
