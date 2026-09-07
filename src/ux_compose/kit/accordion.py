"""Drop-in accordion — open ids as a MorphState tuple.

Host seam: override ``SECTIONS``. Several panels may be open. Reading is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    Component,
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

    def render(self):
        opened = self._open_set()
        items = []
        for key, title, body in self._sections():
            is_open = key in opened
            caret = span(
                "▾",
                className=self.class_caret + (" rotate-180" if is_open else ""),
                aria_hidden="true",
            )
            items.append(
                section(
                    button(
                        span(title, className=self.class_item_title),
                        span(
                            caret,
                            span("Hide" if is_open else "Show", className=self.class_mark),
                            className="flex items-center gap-2",
                        ),
                        type="button",
                        className=self.class_trigger,
                        aria_expanded="true" if is_open else "false",
                        **bind(self.toggle, key=key),
                    ),
                    p(body, className=self.class_lede) if is_open else span("", className=self.class_sr),
                    className=self.class_item,
                    id=f"acc-{key}",
                )
            )
        return div(
            span("Guide", className=self.class_kicker),
            h2("How it is made", className=self.class_title),
            *items,
            id=self.id,
            className=self.class_card,
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
