"""Drop-in popover — non-modal disclosure anchored to a trigger.

Host seam: override ``title`` / ``body`` copy. Opening is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. Caps: none. A11y (APG Popover): trigger
``aria-expanded`` ``aria-controls`` ``aria-haspopup=dialog``. Panel
``role=dialog`` without ``aria-modal`` (non-modal). Escape on scrim.
Not OverlayChrome — no focus trap; dialogs own that.
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


class Popover(Component):
    """Light overlay. Presence is MorphState. Resting trigger stays in flow."""

    id = "popover"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )
    class_wrap = "relative z-20 inline-flex"
    class_panel = (
        "absolute left-0 top-[calc(100%+0.5rem)] z-30 w-72 rounded-2xl border "
        "border-stone-200 bg-white p-4 shadow-lg"
    )
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"

    open = MorphState(False)

    def render(self):
        is_open = bool(self.open)
        title_id = f"{self.id}-title"
        panel = (
            div(
                h2("Winter restock", id=title_id, className="m-0 text-sm font-semibold"),
                p("Linen and oak land Thursday. Closing is public Morph.", className=self.class_lede + " mt-1"),
                id=f"{self.id}-panel",
                className=self.class_panel,
                role="dialog",
                aria_labelledby=title_id,
            )
            if is_open else span("", className=self.class_sr)
        )
        scrim = (
            button(
                span("Close", className=self.class_sr),
                type="button",
                className=self.class_scrim,
                aria_label="Close",
                data_channel_on="click keydown.escape",
                **bind(self.toggle),
            )
            if is_open else span("", className=self.class_sr)
        )
        return div(
            span("Hint", className=self.class_kicker),
            h2("A quiet note", className=self.class_title),
            p("Not a modal. Focus stays in the page.", className=self.class_lede),
            scrim,
            div(
                button(
                    "What's new",
                    type="button",
                    id=f"{self.id}-trigger",
                    className=self.class_btn,
                    aria_expanded="true" if is_open else "false",
                    aria_haspopup="dialog",
                    aria_controls=f"{self.id}-panel",
                    **bind(self.toggle),
                ),
                panel,
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
