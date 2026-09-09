"""Drop-in stats — named metrics as RefState, dirty MorphState.

Host seam: render slots OR subclass.
Accepted: ``items`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``items``. Caps: none. A11y: list of
``role=group`` tiles; each value ``aria-label`` includes the name.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    MorphState,
    RefState,
    action,
    bind,
    update_with,
    button,
    div,
    h2,
    p,
    span,
)


class Stats(Component):
    """Three named counts. Magnitude is RefState; ``dirty`` morphs the card."""

    id = "stats"
    _SEAMS = {'items': 'ITEMS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_grid = "grid grid-cols-3 gap-3"
    class_tile = "flex flex-col gap-1 rounded-2xl bg-stone-50 px-4 py-4"
    class_num = "m-0 font-serif text-3xl font-semibold tracking-tight tabular-nums"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium"
    )

    ITEMS = (
        ("orders", "Orders", "24"),
        ("pieces", "Pieces", "8"),
        ("held", "On hold", "1"),
    )

    items = RefState(())
    dirty = MorphState("idle")

    def _items(self):
        live = tuple(self.items or ())
        return live if live else tuple(self.ITEMS)

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        tiles = [
            div(
                span(lab, className=self.class_kicker),
                p(val, className=self.class_num, aria_label=f"{lab} {val}"),
                className=self.class_tile,
                role="group",
                aria_label=lab,
            )
            for key, lab, val in self._items()
        ]
        return kit_shell(self,
            div(*tiles, className=self.class_grid),
            button("Refresh", type="button", className=self.class_btn, **bind(self.refresh)),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Today", className=self.class_kicker),
                h2("On the desk", className=self.class_title),
                p("Counts live on RefState. Dirty is the morph clock.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def refresh(self):
        self.items = tuple(self.ITEMS)
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self)
