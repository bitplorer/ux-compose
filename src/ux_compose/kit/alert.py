"""Drop-in alert — inline status with optional public dismiss.

Host seam: render slots OR subclass.
Accepted: ``title``, ``body``, ``kind`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. Caps: none. A11y: ``role=alert`` for assertive copy.
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


class Alert(Component):
    """Inline warning. Closing morphs the region away."""

    id = "alert"
    _SEAMS = {'title': 'TITLE', 'body': 'BODY', 'kind': 'KIND'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-3 "
        "rounded-3xl border border-amber-200 bg-amber-50 p-6 text-amber-950 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-amber-700"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-amber-900/80"
    class_x = (
        "self-start min-h-11 cursor-pointer rounded-full border-0 bg-transparent "
        "px-3 text-sm font-medium text-amber-900 hover:bg-amber-100"
    )
    class_rest = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-3 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )

    TITLE = "The kiln is warm"
    BODY = "Finish the last board before noon. Closing this note is public."
    KIND = "warning"

    open = MorphState(True)

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        if not bool(self.open):
            return kit_shell(self,
                button("Show alert", type="button", className=self.class_x + " border border-stone-200", **bind(self.show)),
                chrome=(
                    span("Quiet", className="text-xs font-medium uppercase tracking-widest text-stone-400"),
                    h2("No alerts", className="m-0 font-serif text-2xl font-semibold"),
                    p("Show the note again when you need it.", className="m-0 text-sm text-stone-500"),
                ),
                id=self.id,
                className=self.class_rest,
                data_open="0",
            )
        title_id = f"{self.id}-title"
        return kit_shell(self,
            span(self.KIND, className=self.class_kicker),
            h2(self.TITLE, id=title_id, className=self.class_title),
            p(self.BODY, className=self.class_lede),
            button("Dismiss", type="button", className=self.class_x, **bind(self.dismiss)),
            id=self.id,
            className=self.class_card,
            role="alert",
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
