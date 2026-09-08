"""Drop-in alert — inline status with optional public dismiss.

Host seam: override ``TITLE`` / ``BODY`` / ``KIND``. Dismiss is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. Caps: none. A11y: ``role=alert`` for assertive copy.
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


class Alert(Component):
    """Inline warning. Closing morphs the region away."""

    id = "alert"

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

    def render(self):
        if not bool(self.open):
            return div(
                span("Quiet", className="text-xs font-medium uppercase tracking-widest text-stone-400"),
                h2("No alerts", className="m-0 font-serif text-2xl font-semibold"),
                p("Show the note again when you need it.", className="m-0 text-sm text-stone-500"),
                button("Show alert", type="button", className=self.class_x + " border border-stone-200", **bind(self.show)),
                id=self.id,
                className=self.class_rest,
                data_open="0",
            )
        title_id = f"{self.id}-title"
        return div(
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
