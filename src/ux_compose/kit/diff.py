"""Drop-in diff — named before/after view.

Host seam: construct kwargs OR subclass.
Accepted: ``before``, ``after``, ``views`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``which``. Caps: none. A11y: view radiogroup; each pane labelled.
Not Tabs (no tabpanels of unrelated content).
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


class Diff(Kit):
    """Two copies of a note. The view is a name."""

    id = "diff"
    _SEAMS = {'before': 'BEFORE', 'after': 'AFTER', 'views': 'VIEWS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_pane = "rounded-2xl bg-stone-50 px-4 py-3 font-mono text-sm"

    BEFORE = "Work shirt — marked at the shoulder."
    AFTER = "Work shirt — cut to the shoulder, waxed."
    VIEWS = (("before", "Before"), ("after", "After"), ("split", "Split"))

    which = MorphState("split")

    def render(self):
        which = str(self.which or "split")
        chips = [
            button(
                lab,
                type="button",
                role="radio",
                aria_checked="true" if key == which else "false",
                className="rounded-full px-3 py-2 text-xs " + ("bg-stone-900 text-stone-50" if key == which else "bg-stone-100"),
                **bind(self.choose, key=key),
            )
            for key, lab in self.VIEWS
        ]
        panes = []
        if which in {"before", "split"}:
            panes.append(p(self.BEFORE, className=self.class_pane, aria_label="Before"))
        if which in {"after", "split"}:
            panes.append(p(self.AFTER, className=self.class_pane, aria_label="After"))
        return self.kit_shell(
            div(*chips, className="flex gap-2", role="radiogroup", aria_label="View"),
            div(*panes, className="flex flex-col gap-2"),
            id=self.id,
            className=self.class_card,
            data_which=which,
            chrome=(
                span("Revise", className=self.class_kicker),
                h2("What changed", className=self.class_title),
                p("A named view. Switching is public.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {k for k, _ in self.VIEWS}
        self.which = key if key in keys else "split"
        return update_with(self, extra_ops=[notify(str(self.which))])
