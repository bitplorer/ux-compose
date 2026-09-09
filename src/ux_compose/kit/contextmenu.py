"""Drop-in context menu — click or longpress on the same control.

Host seam: render slots OR subclass.
Accepted: ``items`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``, ``dirty``. RefState: ``ran``. Caps: none.
A11y (APG Menu): trigger ``aria-haspopup=menu`` ``aria-expanded``
``aria-controls``; panel ``role=menu`` ``menuitem``. Escape on scrim.
Longpress lives on the *trigger*, not the host, so menu items do not
inherit it. The menu is a floating panel (list-none), not a native tab/list.
"""

from __future__ import annotations

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
    li,
    p,
    span,
    ul,
)


def _plan(name: str, target: str, *, ms: int = 120):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene(name).enter(target, rise.enter(ms=ms))
    except Exception:
        return None


class ContextMenu(Component):
    """Hold or click the canvas. Items are named keys."""

    id = "contextmenu"
    _SEAMS = {'items': 'ITEMS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_stage = "relative"
    class_canvas = (
        "flex min-h-40 w-full cursor-pointer flex-col items-center justify-center gap-1 "
        "rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 text-center "
        "select-none"
    )
    class_menu = (
        "absolute left-1/2 top-1/2 z-30 m-0 flex w-56 list-none "
        "-translate-x-1/2 -translate-y-1/2 flex-col rounded-2xl "
        "border border-stone-200 bg-white p-1.5 shadow-xl"
    )
    class_item = "m-0 block list-none p-0"
    class_row = (
        "flex min-h-11 w-full cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3 text-left text-sm text-stone-900 hover:bg-stone-100 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_scrim = "fixed inset-0 z-20 cursor-pointer border-0 bg-transparent"
    class_choice = "m-0 text-sm text-stone-500"
    class_sr = "sr-only"

    ITEMS = (
        ("rename", "Rename"),
        ("duplicate", "Duplicate"),
        ("inspect", "Inspect"),
    )

    open = MorphState(False)
    ran = RefState("")
    dirty = MorphState("idle")

    def on_run(self, key: str) -> str:
        return key.replace("-", " ")

    def _mark_dirty(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        is_open = bool(self.open)
        ran = str(self.ran or "")
        menu_id = f"{self.id}-menu"
        layer = []
        if is_open:
            rows = [
                li(
                    button(
                        label,
                        type="button",
                        role="menuitem",
                        className=self.class_row,
                        **bind(self.run, key=key),
                    ),
                    className=self.class_item,
                )
                for key, label in self.ITEMS
            ]
            layer = [
                button(
                    span("Close", className=self.class_sr),
                    type="button",
                    className=self.class_scrim,
                    aria_label="Close menu",
                    data_channel_on="click keydown.escape",
                    **bind(self.close),
                ),
                ul(*rows, id=menu_id, className=self.class_menu, role="menu"),
            ]
        return kit_shell(self,
            p(
                "The trigger accepts both pointers. Items stay on click only.",
                className=self.class_lede,
            ),
            p(f"Ran · {ran}" if ran else "No command yet.", className=self.class_choice),
            div(
                button(
                    span("Hold · or click", className="text-sm font-medium text-stone-700"),
                    span("Opens the same menu.", className="text-xs text-stone-400"),
                    type="button",
                    className=self.class_canvas,
                    aria_haspopup="menu",
                    aria_expanded="true" if is_open else "false",
                    aria_controls=menu_id,
                    data_channel_on="click longpress delay:480",
                    **bind(self.open_menu),
                ),
                *layer,
                className=self.class_stage,
            ),
            id=self.id,
            className=self.class_card,
            role="region",
            data_open="1" if is_open else "0",
            data_channel_id=self.id,
            chrome=(
                span("Hold or click", className=self.class_kicker),
                h2("Context menu", className=self.class_title),
            ),
        )

    @action(caps=())
    def open_menu(self):
        self.open = True
        self._mark_dirty()
        return update_with(self, _plan("ctx-open", f"#{self.id}"))

    @action(caps=())
    def close(self):
        self.open = False
        self._mark_dirty()
        return update_with(self)

    @action(caps=())
    def run(self, key: str = ""):
        keys = {row[0] for row in self.ITEMS}
        if key not in keys:
            return update_with(self)
        self.ran = key
        self.open = False
        self._mark_dirty()
        return update_with(self, extra_ops=[notify(self.on_run(key))])
