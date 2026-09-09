"""Drop-in banner — page-level status strip, public dismiss.

Host seam: render slots OR subclass.
Accepted: ``title``, ``body`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. Caps: none. A11y: ``role=region`` labelledby; not
``role=alert`` (that is Alert).
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    MorphState,
    action,
    bind,
    update_with,
    button,
    div,
    h2,
    p,
    span,
)


class Banner(Component):
    """Site-wide notice. Closing is Morph, not a Cap."""

    id = "banner"
    _SEAMS = {'title': 'TITLE', 'body': 'BODY'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] items-start "
        "justify-between gap-4 rounded-3xl border border-sky-200 bg-sky-50 px-6 py-5 text-sky-950 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-sky-700"
    class_title = "m-0 font-serif text-xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-sky-900/80"
    class_x = (
        "min-h-11 min-w-11 cursor-pointer rounded-full border-0 bg-transparent "
        "text-sm font-medium text-sky-900 hover:bg-sky-100"
    )
    class_rest = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] flex-col gap-3 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )

    TITLE = "Winter hours"
    BODY = "The studio closes at dusk. The banner is chrome, not authority."

    open = MorphState(True)

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        if not bool(self.open):
            return kit_shell(self,
                button("Show banner", type="button", className=self.class_x + " border border-stone-200 px-4", **bind(self.show)),
                chrome=(
                    span("Quiet", className="text-xs font-medium uppercase tracking-widest text-stone-400"),
                    h2("Banner hidden", className="m-0 font-serif text-2xl font-semibold"),
                ),
                id=self.id,
                className=self.class_rest,
                data_open="0",
            )
        title_id = f"{self.id}-title"
        return kit_shell(self,
            div(
                h2(self.TITLE, id=title_id, className=self.class_title),
                p(self.BODY, className=self.class_lede),
            ),
            button("Dismiss", type="button", className=self.class_x, aria_label="Dismiss banner", **bind(self.dismiss)),
            chrome=(span("Notice", className=self.class_kicker),),
            id=self.id,
            className=self.class_card,
            role="region",
            aria_labelledby=title_id,
            data_open="1",
        )

    @action(caps=())
    def dismiss(self):
        self.open = False
        return update_with(self)

    @action(caps=())
    def show(self):
        self.open = True
        return update_with(self)
