"""Drop-in timeline — named events with a named filter.

Host seam: construct kwargs OR subclass.
Accepted: ``lanes``, ``events`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``which``. Caps: none. A11y: filter ``role=radiogroup`` /
``radio``; events ``role=list``. Event keys are names, not indexes.
Not FilterBar (no query field).
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
    li,
    p,
    span,
    ul,
)


class Timeline(Kit):
    """What happened, in order. The lane is a name.

    ``EVENTS`` is ``(lane, title, body)``. ``LANES`` is ``(key, label)``.
    """

    id = "timeline"
    _SEAMS = {'lanes': 'LANES', 'events': 'EVENTS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_chips = "flex flex-wrap gap-1"
    class_chip = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border "
        "border-stone-200 bg-stone-50 px-3 text-xs font-medium"
    )
    class_chip_on = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border-0 "
        "bg-stone-900 px-3 text-xs font-medium text-stone-50"
    )
    class_list = "m-0 flex list-none flex-col gap-2 border-l border-stone-200 p-0 pl-4"
    class_row = "relative text-sm"

    LANES = (
        ("all", "All"),
        ("cut", "Cut"),
        ("make", "Make"),
        ("keep", "Keep"),
    )
    EVENTS = (
        ("cut", "Shirt marked", "Cut"),
        ("make", "Board oiled", "Make"),
        ("keep", "Throw folded", "Keep"),
        ("cut", "Second shirt", "Cut"),
    )

    which = MorphState("all")

    def _lanes(self):
        return tuple(self.LANES)

    def _events(self):
        return tuple(self.EVENTS)

    def _hits(self):
        which = str(self.which or "all")
        rows = []
        for lane, title, lab in self._events():
            if which not in {"", "all"} and lane != which:
                continue
            rows.append((lane, title, lab))
        return tuple(rows)

    def render(self):
        which = str(self.which or "all")
        keys = {row[0] for row in self._lanes()}
        if which not in keys:
            which = self._lanes()[0][0]
        chips = [
            button(
                lab,
                type="button",
                role="radio",
                aria_checked="true" if key == which else "false",
                className=self.class_chip_on if key == which else self.class_chip,
                **bind(self.choose, key=key),
            )
            for key, lab in self._lanes()
        ]
        hits = self._hits()
        items = [
            li(
                span(lab, className="text-xs font-medium uppercase tracking-widest text-stone-400"),
                p(title, className="m-0"),
                className=self.class_row,
            )
            for _lane, title, lab in hits
        ]
        return self.kit_shell(
            div(*chips, className=self.class_chips, role="radiogroup", aria_label="Lane"),
            ul(*items, className=self.class_list, role="list") if items else p("Nothing in this lane.", className=self.class_lede),
            id=self.id,
            className=self.class_card,
            data_which=which,
            chrome=(
                span("When", className=self.class_kicker),
                h2("What happened", className=self.class_title),
                p("A named lane. Filtering is public.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._lanes()}
        self.which = key if key in keys else "all"
        return update_with(self, extra_ops=[notify(str(self.which))])
