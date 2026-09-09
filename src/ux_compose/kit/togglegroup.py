"""Drop-in toggle group — exclusive named segment, APG radio group.

Host seam: construct kwargs OR subclass.
Accepted: ``items`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. Caps: none. A11y (APG Radio Group):
``role=radiogroup`` labelledby the title; each option ``role=radio``
``aria-checked``; selected ``tabindex=0`` others ``-1``. Ids are
``{id}-opt-{k}``. Not Tabs (no tabpanels) and not Badge (status chips).
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


class ToggleGroup(Kit):
    """One named band. Exclusive. The key is MorphState.

    ``ITEMS`` is ``(key, label)``. Override on the copy.
    """

    id = "togglegroup"
    _SEAMS = {'items': 'ITEMS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_group = "flex min-w-0 gap-1 overflow-x-auto rounded-full bg-stone-100 p-1"
    class_opt = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-transparent px-4 text-sm font-medium text-stone-500 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_opt_on = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-white px-4 text-sm font-medium text-stone-900 shadow-sm "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )

    ITEMS = (
        ("day", "Day"),
        ("week", "Week"),
        ("month", "Month"),
    )

    value = MorphState("day")

    def _items(self):
        return tuple(self.ITEMS)

    def _current(self):
        items = self._items()
        keys = {row[0] for row in items}
        cur = str(self.value or "")
        if cur not in keys:
            return items[0]
        for row in items:
            if row[0] == cur:
                return row
        return items[0]

    def render(self):
        key, label = self._current()
        title_id = f"{self.id}-label"
        segs = []
        for k, lab in self._items():
            on = k == key
            segs.append(
                button(
                    lab,
                    type="button",
                    id=f"{self.id}-opt-{k}",
                    role="radio",
                    aria_checked="true" if on else "false",
                    tabindex="0" if on else "-1",
                    className=self.class_opt_on if on else self.class_opt,
                    **bind(self.choose, key=k),
                )
            )
        return self.kit_shell(
            span("Range", className=self.class_kicker),
            h2("How far", id=title_id, className=self.class_title),
            p(f"Showing {label.lower()}. Picking is public.", className=self.class_lede),
            div(
                *segs,
                className=self.class_group,
                role="radiogroup",
                aria_labelledby=title_id,
            ),
            id=self.id,
            className=self.class_card,
            data_value=key,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._items()}
        self.value = key if key in keys else self._items()[0][0]
        return update_with(self, extra_ops=[notify(str(self.value))])
