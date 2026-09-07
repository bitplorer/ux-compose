"""Drop-in sidebar — collapsible rail, one active key.

Host seam: override ``ITEMS``. Opening a section is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    Component,
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


class Sidebar(Component):
    """App rail. Active key is MorphState. Collapse is presence.

    ``ITEMS`` is ``(key, label, title, body)``. Override on the copy.
    """

    id = "sidebar"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] overflow-hidden rounded-3xl "
        "border border-stone-200 bg-white text-stone-900 shadow-sm"
    )
    class_rail = (
        "flex w-44 shrink-0 flex-col gap-1 border-r border-stone-200 bg-stone-50 p-3"
    )
    class_rail_slim = (
        "flex w-16 shrink-0 flex-col gap-1 border-r border-stone-200 bg-stone-50 p-2"
    )
    class_brand = "px-2 py-2 text-xs font-medium uppercase tracking-widest text-stone-400"
    class_item = (
        "flex min-h-11 cursor-pointer items-center rounded-2xl border-0 "
        "bg-transparent px-3 text-left text-sm text-stone-600 hover:bg-white"
    )
    class_item_on = (
        "flex min-h-11 cursor-pointer items-center rounded-2xl border-0 "
        "bg-white px-3 text-left text-sm font-medium text-stone-900 shadow-sm"
    )
    class_item_slim = (
        "flex min-h-11 w-full cursor-pointer items-center justify-center "
        "rounded-2xl border-0 bg-transparent text-sm font-medium text-stone-500 "
        "hover:bg-white"
    )
    class_item_slim_on = (
        "flex min-h-11 w-full cursor-pointer items-center justify-center "
        "rounded-2xl border-0 bg-white text-sm font-medium text-stone-900 shadow-sm"
    )
    class_fold = (
        "mt-auto min-h-11 cursor-pointer rounded-2xl border-0 bg-transparent "
        "px-3 text-left text-xs font-medium text-stone-400 hover:text-stone-900"
    )
    class_pane = "flex min-w-0 flex-1 flex-col gap-2 p-6"
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"

    ITEMS = (
        ("desk", "Desk", "A quiet desk", "Today's pieces stay on this unit. The rail is MorphState."),
        ("catalog", "Catalog", "Winter list", "Linen, oak, wool, clay. Opening a section is public."),
        ("billing", "Billing", "Nothing to pay", "Collapse is presence. Caps stay off chrome."),
    )

    active = MorphState("desk")
    collapsed = MorphState(False)

    def _items(self):
        return tuple(self.ITEMS)

    def _current(self):
        items = self._items()
        keys = {row[0] for row in items}
        cur = str(self.active or "")
        if cur not in keys:
            return items[0]
        for row in items:
            if row[0] == cur:
                return row
        return items[0]

    def render(self):
        key, label, title, body = self._current()
        slim = bool(self.collapsed)
        links = []
        for k, lab, _t, _b in self._items():
            on = k == key
            if slim:
                links.append(
                    button(
                        lab[:1],
                        type="button",
                        title=lab,
                        className=self.class_item_slim_on if on else self.class_item_slim,
                        **bind(self.select, key=k),
                    )
                )
            else:
                links.append(
                    button(
                        lab,
                        type="button",
                        className=self.class_item_on if on else self.class_item,
                        **bind(self.select, key=k),
                    )
                )
        return div(
            div(
                span("Lumen", className=self.class_brand),
                *links,
                button(
                    "Open" if slim else "Fold",
                    type="button",
                    className=self.class_fold,
                    **bind(self.toggle),
                ),
                className=self.class_rail_slim if slim else self.class_rail,
            ),
            div(
                span(label, className=self.class_kicker),
                h2(title, className=self.class_title),
                p(body, className=self.class_lede),
                className=self.class_pane,
            ),
            id=self.id,
            className=self.class_card,
            data_active=key,
            data_collapsed="1" if slim else "0",
        )

    @action(caps=())
    def select(self, key: str = ""):
        keys = {row[0] for row in self._items()}
        self.active = key if key in keys else self._items()[0][0]
        return update_with(self, extra_ops=[notify(str(self.active))])

    @action(caps=())
    def toggle(self):
        self.collapsed = not bool(self.collapsed)
        return update_with(self)
