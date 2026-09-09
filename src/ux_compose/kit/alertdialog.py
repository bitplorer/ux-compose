"""Drop-in alert dialog — interrupting confirm. Same Host shape as Dialog.

Host seam: render slots OR subclass.
Accepted: ``title``, ``body`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. RefState: ``title``, ``body``. Caps: ``items.delete``
on ``confirm``. A11y (APG Alert Dialog): ``role=alertdialog`` ``aria-modal``
labelledby + describedby. OverlayChrome owns panel ids + open plan. Escape
and scrim do **not** dismiss an interrupting alert — Keep it / Delete are
the explicit choices. Not a second Host — Dialog's sibling with a louder
role.
"""

from __future__ import annotations

from ux_compose.kit.overlay import overlay as overlay_chrome

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
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


class AlertDialog(Component):
    """Must-answer overlay. ``role=alertdialog`` so AT announces immediately."""

    id = "alertdialog"
    _SEAMS = {'title': 'title', 'body': 'body'}

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 hover:bg-stone-100"
    )
    class_btn_danger = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-rose-800 px-5 text-sm font-medium text-rose-50 hover:bg-rose-700"
    )
    class_scrim = "fixed inset-0 z-40 bg-stone-900/40"
    class_stage = "pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4"
    class_panel = (
        "pointer-events-auto flex w-[min(28rem,calc(100vw-2rem))] flex-col gap-3 "
        "rounded-3xl bg-white px-7 py-6 shadow-xl"
    )
    class_actions = "mt-3 flex justify-end gap-2"

    open = MorphState(False)
    title = RefState("This cannot be undone")
    body = RefState("The oak board leaves the catalog.")

    def on_confirm(self) -> str:
        return "Deleted"

    def _chrome(self):
        return overlay_chrome(self.id, kind="dialog")

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        kids = (
            [
                span("Interrupt", className=self.class_kicker),
                h2("Alert dialog", className=self.class_title),
                p("Asking is public. Confirming spends a Cap.", className=self.class_lede),
                button("Delete the board…", type="button", className=self.class_btn_danger, **bind(self.ask)),
            ]
            if getattr(self, "shell", True)
            else []
        )
        if bool(self.open):
            ch = self._chrome()
            title_id = f"{self.id}-title"
            desc_id = f"{self.id}-desc"
            kids.extend([
                div(
                    id=ch.scrim_id,
                    className=self.class_scrim,
                    aria_hidden="true",
                ),
                div(
                    div(
                        h2(str(self.title or "Confirm"), id=title_id, className=self.class_title),
                        p(str(self.body or ""), id=desc_id, className=self.class_lede),
                        div(
                            button(
                                "Keep it",
                                type="button",
                                id=ch.dismiss_id,
                                className=self.class_btn_ghost,
                                autofocus=True,
                                **bind(self.cancel),
                            ),
                            button("Delete", type="button", className=self.class_btn_danger, **bind(self.confirm)),
                            className=self.class_actions,
                        ),
                        id=ch.panel_id,
                        className=self.class_panel,
                        role="alertdialog",
                        aria_modal="true",
                        aria_labelledby=title_id,
                        aria_describedby=desc_id,
                        **ch.focus_attrs(),
                    ),
                    className=self.class_stage,
                ),
            ])
        return kit_shell(self,
            *kids,
            id=self.id,
            className=self.class_card,
            data_open="1" if bool(self.open) else "0",
            data_channel_id=self.id,
        )

    @action(caps=())
    def ask(self):
        self.open = True
        return update_with(self, self._chrome().open_plan())

    @action(caps=())
    def cancel(self):
        self.open = False
        return update_with(self)

    @action(caps=("items.delete",))
    def confirm(self):
        self.open = False
        return update_with(self, extra_ops=[notify(self.on_confirm())])
