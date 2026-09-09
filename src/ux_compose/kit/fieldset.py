"""Drop-in fieldset — grouped named choices under a legend.

Host seam: construct kwargs OR subclass.
Accepted: ``options`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. Caps: none. A11y: native ``fieldset`` + ``legend``,
radiogroup ``role`` with ``aria-labelledby``. Each radio labelled.
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
    fieldset,
    h2,
    legend,
    p,
    span,
)


class Fieldset(Kit):
    """One named choice in a group. The legend is the accessible name."""

    id = "fieldset"
    _SEAMS = {'options': 'OPTIONS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_set = "m-0 flex flex-col gap-2 rounded-2xl border border-stone-200 p-4"
    class_legend = "px-1 text-sm font-medium"
    class_opt = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-transparent "
        "px-3 text-left text-sm hover:bg-stone-50"
    )
    class_opt_on = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-stone-100 "
        "px-3 text-left text-sm font-medium"
    )

    OPTIONS = (
        ("linen", "Linen"),
        ("oak", "Oak"),
        ("wool", "Wool"),
    )

    value = MorphState("linen")

    def _options(self):
        return tuple(self.OPTIONS)

    def render(self):
        val = str(self.value or self._options()[0][0])
        legend_id = f"{self.id}-legend"
        opts = [
            button(
                lab,
                type="button",
                role="radio",
                aria_checked="true" if key == val else "false",
                className=self.class_opt_on if key == val else self.class_opt,
                **bind(self.choose, key=key),
            )
            for key, lab in self._options()
        ]
        return self.kit_shell(
            fieldset(
                legend("Material", id=legend_id, className=self.class_legend),
                *opts,
                className=self.class_set,
                role="radiogroup",
                aria_labelledby=legend_id,
            ),
            id=self.id,
            className=self.class_card,
            data_value=val,
            chrome=(
                span("Group", className=self.class_kicker),
                h2("Finish", className=self.class_title),
                p("A fieldset names the group. The value is a name.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {k for k, _ in self._options()}
        self.value = key if key in keys else self._options()[0][0]
        return update_with(self, extra_ops=[notify(str(self.value))])
