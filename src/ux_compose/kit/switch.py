"""Drop-in switch — boolean MorphState, public flip.

Host seam: render slots OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``on``. Caps: none. A11y (APG Switch): ``role=switch``
``aria-checked`` ``aria-labelledby``.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
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


class Switch(Component):
    """Quiet hours. Boolean MorphState is qualitative — legal on the session plane."""

    id = "switch"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_row = "flex items-center justify-between gap-4"
    class_track = (
        "relative inline-flex h-7 w-12 cursor-pointer items-center rounded-full border-0 p-0.5"
    )
    class_knob = "block h-6 w-6 rounded-full bg-white shadow"

    on = MorphState(False)

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        on = bool(self.on)
        label_id = f"{self.id}-label"
        return kit_shell(self,
            h2("Quiet hours", id=label_id, className=self.class_title),
            p(
                "Notifications hush after dusk." if on else "Notifications reach the table.",
                className=self.class_lede,
            ),
            div(
                span("On" if on else "Off", className="text-sm font-medium"),
                button(
                    span("", className=self.class_knob + (" ml-auto" if on else "")),
                    type="button",
                    role="switch",
                    aria_checked="true" if on else "false",
                    aria_labelledby=label_id,
                    className=self.class_track + (" bg-stone-800" if on else " bg-stone-300"),
                    **bind(self.flip),
                ),
                className=self.class_row,
            ),
            id=self.id,
            className=self.class_card,
            data_on="1" if on else "0",
            chrome=(
                span("Quiet", className=self.class_kicker),
            ),
        )

    @action(caps=())
    def flip(self):
        self.on = not bool(self.on)
        return update_with(self, extra_ops=[notify("on" if self.on else "off")])
