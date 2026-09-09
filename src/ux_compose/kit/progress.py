"""Drop-in progress — magnitude on RefState, dirty MorphState.

Host seam: construct kwargs OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``value`` (0–100 string/int). Caps: none.
A11y (APG Meter/Progress): ``role=progressbar`` ``aria-valuemin/max/now``
``aria-labelledby``. Quantity never lives on MorphState.
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
    MorphState,
    RefState,
    action,
    bind,
    update_with,
    button,
    div,
    h2,
    p,
    progress,
    span,
)


class Progress(Kit):
    """Named completion. The bar is a progress element, not a quantity Morph."""

    id = "progress"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_bar = "h-3 w-full overflow-hidden rounded-full bg-stone-100"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )

    value = RefState(40)
    dirty = MorphState("idle")

    def _pct(self) -> int:
        try:
            n = int(self.value or 0)
        except (TypeError, ValueError):
            n = 0
        return max(0, min(100, n))

    def render(self):
        n = self._pct()
        title_id = f"{self.id}-title"
        return self.kit_shell(
            span("Work", className=self.class_kicker),
            h2("On the board", id=title_id, className=self.class_title),
            p(f"{n} of 100", className=self.class_lede),
            progress(
                value=str(n),
                max="100",
                className=self.class_bar,
                role="progressbar",
                aria_valuemin="0",
                aria_valuemax="100",
                aria_valuenow=str(n),
                aria_labelledby=title_id,
            ),
            button("Advance", type="button", className=self.class_btn, **bind(self.advance)),
            id=self.id,
            className=self.class_card,
            data_value=str(n),
        )

    @action(caps=())
    def advance(self):
        self.value = min(100, self._pct() + 20)
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self)
