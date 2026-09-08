"""Drop-in tooltip — described-by hint on MorphState open.

Host seam: override ``TIP``. Opening is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. Caps: none. A11y (APG Tooltip): trigger
``aria-describedby``; tip ``role=tooltip``. Not modal. Escape closes.
"""

from __future__ import annotations

from ux_compose import (
    Component,
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


class Tooltip(Component):
    """Short description of a control. Presence is MorphState."""

    id = "tooltip"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_wrap = "relative z-20 inline-flex"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium"
    )
    class_tip = (
        "absolute left-1/2 top-[calc(100%+0.4rem)] z-30 w-max max-w-56 -translate-x-1/2 "
        "rounded-xl bg-stone-900 px-3 py-2 text-xs text-stone-50 shadow-lg"
    )
    class_sr = "sr-only"

    TIP = "Archive spends items.archive. Hover is public."

    open = MorphState(False)

    def render(self):
        is_open = bool(self.open)
        tip_id = f"{self.id}-tip"
        tip = (
            span(self.TIP, id=tip_id, className=self.class_tip, role="tooltip")
            if is_open else span("", id=tip_id, className=self.class_sr, role="tooltip")
        )
        return div(
            span("Hint", className=self.class_kicker),
            h2("What this does", className=self.class_title),
            p("The tip describes the control. It is not a dialog.", className=self.class_lede),
            div(
                button(
                    "Archive",
                    type="button",
                    id=f"{self.id}-trigger",
                    className=self.class_btn,
                    aria_describedby=tip_id,
                    data_channel_on="click keydown.escape",
                    **bind(self.toggle),
                ),
                tip,
                className=self.class_wrap,
            ),
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
        )

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)
