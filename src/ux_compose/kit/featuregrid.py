"""Drop-in feature grid — named tiles, public select.

Host seam: render slots OR subclass.
Accepted: ``items`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``active``. Caps: none. A11y: list of articles labelledby
each title.
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
    article,
    button,
    div,
    h2,
    h3,
    p,
    span,
)


class FeatureGrid(Component):
    """Three named promises. The active tile is MorphState."""

    id = "featuregrid"
    _SEAMS = {'items': 'ITEMS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_grid = "grid grid-cols-1 gap-3 sm:grid-cols-3"
    class_tile = (
        "flex min-h-36 cursor-pointer flex-col gap-2 rounded-2xl border border-stone-200 "
        "bg-stone-50 px-4 py-4 text-left"
    )
    class_tile_on = (
        "flex min-h-36 cursor-pointer flex-col gap-2 rounded-2xl border border-stone-800 "
        "bg-white px-4 py-4 text-left shadow-sm"
    )
    class_h = "m-0 font-serif text-lg font-medium"

    ITEMS = (
        ("cut", "Cut", "One region morphs. The page does not remount."),
        ("make", "Make", "Actions stay on this Component."),
        ("keep", "Keep", "Caps stay off chrome."),
    )

    active = MorphState("cut")

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        cur = str(self.active or "cut")
        tiles = []
        for key, title, body in self.ITEMS:
            on = key == cur
            tid = f"{self.id}-{key}"
            tiles.append(
                article(
                    button(
                        h3(title, id=tid, className=self.class_h),
                        p(body, className=self.class_lede),
                        type="button",
                        className="flex h-full flex-col gap-2 border-0 bg-transparent p-0 text-left",
                        **bind(self.select, key=key),
                    ),
                    className=self.class_tile_on if on else self.class_tile,
                    aria_labelledby=tid,
                    **({"aria_current": "true"} if on else {}),
                )
            )
        return kit_shell(self,
            div(*tiles, className=self.class_grid),
            id=self.id,
            className=self.class_card,
            data_active=cur,
            chrome=(
                span("Why", className=self.class_kicker),
                h2("How it is made", className=self.class_title),
                p("Pick a tile. Opening is public.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def select(self, key: str = ""):
        keys = {row[0] for row in self.ITEMS}
        self.active = key if key in keys else "cut"
        return update_with(self, extra_ops=[notify(str(self.active))])
