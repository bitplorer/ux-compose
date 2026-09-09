"""Drop-in resizable — named split between two panes.

Host seam: construct kwargs OR subclass.
Accepted: ``splits`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value`` (named split, not a percent MorphState). Caps: none.
A11y: split chips ``role=radiogroup`` / ``radio`` ``aria-checked``;
separator ``role=separator`` ``aria-orientation=vertical``; panes labelled.
Not Slider (this is a named band).
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


class Resizable(Kit):
    """Two panes. The split is a name: even / wide / rail."""

    id = "resizable"
    _SEAMS = {'splits': 'SPLITS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_stage = "flex min-h-36 overflow-hidden rounded-2xl border border-stone-200"
    class_pane = "flex flex-col justify-center px-4 py-4 text-sm"
    class_sep = "w-px cursor-col-resize bg-stone-200"

    SPLITS = (("even", "Even", "1fr 1fr"), ("wide", "Wide left", "2fr 1fr"), ("rail", "Rail", "1fr 2fr"))
    value = MorphState("even")

    def render(self):
        val = str(self.value or "even")
        grid = next((g for k, _l, g in self.SPLITS if k == val), "1fr 1fr")
        return self.kit_shell(
            div(
                *[
                    button(
                        lab,
                        type="button",
                        role="radio",
                        aria_checked="true" if key == val else "false",
                        className="rounded-full px-3 py-2 text-xs " + ("bg-stone-900 text-stone-50" if key == val else "bg-stone-100"),
                        **bind(self.split, key=key),
                    )
                    for key, lab, _g in self.SPLITS
                ],
                className="flex gap-2",
                role="radiogroup",
                aria_label="Split",
            ),
            div(
                div("List", className=self.class_pane + " bg-stone-50", aria_label="List pane"),
                span("", className=self.class_sep, role="separator", aria_orientation="vertical", aria_label="Resize"),
                div("Detail", className=self.class_pane + " bg-white", aria_label="Detail pane"),
                className=self.class_stage,
                style=f"display:grid;grid-template-columns:{grid}",
            ),
            id=self.id,
            className=self.class_card,
            data_value=val,
            chrome=(
                span("Split", className=self.class_kicker),
                h2("Two desks", className=self.class_title),
                p("A named split. Quantity never lives here.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def split(self, key: str = ""):
        keys = {row[0] for row in self.SPLITS}
        self.value = key if key in keys else "even"
        return update_with(self, extra_ops=[notify(str(self.value))])
