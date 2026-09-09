"""Drop-in nav menu — disclosure of named destinations.

Host seam: construct kwargs OR subclass.
Accepted: ``items`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``, ``value``. Caps: none. A11y (APG Menu): trigger
``aria-haspopup=menu`` ``aria-expanded``; panel ``role=menu`` / ``menuitem``.
Escape on scrim.
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
    MorphState,
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


class NavMenu(Kit):
    """Desktop menu. Value is a named key. Menu is presence."""

    id = "navmenu"
    _SEAMS = {'items': 'ITEMS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_wrap = "relative z-20 max-w-72"
    class_trigger = (
        "flex min-h-11 w-full cursor-pointer items-center justify-between gap-4 "
        "rounded-2xl border border-stone-200 bg-stone-50 px-4 text-sm"
    )
    class_menu = (
        "absolute left-0 right-0 top-[calc(100%+0.35rem)] z-30 flex flex-col "
        "rounded-2xl border border-stone-200 bg-white p-1.5 shadow-lg"
    )
    class_item = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3.5 text-left text-sm hover:bg-stone-100"
    )
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"

    ITEMS = (
        ("desk", "Desk"),
        ("catalog", "Catalog"),
        ("billing", "Billing"),
    )

    open = MorphState(False)
    value = MorphState("desk")

    def _items(self):
        return tuple(self.ITEMS)

    def render(self):
        val = str(self.value or self._items()[0][0])
        is_open = bool(self.open)
        shown = next((lab for k, lab in self._items() if k == val), val)
        rows = [
            button(
                lab,
                type="button",
                role="menuitem",
                className=self.class_item,
                **bind(self.choose, key=key),
            )
            for key, lab in self._items()
        ] if is_open else []
        menu = (
            div(*rows, id=f"{self.id}-menu", className=self.class_menu, role="menu")
            if is_open else span("", className=self.class_sr)
        )
        scrim = (
            button(
                span("Close", className=self.class_sr),
                type="button",
                className=self.class_scrim,
                aria_label="Close menu",
                data_channel_on="click keydown.escape",
                **bind(self.toggle),
            )
            if is_open else span("", className=self.class_sr)
        )
        return self.kit_shell(
            scrim,
            div(
                button(
                    shown,
                    type="button",
                    id=f"{self.id}-trigger",
                    className=self.class_trigger,
                    aria_haspopup="menu",
                    aria_expanded="true" if is_open else "false",
                    aria_controls=f"{self.id}-menu",
                    **bind(self.toggle),
                ),
                menu,
                className=self.class_wrap,
            ),
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
            data_value=val,
            chrome=(
                span("Jump", className=self.class_kicker),
                h2("Go somewhere", className=self.class_title),
                p("A named destination. Opening the menu is public.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {k for k, _ in self._items()}
        if key in keys:
            self.value = key
        self.open = False
        return update_with(self, extra_ops=[notify(str(self.value))])
