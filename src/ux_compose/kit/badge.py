"""Drop-in badge — named status chip.

Host seam: construct kwargs OR subclass.
Accepted: ``items`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. Caps: none. A11y: list of status text; selected
``aria-pressed``.
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
    MorphState,
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


class Badge(Kit):
    """One named status. Not a notification stack (that's Toast)."""

    id = "badge"
    _SEAMS = {'items': 'ITEMS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_row = "flex flex-wrap gap-2"
    class_chip = (
        "inline-flex min-h-8 cursor-pointer items-center rounded-full border "
        "border-stone-200 bg-stone-50 px-3 text-xs font-medium"
    )
    class_chip_on = (
        "inline-flex min-h-8 cursor-pointer items-center rounded-full border-0 "
        "bg-stone-900 px-3 text-xs font-medium text-stone-50"
    )

    ITEMS = (("cut", "Cut"), ("make", "Make"), ("keep", "Keep"))

    value = MorphState("cut")

    def render(self):
        val = str(self.value or "cut")
        chips = [
            button(
                lab,
                type="button",
                className=self.class_chip_on if key == val else self.class_chip,
                aria_pressed="true" if key == val else "false",
                **bind(self.choose, key=key),
            )
            for key, lab in self.ITEMS
        ]
        return self.kit_shell(
            div(*chips, className=self.class_row),
            id=self.id,
            className=self.class_card,
            data_value=val,
            chrome=(
                span("Stage", className=self.class_kicker),
                h2("Status", className=self.class_title),
                p("A named chip. Quantity never lives here.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {k for k, _ in self.ITEMS}
        self.value = key if key in keys else "cut"
        return update_with(self, extra_ops=[notify(str(self.value))])
