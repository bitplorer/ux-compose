"""Drop-in slider — magnitude on RefState, dirty MorphState.

Host seam: override min/max labels. Sliding is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``value``. Caps: none.
A11y (APG Slider): ``role=slider`` ``aria-valuemin/max/now`` labelledby.
Label ``for`` ↔ range id. Quantity never lives on MorphState.
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
    div,
    h2,
    input_,
    label,
    p,
    span,
)


class Slider(Component):
    """Named range. The number is RefState; dirty morphs the card."""

    id = "slider"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_input = "w-full accent-stone-800"

    value = RefState(40)
    dirty = MorphState("idle")

    def _n(self) -> int:
        try:
            return max(0, min(100, int(self.value or 0)))
        except (TypeError, ValueError):
            return 0

    def render(self):
        n = self._n()
        fid = f"{self.id}-range"
        lab_id = f"{self.id}-label"
        return div(
            span("Amount", className=self.class_kicker),
            h2("How much", id=lab_id, className=self.class_title),
            p(f"{n} of 100", className=self.class_lede),
            label("Amount", className=self.class_label, html_for=fid),
            input_(
                type="range",
                name="value",
                id=fid,
                min="0",
                max="100",
                value=str(n),
                className=self.class_input,
                role="slider",
                aria_valuemin="0",
                aria_valuemax="100",
                aria_valuenow=str(n),
                aria_labelledby=lab_id,
                **bind(self.set_value),
            ),
            id=self.id,
            className=self.class_card,
            data_value=str(n),
        )

    @action(caps=())
    def set_value(self, value: str = "40", **kwargs):
        raw = value if value != "" else kwargs.get("value", "40")
        try:
            self.value = max(0, min(100, int(raw)))
        except (TypeError, ValueError):
            self.value = 40
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self, extra_ops=[notify(str(self.value))])
