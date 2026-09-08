"""Drop-in pricing section — comparison table of named tiers.

Host seam: override ``TIERS`` / ``FEATURES``. Choosing is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. Caps: none. A11y: ``<table>`` with ``scope=col``.
Choose binds the button, not the row (table checkbox-not-tr pattern).
Not Plans (no radiogroup of whole cards).
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
    table,
    tbody,
    td,
    th,
    thead,
    tr,
)


class PricingSection(Component):
    """Compare named desks. The selected key is MorphState.

    ``TIERS`` is ``(key, name, price)``. ``FEATURES`` is ``(label, {key: cell})``.
    """

    id = "pricingsection"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full min-w-0 max-w-[44rem] flex-col gap-4 "
        "overflow-x-auto rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_table = "w-full min-w-[28rem] border-collapse text-sm"
    class_th = "px-3 py-3 text-left font-medium"
    class_td = "border-t border-stone-100 px-3 py-3 text-stone-600"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border "
        "border-stone-200 bg-white px-4 text-sm"
    )
    class_btn_on = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border-0 "
        "bg-stone-900 px-4 text-sm text-stone-50"
    )

    TIERS = (
        ("studio", "Studio", "48"),
        ("atelier", "Atelier", "96"),
        ("house", "House", "180"),
    )
    FEATURES = (
        ("Seats", {"studio": "1", "atelier": "4", "house": "The house"}),
        ("Cut", {"studio": "Winter list", "atelier": "Priority", "house": "Private rail"}),
        ("Live", {"studio": "—", "atelier": "Morph", "house": "Caps included"}),
    )

    value = MorphState("studio")

    def _tiers(self):
        return tuple(self.TIERS)

    def render(self):
        val = str(self.value or self._tiers()[0][0])
        keys = {row[0] for row in self._tiers()}
        if val not in keys:
            val = self._tiers()[0][0]
        heads = [th("Feature", scope="col", className=self.class_th)]
        for key, name, price in self._tiers():
            heads.append(th(f"{name} · ${price}", scope="col", className=self.class_th))
        body = []
        for label, cells in self.FEATURES:
            body.append(
                tr(
                    th(label, scope="row", className=self.class_td),
                    *[td(cells.get(key, "—"), className=self.class_td) for key, _n, _p in self._tiers()],
                )
            )
        chooses = [
            td(
                button(
                    "Current" if key == val else "Choose",
                    type="button",
                    className=self.class_btn_on if key == val else self.class_btn,
                    aria_pressed="true" if key == val else "false",
                    **bind(self.choose, key=key),
                ),
                className=self.class_td,
            )
            for key, _n, _p in self._tiers()
        ]
        body.append(tr(th("Join", scope="row", className=self.class_td), *chooses))
        chosen = next((n for k, n, _p in self._tiers() if k == val), val)
        return div(
            span("Join", className=self.class_kicker),
            h2("Desks", className=self.class_title),
            p(f"Selected · {chosen}. Picking is public.", className=self.class_lede),
            table(
                thead(tr(*heads)),
                tbody(*body),
                className=self.class_table,
            ),
            id=self.id,
            className=self.class_card,
            data_value=val,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._tiers()}
        self.value = key if key in keys else self._tiers()[0][0]
        return update_with(self, extra_ops=[notify(str(self.value))])
