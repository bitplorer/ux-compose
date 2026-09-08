"""Drop-in rating — named stars, APG radio group.

Host seam: override ``STARS``. Choosing is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value`` (a name, never an int). Caps: none.
A11y (APG Radio Group): ``role=radiogroup`` labelledby; each star
``role=radio`` ``aria-checked``. Not Slider (magnitude).
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


class Rating(Component):
    """How it sits. The key is a name (one … five), not MorphState(int).

    ``STARS`` is ``(key, label)``. Override on the copy.
    """

    id = "rating"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_row = "flex gap-1"
    class_star = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent text-lg text-stone-300"
    )
    class_star_on = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent text-lg text-stone-900"
    )

    STARS = (
        ("one", "1"),
        ("two", "2"),
        ("three", "3"),
        ("four", "4"),
        ("five", "5"),
    )

    value = MorphState("three")

    def _stars(self):
        return tuple(self.STARS)

    def render(self):
        keys = [row[0] for row in self._stars()]
        cur = str(self.value or "three")
        if cur not in keys:
            cur = keys[2] if len(keys) > 2 else keys[0]
        n = keys.index(cur) + 1
        title_id = f"{self.id}-label"
        stars = []
        for i, (key, lab) in enumerate(self._stars(), start=1):
            on = i <= n
            stars.append(
                button(
                    "★",
                    type="button",
                    id=f"{self.id}-opt-{key}",
                    role="radio",
                    aria_checked="true" if key == cur else "false",
                    aria_label=f"{lab} of {len(keys)}",
                    tabindex="0" if key == cur else "-1",
                    className=self.class_star_on if on else self.class_star,
                    **bind(self.choose, key=key),
                )
            )
        return div(
            span("Keep", className=self.class_kicker),
            h2("How it sits", id=title_id, className=self.class_title),
            p(f"{n} of {len(keys)}. The key is a name.", className=self.class_lede),
            div(
                *stars,
                className=self.class_row,
                role="radiogroup",
                aria_labelledby=title_id,
            ),
            id=self.id,
            className=self.class_card,
            data_value=cur,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._stars()}
        self.value = key if key in keys else self._stars()[2][0]
        return update_with(self, extra_ops=[notify(str(self.value))])
