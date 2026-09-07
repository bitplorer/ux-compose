"""Drop-in sheet — edge panel. Same shape as a dialog, different placement.

Swipe lives on Close / Done, not the root. OverlayChrome owns
scrim/panel/dismiss ids, dismiss grammar, and the open plan.
"""

from __future__ import annotations

from ux_compose.kit.overlay import overlay as overlay_chrome

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    bind,
    update_with,
    button,
    div,
    h2,
    p,
    span,
)


class Sheet(Component):
    """Drawer from the right. Presence is MorphState. Resting card stays in flow."""

    id = "sheet"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_scrim = "fixed inset-0 z-40 cursor-pointer border-0 bg-stone-900/40"
    class_panel = (
        "fixed top-0 right-0 z-50 flex h-dvh w-[min(22rem,calc(100vw-1.25rem))] "
        "touch-pan-y select-none flex-col gap-3 border-l border-stone-200 bg-white px-6 py-7 shadow-xl"
    )
    class_head = "flex items-start justify-between gap-4"
    class_sr = "sr-only"

    open = MorphState(False)
    title = RefState("Filters")
    body = RefState("Narrow the catalog. Closing morphs the panel away.")
    which = RefState("filters")

    def _chrome(self):
        return overlay_chrome(self.id, kind="sheet")

    def render(self):
        is_open = bool(self.open)
        ch = self._chrome()
        layer = []
        if is_open:
            layer = [
                button(
                    span("Close", className=self.class_sr),
                    type="button",
                    id=ch.scrim_id,
                    className=self.class_scrim,
                    aria_label="Close",
                    **bind(self.close),
                ),
                div(
                    div(
                        span("Panel", className=self.class_kicker),
                        button(
                            "Close",
                            type="button",
                            id=ch.dismiss_id,
                            className=self.class_btn_ghost,
                            data_channel_on=ch.swipe_on_dismiss(),
                            **bind(self.close),
                        ),
                        className=self.class_head,
                    ),
                    h2(
                        str(self.title or "Filters"),
                        className=self.class_title,
                        id=f"{self.id}-title",
                    ),
                    p(str(self.body or ""), className=self.class_lede + " flex-1"),
                    button(
                        "Done",
                        type="button",
                        id=f"{self.id}-done",
                        className=self.class_btn_primary + " mt-auto",
                        data_channel_on=ch.swipe_on_dismiss(),
                        **bind(self.close),
                    ),
                    id=ch.panel_id,
                    className=self.class_panel,
                    role="dialog",
                    aria_modal="true",
                    aria_labelledby=f"{self.id}-title",
                ),
            ]
        return div(
            span("Edge", className=self.class_kicker),
            h2("Filters", className=self.class_title),
            p(
                "A sheet is a dialog that arrives from the side. Swipe right on Close to dismiss.",
                className=self.class_lede,
            ),
            button(
                "Open filters",
                type="button",
                className=self.class_btn_primary,
                **bind(self.open_sheet, which="filters"),
            ),
            *layer,
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
            data_channel_id=self.id,
        )

    @action(caps=())
    def open_sheet(self, which: str = "filters", title: str = "", body: str = ""):
        self.open = True
        self.which = which or "filters"
        if title:
            self.title = title
        if body:
            self.body = body
        return update_with(self, self._chrome().open_plan())

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)
