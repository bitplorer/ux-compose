"""Drop-in tabs — one MorphState key, public select.

Host seam: override ``ITEMS``. Opening a tab is not an authority event.
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
    div,
    h2,
    p,
    button,
    nav,
    section,
    span,
)


class Tabs(Component):
    """Segmented tabs. The active key is MorphState.

    ``ITEMS`` is ``(key, label, title, body)``. Override on the copy.
    """

    id = "tabs"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 overflow-x-hidden "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_tablist = (
        "flex min-w-0 gap-1 overflow-x-auto rounded-full bg-stone-100 p-1"
    )
    class_tab = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-transparent px-4 text-sm font-medium text-stone-500 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_tab_on = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-white px-4 text-sm font-medium text-stone-900 shadow-sm "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_panel = "flex flex-col gap-2 rounded-2xl bg-stone-50 px-5 py-5"

    ITEMS = (
        (
            "overview",
            "Overview",
            "A quiet desk",
            "One region morphs. The page does not remount. Work stays on this Component.",
        ),
        (
            "work",
            "Work",
            "What is open",
            "Three notes, a winter catalog, and nothing due tonight. Actions stay here.",
        ),
        (
            "billing",
            "Billing",
            "Nothing to pay",
            "Opening a tab is not an authority event. Caps stay off chrome.",
        ),
    )

    tab = MorphState("overview")

    def _items(self):
        return tuple(self.ITEMS)

    def _current(self):
        items = self._items()
        keys = {row[0] for row in items}
        cur = str(self.tab or "")
        if cur not in keys:
            return items[0]
        for row in items:
            if row[0] == cur:
                return row
        return items[0]

    def render(self):
        key, label, title, body = self._current()
        segs = []
        for k, lab, _t, _b in self._items():
            on = k == key
            segs.append(
                button(
                    lab,
                    type="button",
                    role="tab",
                    aria_selected="true" if on else "false",
                    className=self.class_tab_on if on else self.class_tab,
                    **bind(self.select, tab=k),
                )
            )
        return div(
            span("Workspace", className=self.class_kicker),
            nav(*segs, className=self.class_tablist, role="tablist"),
            section(
                span(f"Panel · {label}", className=self.class_kicker),
                h2(title, className=self.class_title),
                p(body, className=self.class_lede),
                id=f"tab-{key}",
                className=self.class_panel,
                role="tabpanel",
            ),
            id=self.id,
            className=self.class_card,
            data_tab=key,
        )

    @action(caps=())
    def select(self, tab: str = ""):
        keys = {row[0] for row in self._items()}
        self.tab = tab if tab in keys else self._items()[0][0]
        return update_with(self, extra_ops=[notify(str(self.tab))])
