"""Drop-in countdown — remaining magnitude on RefState.

Host seam: construct kwargs OR subclass.
Accepted: ``remain`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``remain``. Caps: none.
A11y: ``role=timer`` ``aria-live=polite`` labelledby. Quantity never
lives on MorphState. Not Stepper (named wizard) and not SpinButton.
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
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


class Countdown(Kit):
    """Seconds until the cut. The number is RefState."""

    id = "countdown"
    _SEAMS = {'remain': 'remain'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_num = "m-0 font-serif text-5xl font-semibold tracking-tight"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border "
        "border-stone-200 bg-white px-4 text-sm"
    )

    remain = RefState(12)
    dirty = MorphState("idle")

    def _n(self) -> int:
        try:
            return max(0, int(self.remain or 0))
        except (TypeError, ValueError):
            return 0

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        n = self._n()
        title_id = f"{self.id}-label"
        return self.kit_shell(
            span("Until", className=self.class_kicker),
            h2("The cut", id=title_id, className=self.class_title),
            p(f"{n}s left. Magnitude is RefState.", className=self.class_lede),
            p(
                str(n),
                className=self.class_num,
                role="timer",
                aria_live="polite",
                aria_labelledby=title_id,
            ),
            button("Tick", type="button", className=self.class_btn, **bind(self.tick)),
            id=self.id,
            className=self.class_card,
            data_remain=str(n),
        )

    @action(caps=())
    def tick(self):
        self.remain = max(0, self._n() - 1)
        self._mark()
        return update_with(self, extra_ops=[notify(str(self.remain))])
