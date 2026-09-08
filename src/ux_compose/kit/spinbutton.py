"""Drop-in spinbutton — quantity on RefState, APG spinbutton.

Host seam: override min/max. Stepping is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``value``. Caps: none.
A11y (APG Spinbutton): labelled field ``role=spinbutton``
``aria-valuemin/max/now`` ``aria-labelledby``. Label ``for`` ↔ input id.
Plus/minus are supporting buttons, not the spinbutton. Quantity never
lives on MorphState. Not Slider (range) and not Stepper (named wizard).
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
    input_,
    label,
    p,
    span,
)


class SpinButton(Component):
    """How many on the board. The number is RefState; dirty morphs the card."""

    id = "spinbutton"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_row = "flex items-center gap-2"
    class_btn = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-200 bg-white text-lg font-medium"
    )
    class_input = (
        "min-h-11 w-20 rounded-2xl border border-stone-200 bg-stone-50 text-center "
        "text-sm outline-none focus:border-stone-400"
    )

    MIN = 1
    MAX = 9

    value = RefState(2)
    dirty = MorphState("idle")

    def _n(self) -> int:
        lo, hi = int(self.MIN), int(self.MAX)
        try:
            return max(lo, min(hi, int(self.value or lo)))
        except (TypeError, ValueError):
            return lo

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        n = self._n()
        fid = f"{self.id}-value"
        lab_id = f"{self.id}-label"
        lo, hi = int(self.MIN), int(self.MAX)
        return div(
            span("Count", className=self.class_kicker),
            h2("On the board", id=lab_id, className=self.class_title),
            p(f"{n} of {hi}. Magnitude is RefState.", className=self.class_lede),
            label("Quantity", className=self.class_label, html_for=fid),
            div(
                button(
                    "−",
                    type="button",
                    className=self.class_btn,
                    aria_label="Decrease",
                    **bind(self.dec),
                ),
                input_(
                    type="text",
                    name="value",
                    id=fid,
                    value=str(n),
                    inputmode="numeric",
                    autocomplete="off",
                    className=self.class_input,
                    role="spinbutton",
                    aria_valuemin=str(lo),
                    aria_valuemax=str(hi),
                    aria_valuenow=str(n),
                    aria_labelledby=lab_id,
                    **bind(self.set_value),
                ),
                button(
                    "+",
                    type="button",
                    className=self.class_btn,
                    aria_label="Increase",
                    **bind(self.inc),
                ),
                className=self.class_row,
            ),
            id=self.id,
            className=self.class_card,
            data_value=str(n),
        )

    @action(caps=())
    def set_value(self, value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get("value", "")
        lo, hi = int(self.MIN), int(self.MAX)
        try:
            self.value = max(lo, min(hi, int(raw)))
        except (TypeError, ValueError):
            self.value = lo
        self._mark()
        return update_with(self, extra_ops=[notify(str(self.value))])

    @action(caps=())
    def inc(self):
        self.value = min(int(self.MAX), self._n() + 1)
        self._mark()
        return update_with(self, extra_ops=[notify(str(self.value))])

    @action(caps=())
    def dec(self):
        self.value = max(int(self.MIN), self._n() - 1)
        self._mark()
        return update_with(self, extra_ops=[notify(str(self.value))])
