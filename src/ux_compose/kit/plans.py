"""Drop-in plan cards — radio group as a set of named choices.

Host seam: override ``PLANS`` and ``on_choose(key)``. Picking is public.
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
    button,
    div,
    h2,
    h3,
    p,
    span,
)


class Plans(Component):
    """Choose one named plan. The selected key is MorphState.

    ``PLANS`` is ``(key, name, price, lede, (feature, …))". Override on the copy.
    """

    id = "plans"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full min-w-0 max-w-[44rem] flex-col gap-4 overflow-x-hidden rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_grid = "grid grid-cols-1 gap-3"
    class_plan = (
        "flex min-h-44 cursor-pointer flex-col gap-2 rounded-2xl border "
        "border-stone-200 bg-stone-50 px-5 py-5 text-left text-inherit"
    )
    class_plan_on = (
        "flex min-h-44 cursor-pointer flex-col gap-2 rounded-2xl border "
        "border-stone-800 bg-white px-5 py-5 text-left text-inherit shadow-sm"
    )
    class_name = "m-0 font-serif text-xl font-medium tracking-tight"
    class_price = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_feat = "m-0 text-sm text-stone-500"
    class_mark = "text-xs font-semibold uppercase tracking-widest text-stone-400"

    PLANS = (
        (
            "studio",
            "Studio",
            "48",
            "One quiet desk.",
            ("One seat", "Winter catalog", "Email desk"),
        ),
        (
            "atelier",
            "Atelier",
            "96",
            "The whole floor.",
            ("Four seats", "Priority cut", "Live morph"),
        ),
        (
            "house",
            "House",
            "180",
            "A room of one's own.",
            ("The house", "Private rail", "Caps included"),
        ),
    )

    value = MorphState("atelier")

    def on_choose(self, key: str) -> str:
        """Host seam. Return toast copy."""
        return key

    def _plans(self):
        return tuple(self.PLANS)

    def render(self):
        val = str(self.value or self._plans()[0][0])
        cards = []
        for key, name, price, lede, feats in self._plans():
            on = key == val
            kids = [
                span("Current" if on else "Plan", className=self.class_mark),
                h3(name, className=self.class_name),
                p(f"${price}", className=self.class_price),
                p(lede, className=self.class_lede),
            ]
            for feat in feats:
                kids.append(p(feat, className=self.class_feat))
            cards.append(
                button(
                    *kids,
                    type="button",
                    className=self.class_plan_on if on else self.class_plan,
                    aria_pressed="true" if on else "false",
                    **bind(self.choose, key=key),
                )
            )
        chosen = next((row[1] for row in self._plans() if row[0] == val), val)
        return div(
            span("Join", className=self.class_kicker),
            h2("Choose a desk", className=self.class_title),
            p(f"Selected · {chosen}. Picking is public.", className=self.class_lede),
            div(*cards, className=self.class_grid, role="radiogroup"),
            id=self.id,
            className=self.class_card,
            data_value=val,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._plans()}
        if key in keys:
            self.value = key
        return update_with(self, extra_ops=[notify(self.on_choose(str(self.value)))])
