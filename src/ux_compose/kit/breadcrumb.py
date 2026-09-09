"""Drop-in breadcrumb — trail of named crumbs.

Host seam: construct kwargs OR subclass.
Accepted: ``trail`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
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
    nav,
    p,
    span,
)


class Breadcrumb(Kit):
    """Path of named keys. ``here`` is MorphState.

    ``TRAIL`` is ``(key, label)``. The current crumb is not a button.
    """

    id = "breadcrumb"
    _SEAMS = {'trail': 'TRAIL'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_trail = "flex flex-wrap items-center gap-1.5 text-sm"
    class_crumb = (
        "min-h-11 cursor-pointer rounded-full border-0 bg-transparent px-2 "
        "font-medium text-stone-500 hover:text-stone-900"
    )
    class_here = "px-2 font-medium text-stone-900"
    class_sep = "text-stone-300"

    TRAIL = (
        ("studio", "Studio"),
        ("catalog", "Catalog"),
        ("oak", "Oak board"),
    )

    here = MorphState("oak")

    def _trail(self):
        return tuple(self.TRAIL)

    def _shown(self):
        rows = self._trail()
        keys = [row[0] for row in rows]
        cur = str(self.here or keys[-1])
        if cur not in keys:
            cur = keys[-1]
        idx = keys.index(cur)
        return rows[: idx + 1], cur

    def render(self):
        shown, cur = self._shown()
        label = shown[-1][1]
        crumbs = []
        for i, (key, lab) in enumerate(shown):
            last = i == len(shown) - 1
            if i:
                crumbs.append(span("/", className=self.class_sep, aria_hidden="true"))
            if last:
                crumbs.append(span(lab, className=self.class_here, aria_current="page"))
            else:
                crumbs.append(
                    button(
                        lab,
                        type="button",
                        className=self.class_crumb,
                        **bind(self.goto, key=key),
                    )
                )
        return self.kit_shell(
            span("Path", className=self.class_kicker),
            nav(*crumbs, className=self.class_trail, aria_label="Breadcrumb"),
            h2(label, className=self.class_title),
            p("The trail is a tuple of names. Walking back is public.", className=self.class_lede),
            id=self.id,
            className=self.class_card,
            data_here=cur,
        )

    @action(caps=())
    def goto(self, key: str = ""):
        keys = {row[0] for row in self._trail()}
        self.here = key if key in keys else self._trail()[-1][0]
        return update_with(self, extra_ops=[notify(str(self.here))])
