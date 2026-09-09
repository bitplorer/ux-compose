"""Drop-in action sheet — bottom panel, swipe-down to dismiss.

Host seam: construct kwargs OR subclass.
Accepted: ``actions`` (same type as ``ACTIONS``); ``shell`` (bool; ``False``
renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.

Swipe lives on the handle and Cancel, not the root. OverlayChrome owns
scrim/panel/dismiss ids, handle grammar, and the open plan.

MorphState: ``open``, ``dirty``. RefState: ``picked``. Caps: ``orders.archive``
on archive row. A11y: ``role=dialog`` ``aria-modal`` labelledby. First
action autofocuses on open. Escape on scrim/Cancel via ``dismiss_on()``.
"""

from __future__ import annotations

from ux_compose.kit.overlay import overlay as overlay_chrome

from ux_compose.kit_construct import Kit
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


class ActionSheet(Kit):
    """A sheet from the bottom. Presence is MorphState. Pick is a named key."""

    id = "actionsheet"
    _SEAMS = {'actions': 'ACTIONS'}

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 w-full cursor-pointer items-center justify-center rounded-2xl "
        "border border-stone-200 bg-white px-5 py-3 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_btn_danger = (
        "inline-flex min-h-11 w-full cursor-pointer items-center justify-center rounded-2xl "
        "border-0 bg-rose-700 px-5 py-3 text-sm font-medium text-white hover:bg-rose-800"
    )
    class_scrim = "fixed inset-0 z-40 cursor-pointer border-0 bg-stone-900/40"
    class_panel = (
        "fixed inset-x-0 bottom-0 z-50 flex max-h-[min(28rem,80dvh)] touch-pan-x select-none "
        "flex-col gap-2 rounded-t-3xl border border-stone-200 bg-white px-5 pb-7 pt-1 shadow-xl"
    )
    class_handle_hit = (
        "mx-auto flex min-h-11 w-full cursor-grab items-center justify-center "
        "border-0 bg-transparent p-0"
    )
    class_handle = "pointer-events-none block h-1.5 w-10 rounded-full bg-stone-300"
    class_choice = "m-0 text-sm text-stone-500"
    class_sr = "sr-only"

    ACTIONS = (
        ("share", "Share this piece", False),
        ("pin", "Pin to the desk", False),
        ("archive", "Archive (Cap)", True),
    )

    open = MorphState(False)
    picked = RefState("")
    dirty = MorphState("idle")

    def on_pick(self, key: str) -> str:
        return key.replace("-", " ")

    def _mark_dirty(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def _chrome(self):
        return overlay_chrome(self.id, kind="actionsheet")

    def render(self):
        is_open = bool(self.open)
        picked = str(self.picked or "")
        ch = self._chrome()
        layer = []
        if is_open:
            rows = []
            for i, (key, label, dest) in enumerate(self.ACTIONS):
                extra = {"autofocus": True} if i == 0 else {}
                rows.append(
                    button(
                        label,
                        type="button",
                        className=self.class_btn_danger if dest else self.class_btn_ghost,
                        **extra,
                        **bind(self.pick if not dest else self.archive, key=key),
                    )
                )
            layer = [
                button(
                    span("Close", className=self.class_sr),
                    type="button",
                    id=ch.scrim_id,
                    className=self.class_scrim,
                    aria_label="Close",
                    data_channel_on=ch.dismiss_on(),
                    **bind(self.close),
                ),
                div(
                    button(
                        span("Dismiss", className=self.class_sr),
                        div("", className=self.class_handle),
                        type="button",
                        id=ch.dismiss_id,
                        className=self.class_handle_hit,
                        aria_label="Dismiss",
                        data_channel_on=ch.swipe_on_handle(),
                        **bind(self.close),
                    ),
                    span("Actions", className=self.class_kicker),
                    h2("What next", className=self.class_title, id=f"{self.id}-title"),
                    *rows,
                    button(
                        "Cancel",
                        type="button",
                        id=f"{self.id}-cancel",
                        className=self.class_btn_ghost + " mt-1 text-stone-500",
                        data_channel_on=ch.dismiss_on(),
                        **bind(self.close),
                    ),
                    id=ch.panel_id,
                    className=self.class_panel,
                    role="dialog",
                    aria_modal="true",
                    aria_labelledby=f"{self.id}-title",
                    **ch.focus_attrs(),
                ),
            ]
        return self.kit_shell(
            p(f"Last pick · {picked}" if picked else "Nothing picked yet.", className=self.class_choice),
            button("Open actions", type="button", className=self.class_btn_primary, **bind(self.open_sheet)),
            *layer,
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
            data_channel_id=self.id,
            chrome=(
                span("Sheet · swipe down", className=self.class_kicker),
                h2("Action sheet", className=self.class_title),
                p("Opens from the bottom. Swipe the handle or Cancel to dismiss.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def open_sheet(self):
        self.open = True
        self._mark_dirty()
        return update_with(self, self._chrome().open_plan())

    @action(caps=())
    def close(self):
        self.open = False
        self._mark_dirty()
        return update_with(self)

    @action(caps=())
    def pick(self, key: str = ""):
        keys = {row[0] for row in self.ACTIONS if not row[2]}
        if key not in keys:
            return update_with(self)
        self.picked = key
        self.open = False
        self._mark_dirty()
        return update_with(self, extra_ops=[notify(self.on_pick(key))])

    @action(caps=("orders.archive",))
    def archive(self, key: str = ""):
        self.picked = key or "archive"
        self.open = False
        self._mark_dirty()
        return update_with(self, extra_ops=[notify("archived")])
