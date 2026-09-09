"""Drop-in accordion — open ids as a MorphState tuple.

Host seam: render slots OR subclass.
Accepted: ``sections`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open_ids`` (identity tuple). Caps: none. A11y (APG Accordion):
header button ``aria-expanded`` ``aria-controls``; panel ``role=region``
``aria-labelledby``. Heading wraps the trigger.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    MorphState,
    action,
    bind,
    update_with,
    button,
    div,
    h2,
    p,
    section,
    span,
)


class Accordion(Component):
    """Set of open panel ids. Tuples are identity, not quantity.

    ``SECTIONS`` is ``(key, title, body)``. Override on the copy.
    """

    id = "accordion"
    _SEAMS = {'sections': 'SECTIONS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-3 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 pb-4 pl-0 text-sm leading-relaxed text-stone-500"
    class_item = "border-t border-stone-200 first:border-t-0"
    class_trigger = (
        "flex min-h-11 w-full cursor-pointer items-center justify-between "
        "gap-4 border-0 bg-transparent py-3 text-inherit "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_item_title = "font-serif text-lg font-medium tracking-tight"
    class_mark = "text-xs font-medium text-stone-400"
    class_caret = "inline-block text-stone-400 transition-transform"
    class_sr = "sr-only"

    SECTIONS = (
        ("fit", "Fit", "Cut to the shoulder. One Component owns the open set — nested pages do not."),
        ("finish", "Finish", "Wax, then rest. Morph this unit; never put html= on a scene enter."),
        ("care", "Care", "Brush, never soak. Reading a section is public. Publishing it would take a Cap."),
    )

    open_ids = MorphState(("fit",))

    def _sections(self):
        return tuple(self.SECTIONS)

    def _open_set(self) -> set[str]:
        raw = self.open_ids
        if raw is None:
            return set()
        if isinstance(raw, str):
            return {raw} if raw else set()
        try:
            return {str(x) for x in raw if str(x)}
        except TypeError:
            return {str(raw)} if raw else set()

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        opened = self._open_set()
        items = []
        for key, title, body in self._sections():
            is_open = key in opened
            caret = span(
                "▾",
                className=self.class_caret + (" rotate-180" if is_open else ""),
                aria_hidden="true",
            )
            btn_id = f"{self.id}-h-{key}"
            panel_id = f"{self.id}-p-{key}"
            items.append(
                section(
                    h2(
                        button(
                            span(title, className=self.class_item_title),
                            span(
                                caret,
                                span("Hide" if is_open else "Show", className=self.class_mark),
                                className="flex items-center gap-2",
                            ),
                            type="button",
                            id=btn_id,
                            className=self.class_trigger,
                            aria_expanded="true" if is_open else "false",
                            aria_controls=panel_id,
                            **bind(self.toggle, key=key),
                        ),
                        className="m-0",
                    ),
                    p(
                        body,
                        id=panel_id,
                        className=self.class_lede,
                        role="region",
                        aria_labelledby=btn_id,
                    ) if is_open else span("", className=self.class_sr, id=panel_id),
                    className=self.class_item,
                    id=f"{self.id}-{key}",
                )
            )
        return kit_shell(self,
            *items,
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Guide", className=self.class_kicker),
                h2("How it is made", className=self.class_title),
            ),
        )

    @action(caps=())
    def toggle(self, key: str = ""):
        keys = {row[0] for row in self._sections()}
        cur = self._open_set()
        if key in cur:
            cur.remove(key)
        elif key and key in keys:
            cur.add(key)
        self.open_ids = tuple(sorted(cur))
        return update_with(self)
