"""Drop-in dialog — public ask, Cap-protected confirm.

Host seam: override ``on_confirm()``. Opening is public. Destroying is authority.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
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


class Dialog(Component):
    """Confirm overlay. Target id is silent RefState.

    Override ``on_confirm(target)`` in the product. Demo stand-in notifies.
    The resting card stays in flow; the overlay is presence on top of it.
    """

    id = "dialog"

    class_card = (
        "relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_btn_danger = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-rose-800 px-5 text-sm font-medium text-rose-50 hover:bg-rose-700"
    )
    class_scrim = "fixed inset-0 z-40 cursor-pointer border-0 bg-stone-900/40"
    class_panel = (
        "fixed left-1/2 top-[46%] z-50 flex w-[min(28rem,calc(100vw-2rem))] "
        "-translate-x-1/2 -translate-y-1/2 flex-col gap-3 rounded-3xl "
        "bg-white px-7 py-6 shadow-xl"
    )
    class_actions = "mt-3 flex justify-end gap-2"
    class_sr = "sr-only"

    open = MorphState(False)
    title = RefState("Delete this piece?")
    body = RefState("This cannot be undone.")
    target = RefState("")

    def on_confirm(self, target: str) -> str:
        """Host seam. Return the toast copy. Called after the Cap spent."""
        return f"Deleted {target}" if target else "Deleted"

    def _resting(self):
        return [
            span("Authority", className=self.class_kicker),
            h2("Confirm a delete", className=self.class_title),
            p("Asking is public. Confirming spends a Cap.", className=self.class_lede),
            button(
                "Delete the oak board…",
                type="button",
                className=self.class_btn_danger,
                **bind(self.ask, id="oak-02"),
            ),
        ]

    def render(self):
        kids = list(self._resting())
        if bool(self.open):
            who = str(self.target or "row")
            kids.extend([
                button(
                    span("Close", className=self.class_sr),
                    type="button",
                    className=self.class_scrim,
                    aria_label="Close",
                    **bind(self.cancel),
                ),
                div(
                    h2(str(self.title or "Confirm"), className=self.class_title),
                    p(
                        str(self.body or f"Target {who}. This cannot be undone."),
                        className=self.class_lede,
                    ),
                    div(
                        button(
                            "Keep it",
                            type="button",
                            className=self.class_btn_ghost,
                            **bind(self.cancel),
                        ),
                        button(
                            "Delete",
                            type="button",
                            className=self.class_btn_danger,
                            **bind(self.confirm),
                        ),
                        className=self.class_actions,
                    ),
                    className=self.class_panel,
                    role="dialog",
                    aria_modal="true",
                ),
            ])
        return div(
            *kids,
            id=self.id,
            className=self.class_card,
            data_open="1" if bool(self.open) else "0",
        )

    @action(caps=())
    def ask(self, id: str = "", title: str = "", body: str = ""):
        self.target = id
        if title:
            self.title = title
        if body:
            self.body = body
        self.open = True
        return update_with(self)

    @action(caps=())
    def cancel(self):
        self.open = False
        self.target = ""
        return update_with(self)

    @action(caps=("items.delete",))
    def confirm(self):
        gone = str(self.target or "")
        msg = self.on_confirm(gone)
        self.open = False
        self.target = ""
        return update_with(self, extra_ops=[notify(msg)])
