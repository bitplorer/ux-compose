"""Drop-in separator — composite rule with an optional accessible name.

Host seam: render slots OR subclass.
Accepted: ``label`` (same type as ``LABEL``); ``shell`` (bool; ``False``
renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.

Not a bare ``<hr>`` atom (ux-dom). This unit is a labeled break in a card.
MorphState: none. Caps: none. A11y: ``role=separator`` ``aria-orientation``
plus a visible label when provided.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    div,
    h2,
    hr,
    p,
    span,
)


class Separator(Component):
    """Section break with a name. Composite, not a primitive atom."""

    id = "separator"
    _SEAMS = {'label': 'LABEL'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_row = "flex items-center gap-3"
    class_line = "m-0 min-w-0 flex-1 border-0 border-t border-stone-200"
    class_label = "text-xs font-medium uppercase tracking-widest text-stone-400"

    LABEL = "Or continue"

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        return kit_shell(self,
            div(
                hr(className=self.class_line, role="separator", aria_orientation="horizontal"),
                span(self.LABEL, className=self.class_label),
                hr(className=self.class_line, role="separator", aria_orientation="horizontal", aria_hidden="true"),
                className=self.class_row,
                role="group",
                aria_label=self.LABEL,
            ),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Break", className=self.class_kicker),
                h2("A pause", className=self.class_title),
                p("Above the fold.", className=self.class_lede),
                p("Below the fold.", className=self.class_lede),
            ),
        )
