"""Drop-in hover card — richer tooltip, non-modal dialog.

Host seam: override copy. Opening is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. Caps: none. A11y: trigger ``aria-expanded``
``aria-haspopup=dialog``; panel ``role=dialog`` without aria-modal.
Escape on scrim. Sibling of Popover with denser body.
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


class HoverCard(Component):
    """Preview a person or piece without leaving the row."""

    id = "hovercard"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_wrap = "relative z-20 inline-flex"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border-0 "
        "bg-transparent px-1 text-sm font-medium underline underline-offset-2"
    )
    class_panel = (
        "absolute left-0 top-[calc(100%+0.4rem)] z-30 w-64 rounded-2xl border "
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
                span("Maker", className=self.class_kicker),
                h2("Ada Lovelace", id=title_id, className="m-0 text-base font-semibold"),
                p("Notes, a winter catalog, nothing due tonight.", className=self.class_lede + " mt-1"),
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
            span("Preview", className=self.class_kicker),
            h2("Who made this", className=self.class_title),
            p("Richer than a tooltip. Still not a modal.", className=self.class_lede),
            scrim,
            div(
                button(
                    "Ada Lovelace",
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
