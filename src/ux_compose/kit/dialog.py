"""Drop-in dialog — public ask, Cap-protected confirm.

Host seam: override ``on_confirm()``. Opening is public. Destroying is authority.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

Live: the root ``id`` is the region. Channel picks it up.
Swipe lives on Keep it, not the root and not Delete. A host-level
``swipe.horizontal`` on the card swallows clicks the same way
ActionSheet's root ``swipe.vertical`` did. Keep it accepts
``click swipe.down``. Same synthesizer, no extra JS. Delete stays
click-only — it spends a Cap.
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


def _open_plan(cid: str = "dialog"):
    """Enter the overlay after morph inserts it. Selectors only — no html=.

    Presence is a Motion HOF. Same-node chrome is CSS.
    Close is morph-only: the panel is gone after apply, so an exit recipe
    in the same Result has nothing to play.
    """
    try:
        from ux_compose import scene, fade, rise

        if scene is None or fade is None or rise is None:
            return None
        return (
            scene("dialog-open")
            .enter(f"#{cid}-scrim", fade.enter(ms=120))
            .enter(f"#{cid}-panel", rise.enter(ms=180))
        )
    except Exception:
        return None


class Dialog(Component):
    """Confirm overlay. Target id is silent RefState.

    Override ``on_confirm(target)`` in the product. Demo stand-in notifies.
    The resting card stays in flow; the overlay is presence on top of it.
    The card is not a containing block (no ``relative``, no overflow clip)
    so ``fixed`` overlay is not trapped. Panel and scrim keep stable ids.
    Centering is a fixed flex chassis so rise can own transform.
    """

    id = "dialog"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
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
    class_stage = (
        "pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4"
    )
    class_panel = (
        "pointer-events-auto flex w-[min(28rem,calc(100vw-2rem))] "
        "flex-col gap-3 rounded-3xl bg-white px-7 py-6 shadow-xl"
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
                    id=f"{self.id}-scrim",
                    className=self.class_scrim,
                    aria_label="Close",
                    **bind(self.cancel),
                ),
                div(
                    div(
                        h2(
                            str(self.title or "Confirm"),
                            className=self.class_title,
                            id=f"{self.id}-title",
                        ),
                        p(
                            str(self.body or f"Target {who}. This cannot be undone."),
                            className=self.class_lede,
                        ),
                        div(
                            button(
                                "Keep it",
                                type="button",
                                id=f"{self.id}-dismiss",
                                className=self.class_btn_ghost,
                                data_channel_on="click swipe.down",
                                **bind(self.cancel),
                            ),
                            button(
                                "Delete",
                                type="button",
                                id=f"{self.id}-confirm",
                                className=self.class_btn_danger,
                                **bind(self.confirm),
                            ),
                            className=self.class_actions,
                        ),
                        id=f"{self.id}-panel",
                        className=self.class_panel,
                        role="dialog",
                        aria_modal="true",
                        aria_labelledby=f"{self.id}-title",
                    ),
                    className=self.class_stage,
                ),
            ])
        return div(
            *kids,
            id=self.id,
            className=self.class_card,
            data_open="1" if bool(self.open) else "0",
            data_channel_id=self.id,
        )

    @action(caps=())
    def ask(self, id: str = "", title: str = "", body: str = ""):
        self.target = id
        if title:
            self.title = title
        if body:
            self.body = body
        self.open = True
        return update_with(self, _open_plan(self.id))

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
