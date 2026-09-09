"""Drop-in theme switch — named light / dark / system, APG radio group.

Host seam: construct kwargs OR subclass.
Accepted: ``themes`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. Caps: none. A11y (APG Radio Group):
``role=radiogroup`` labelledby the title; each theme ``role=radio``
``aria-checked``. Not ``role=switch`` — that widget is kit Switch
(boolean quiet hours). Ids are ``{id}-opt-{k}``. Root ``data-theme``.
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


class ThemeSwitch(Kit):
    """Paper, ink, or follow the house. The key is MorphState.

    ``THEMES`` is ``(key, label, lede)``. Override on the copy.
    """

    id = "themeswitch"
    _SEAMS = {'themes': 'THEMES'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_group = "grid grid-cols-3 gap-2"
    class_opt = (
        "flex min-h-20 cursor-pointer flex-col items-start justify-center gap-1 "
        "rounded-2xl border border-stone-200 bg-stone-50 px-4 text-left text-inherit"
    )
    class_opt_on = (
        "flex min-h-20 cursor-pointer flex-col items-start justify-center gap-1 "
        "rounded-2xl border border-stone-800 bg-white px-4 text-left text-inherit shadow-sm"
    )
    class_name = "text-sm font-medium"
    class_hint = "text-xs text-stone-500"

    THEMES = (
        ("light", "Light", "Paper house"),
        ("dark", "Dark", "Ink desk"),
        ("system", "System", "Follow the room"),
    )

    value = MorphState("light")

    def _themes(self):
        return tuple(self.THEMES)

    def _current(self):
        rows = self._themes()
        keys = {row[0] for row in rows}
        cur = str(self.value or "")
        if cur not in keys:
            return rows[0]
        for row in rows:
            if row[0] == cur:
                return row
        return rows[0]

    def render(self):
        key, label, lede = self._current()
        title_id = f"{self.id}-label"
        cards = []
        for k, lab, hint in self._themes():
            on = k == key
            cards.append(
                button(
                    span(lab, className=self.class_name),
                    span(hint, className=self.class_hint),
                    type="button",
                    id=f"{self.id}-opt-{k}",
                    role="radio",
                    aria_checked="true" if on else "false",
                    tabindex="0" if on else "-1",
                    className=self.class_opt_on if on else self.class_opt,
                    **bind(self.choose, key=k),
                )
            )
        return self.kit_shell(
            span("Look", className=self.class_kicker),
            h2("Theme", id=title_id, className=self.class_title),
            p(f"{label} · {lede}. Choosing is public.", className=self.class_lede),
            div(
                *cards,
                className=self.class_group,
                role="radiogroup",
                aria_labelledby=title_id,
            ),
            id=self.id,
            className=self.class_card,
            data_theme=key,
            data_value=key,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._themes()}
        self.value = key if key in keys else self._themes()[0][0]
        return update_with(self, extra_ops=[notify(str(self.value))])
