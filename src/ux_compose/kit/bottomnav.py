"""Drop-in bottom nav — mobile landmark, named sections.

Host seam: render slots OR subclass.
Accepted: ``items`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``active``. Caps: none. A11y: ``nav`` ``aria-label``,
``aria-current=page`` on the active item.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    MorphState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    nav,
    p,
    span,
)


class BottomNav(Component):
    """Phone chrome. One named section. Caps stay off."""

    id = "bottomnav"
    _SEAMS = {'items': 'ITEMS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col "
        "overflow-hidden rounded-3xl border border-stone-200 bg-white text-stone-900 shadow-sm"
    )
    class_pane = "flex min-h-40 flex-col justify-end gap-1 px-6 py-6"
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_bar = "grid grid-cols-3 border-t border-stone-200 bg-stone-50"
    class_item = (
        "flex min-h-14 cursor-pointer flex-col items-center justify-center border-0 "
        "bg-transparent text-xs text-stone-500"
    )
    class_item_on = (
        "flex min-h-14 cursor-pointer flex-col items-center justify-center border-0 "
        "bg-transparent text-xs font-semibold text-stone-900"
    )

    ITEMS = (
        ("desk", "Desk", "A quiet desk"),
        ("catalog", "Catalog", "Winter list"),
        ("you", "You", "Session"),
    )

    active = MorphState("desk")

    def _current(self):
        items = tuple(self.ITEMS)
        cur = str(self.active or items[0][0])
        for row in items:
            if row[0] == cur:
                return row
        return items[0]

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        key, label, title = self._current()
        links = []
        for k, lab, _t in self.ITEMS:
            on = k == key
            links.append(
                button(
                    lab,
                    type="button",
                    className=self.class_item_on if on else self.class_item,
                    **({"aria_current": "page"} if on else {}),
                    **bind(self.select, key=k),
                )
            )
        return kit_shell(self,
            div(
                span(label, className=self.class_kicker),
                h2(title, className=self.class_title),
                className=self.class_pane,
            ),
            nav(*links, className=self.class_bar, aria_label="Sections"),
            chrome=(
                p("The bar is a landmark. Opening a section is public.", className=self.class_lede),
            ),
            id=self.id,
            className=self.class_card,
            data_active=key,
        )

    @action(caps=())
    def select(self, key: str = ""):
        keys = {row[0] for row in self.ITEMS}
        self.active = key if key in keys else "desk"
        return update_with(self, extra_ops=[notify(str(self.active))])
