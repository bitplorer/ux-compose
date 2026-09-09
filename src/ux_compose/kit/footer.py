"""Drop-in footer — contentinfo landmark with named links.

Host seam: render slots OR subclass.
Accepted: ``links`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``here``. Caps: none. A11y: ``footer`` / ``nav`` ``aria-label``,
``aria-current`` on the active crumb.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots
from ux_compose import (
    MorphState,
    action,
    bind,
    notify,
    update_with,
    a,
    div,
    footer,
    nav,
    p,
    span,
)


class Footer(Component):
    """Site floor. Named destinations, not a second Host."""

    id = "footer"
    _SEAMS = {'links': 'LINKS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] flex-col "
        "gap-3 rounded-3xl border border-stone-200 bg-stone-50 px-6 py-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_links = "flex flex-wrap gap-2"
    class_link = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border-0 "
        "bg-transparent px-3 text-sm text-stone-600 hover:bg-white"
    )
    class_link_on = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border-0 "
        "bg-white px-3 text-sm font-medium text-stone-900 shadow-sm"
    )
    class_copy = "m-0 text-xs text-stone-400"

    LINKS = (
        ("desk", "Desk", "/desk"),
        ("catalog", "Catalog", "/catalog"),
        ("care", "Care", "/care"),
    )

    here = MorphState("desk")

    def _links(self):
        return tuple(self.LINKS)

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        cur = str(self.here or self._links()[0][0])
        items = []
        for key, lab, href in self._links():
            on = key == cur
            items.append(
                a(
                    lab,
                    href=href,
                    className=self.class_link_on if on else self.class_link,
                    **({"aria_current": "page"} if on else {}),
                    **bind(self.goto, key=key),
                )
            )
        return footer(
            span("Lumen", className=self.class_kicker),
            nav(*items, className=self.class_links, aria_label="Footer"),
            p("Made to be kept.", className=self.class_copy),
            id=self.id,
            className=self.class_card,
            data_here=cur,
        )

    @action(caps=())
    def goto(self, key: str = ""):
        keys = {row[0] for row in self._links()}
        self.here = key if key in keys else self._links()[0][0]
        return update_with(self, extra_ops=[notify(str(self.here))])
