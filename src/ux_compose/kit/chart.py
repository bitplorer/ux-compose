"""Drop-in chart — named series as an SVG image.

Host seam: override ``SERIES``. Choosing a bar is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``which``. RefState: ``values``. Caps: none.
A11y: ``svg`` ``role=img`` labelled. Magnitudes live on RefState.
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
    rect,
    span,
    svg,
)


class Chart(Component):
    """Winter counts. Bars are names; heights are RefState."""

    id = "chart"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"

    SERIES = (("linen", "Linen"), ("oak", "Oak"), ("wool", "Wool"))
    values = RefState((40, 72, 28))
    which = MorphState("linen")
    dirty = MorphState("idle")

    def _series(self):
        return tuple(self.SERIES)

    def _vals(self):
        raw = tuple(self.values or ())
        out = []
        for i, _row in enumerate(self._series()):
            try:
                out.append(max(0, min(100, int(raw[i]))))
            except (IndexError, TypeError, ValueError):
                out.append(0)
        return tuple(out)

    def render(self):
        which = str(self.which or self._series()[0][0])
        vals = self._vals()
        n = max(len(self._series()), 1)
        gap = 8
        bw = 36
        bars = []
        for i, ((key, lab), v) in enumerate(zip(self._series(), vals)):
            x = 12 + i * (bw + gap)
            h = max(2, int(v * 0.8))
            y = 90 - h
            bars.append(
                rect(
                    x=str(x),
                    y=str(y),
                    width=str(bw),
                    height=str(h),
                    rx="6",
                    fill="#1c1917" if key == which else "#d6d3d1",
                )
            )
        width = 12 + n * (bw + gap)
        return div(
            span("Count", className=self.class_kicker),
            h2("Winter cuts", className=self.class_title),
            p("Named bars. Heights are RefState.", className=self.class_lede),
            svg(
                *bars,
                width=str(width),
                height="96",
                viewBox=f"0 0 {width} 96",
                role="img",
                aria_label="Cuts by material",
                className="max-w-full",
            ),
            div(
                *[
                    button(
                        lab,
                        type="button",
                        className="rounded-full px-3 py-2 text-xs " + ("bg-stone-900 text-stone-50" if key == which else "bg-stone-100"),
                        **bind(self.choose, key=key),
                    )
                    for key, lab in self._series()
                ],
                className="flex flex-wrap gap-2",
            ),
            id=self.id,
            className=self.class_card,
            data_which=which,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._series()}
        self.which = key if key in keys else self._series()[0][0]
        return update_with(self, extra_ops=[notify(str(self.which))])
