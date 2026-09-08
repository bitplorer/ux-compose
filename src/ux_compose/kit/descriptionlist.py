"""Drop-in description list — named facts as ``dl`` / ``dt`` / ``dd``.

Host seam: override ``ITEMS``. Caps: none.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: none. A11y: native description list. Not a table.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    dd,
    div,
    dl,
    dt,
    h2,
    p,
    span,
)


class DescriptionList(Component):
    """Facts about a piece. Terms and details, not columns."""

    id = "descriptionlist"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_list = "m-0 grid grid-cols-[8rem_1fr] gap-x-4 gap-y-2"
    class_dt = "m-0 text-xs font-medium uppercase tracking-widest text-stone-400"
    class_dd = "m-0 text-sm"

    ITEMS = (
        ("Maker", "Ada"),
        ("Finish", "Oak, waxed"),
        ("Stage", "Keep"),
        ("Price", "$72"),
    )

    def render(self):
        rows = []
        for term, detail in self.ITEMS:
            rows.append(dt(term, className=self.class_dt))
            rows.append(dd(detail, className=self.class_dd))
        return div(
            span("Facts", className=self.class_kicker),
            h2("This piece", className=self.class_title),
            p("A description list, not a data table.", className=self.class_lede),
            dl(*rows, className=self.class_list),
            id=self.id,
            className=self.class_card,
        )
