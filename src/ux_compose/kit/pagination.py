"""Drop-in pagination — opaque page keys, never a quantity MorphState.

Host seam: override ``PAGES``. Keys are names (``p1``), not ints.
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
    li,
    p,
    span,
    ul,
)


class Pagination(Component):
    """Named pages. Channel refuses quantity MorphState, so keys are ``p1``…

    ``PAGES`` is ``(key, (item, …))``. Override on the copy.
    """

    id = "pagination"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_btn_muted = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-400 "
        "opacity-50"
    )
    class_list = "m-0 grid list-none gap-1.5 p-0"
    class_item = "rounded-2xl bg-stone-50 px-4 py-3 text-sm"
    class_bar = "mt-1 flex items-center justify-between gap-3"
    class_dots = "flex gap-1"
    class_dot = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent text-sm text-stone-500 "
        "hover:bg-stone-100"
    )
    class_dot_on = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-stone-800 text-sm text-stone-50"
    )

    PAGES = (
        ("p1", ("Work shirt", "Serving board")),
        ("p2", ("Throw", "Pourer")),
        ("p3", ("Oak stool", "Wool cap")),
        ("p4", ("Clay lamp", "Stone bowl")),
    )

    page = MorphState("p1")

    def _pages(self):
        return tuple(self.PAGES)

    def _keys(self):
        return tuple(row[0] for row in self._pages())

    def _current(self):
        keys = self._keys()
        cur = str(self.page or keys[0])
        if cur not in keys:
            cur = keys[0]
        for key, items in self._pages():
            if key == cur:
                return key, items
        return keys[0], self._pages()[0][1]

    def render(self):
        keys = self._keys()
        cur, items = self._current()
        idx = keys.index(cur)
        lis = [li(name, className=self.class_item, id=f"page-item-{i}") for i, name in enumerate(items)]
        dots = []
        for i, key in enumerate(keys, start=1):
            on = key == cur
            dots.append(
                button(
                    str(i),
                    type="button",
                    className=self.class_dot_on if on else self.class_dot,
                    aria_current="page" if on else "false",
                    **bind(self.goto, key=key),
                )
            )
        at_start = idx == 0
        at_end = idx >= len(keys) - 1
        return div(
            span("Catalog", className=self.class_kicker),
            h2("The shelf", className=self.class_title),
            p(f"Page {idx + 1} of {len(keys)}", className=self.class_lede),
            ul(*lis, className=self.class_list),
            div(
                button(
                    "Prev",
                    type="button",
                    className=self.class_btn_muted if at_start else self.class_btn_ghost,
                    aria_disabled="true" if at_start else "false",
                    **bind(self.prev),
                ),
                div(*dots, className=self.class_dots),
                button(
                    "Next",
                    type="button",
                    className=self.class_btn_muted if at_end else self.class_btn_ghost,
                    aria_disabled="true" if at_end else "false",
                    **bind(self.next),
                ),
                className=self.class_bar,
            ),
            id=self.id,
            className=self.class_card,
            data_page=cur,
        )

    @action(caps=())
    def goto(self, key: str = ""):
        keys = self._keys()
        self.page = key if key in keys else keys[0]
        return update_with(self, extra_ops=[notify(str(self.page))])

    @action(caps=())
    def next(self):
        keys = self._keys()
        cur, _ = self._current()
        idx = keys.index(cur)
        if idx < len(keys) - 1:
            self.page = keys[idx + 1]
        return update_with(self)

    @action(caps=())
    def prev(self):
        keys = self._keys()
        cur, _ = self._current()
        idx = keys.index(cur)
        if idx > 0:
            self.page = keys[idx - 1]
        return update_with(self)
