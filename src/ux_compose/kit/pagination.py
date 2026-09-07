"""Drop-in pagination — opaque page keys, never a quantity MorphState.

Host seam: override ``PAGES`` and ``WINDOW``. Keys are names (``p1``), not ints.
``WINDOW`` is how many numbered neighbors sit next to the current page.

The bar never paints every key. Core is a sliding window (always visible).
First / last + gaps are ``max-sm:hidden`` so they cannot sit on the
chevrons on a narrow card. Prev goes one named page back, never to p1.

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
    path,
    span,
    svg,
    ul,
)


def _chevron(direction: str):
    d = "M15 6 9 12l6 6" if direction == "left" else "M9 6l6 6-6 6"
    return svg(
        path(
            d=d,
            fill="none",
            stroke="currentColor",
            **{
                "stroke-width": "1.75",
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
            },
        ),
        **{
            "viewBox": "0 0 24 24",
            "aria-hidden": "true",
            "focusable": "false",
        },
        className="pointer-events-none block h-5 w-5",
    )


def page_slots(idx: int, n: int, window: int = 1):
    """Sliding core + optional first/last.

    Each item is ``("page", i, "core"|"edge")`` or ``("gap", "edge")``.
    ``edge`` chrome is hidden below ``sm`` so a phone never stacks
    page 1 on top of Prev.
    """
    if n <= 0:
        return ()
    idx = min(max(idx, 0), n - 1)
    siblings = max(0, int(window or 0))
    span = 2 * siblings + 1
    if n <= span:
        return tuple(("page", i, "core") for i in range(n))
    start = min(max(0, idx - siblings), n - span)
    core = list(range(start, start + span))
    out = []
    if core[0] > 0:
        out.append(("page", 0, "edge"))
        if core[0] == 2:
            out.append(("page", 1, "edge"))
        elif core[0] > 2:
            out.append(("gap", "edge"))
    for i in core:
        out.append(("page", i, "core"))
    if core[-1] < n - 1:
        if core[-1] == n - 3:
            out.append(("page", n - 2, "edge"))
        elif core[-1] < n - 2:
            out.append(("gap", "edge"))
        out.append(("page", n - 1, "edge"))
    return tuple(out)


class Pagination(Component):
    """Named pages. Channel refuses quantity MorphState, so keys are ``p1``…

    ``PAGES`` is ``(key, (item, …))``. Override on the copy.
    ``WINDOW`` is neighbors each side of the current page (default 1).
    A denser blog pager is ``WINDOW = 2``. Tighter is ``WINDOW = 0``.
    """

    id = "pagination"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_list = "m-0 grid list-none gap-1.5 p-0"
    class_item = "rounded-2xl bg-stone-50 px-4 py-3 text-sm"
    class_bar = "mt-1 flex min-w-0 flex-nowrap items-center gap-1"
    class_pages = (
        "flex min-w-0 flex-1 flex-nowrap items-center justify-center gap-0.5 overflow-hidden"
    )
    class_nav = (
        "relative z-10 inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-200 bg-white text-stone-900 "
        "hover:bg-stone-100 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "disabled:cursor-default disabled:opacity-40 disabled:hover:bg-white"
    )
    class_dot = (
        "inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent text-sm text-stone-500 "
        "hover:bg-stone-100 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_dot_on = (
        "inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-stone-800 text-sm text-stone-50 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/20"
    )
    class_dot_edge = (
        "hidden sm:inline-flex size-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent text-sm text-stone-500 "
        "hover:bg-stone-100 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_gap = (
        "pointer-events-none hidden min-h-11 min-w-6 shrink-0 items-center justify-center "
        "text-sm text-stone-400 sm:inline-flex"
    )
    class_sr = "sr-only"

    # Host seam. Neighbors each side of the current page.
    WINDOW = 1

    PAGES = (
        ("p1", ("Work shirt", "Serving board")),
        ("p2", ("Throw", "Pourer")),
        ("p3", ("Oak stool", "Wool cap")),
        ("p4", ("Clay lamp", "Stone bowl")),
        ("p5", ("Linen napkin", "Wool scarf")),
        ("p6", ("Oak tray", "Clay cup")),
        ("p7", ("Stone vase", "Brass hook")),
        ("p8", ("Wool blanket", "Linen bag")),
        ("p9", ("Clay bowl", "Oak spoon")),
        ("p10", ("Brass lamp", "Stone tile")),
        ("p11", ("Linen apron", "Wool mitt")),
        ("p12", ("Oak bench", "Clay jug")),
    )

    page = MorphState("p1")

    def _pages(self):
        return tuple(self.PAGES)

    def _keys(self):
        return tuple(row[0] for row in self._pages())

    def _window(self) -> int:
        return max(0, int(getattr(self, "WINDOW", 1) or 0))

    def _current(self):
        keys = self._keys()
        cur = str(self.page or keys[0])
        if cur not in keys:
            cur = keys[0]
        for key, items in self._pages():
            if key == cur:
                return key, items
        return keys[0], self._pages()[0][1]

    def _nav(self, direction: str, fn, label: str, *, muted: bool):
        slot = "prev" if direction == "left" else "next"
        return button(
            span(label, className=self.class_sr),
            _chevron(direction),
            type="button",
            id=f"{self.id}-{slot}",
            className=self.class_nav,
            aria_label=label,
            **({"disabled": True, "aria_disabled": "true"} if muted else {}),
            **({} if muted else bind(fn)),
        )

    def _page_btn(self, slot: int, cur: str, keys: tuple, *, edge: bool):
        key = keys[slot]
        on = key == cur
        cls = self.class_dot_on if on else (self.class_dot_edge if edge else self.class_dot)
        return button(
            str(slot + 1),
            type="button",
            id=f"{self.id}-page-{key}",
            className=cls,
            aria_label=f"Page {slot + 1}",
            **({"aria_current": "page"} if on else {}),
            **bind(self.goto, key=key),
        )

    def render(self):
        keys = self._keys()
        cur, items = self._current()
        idx = keys.index(cur)
        n = len(keys)
        lis = [li(name, className=self.class_item, id=f"{self.id}-item-{i}") for i, name in enumerate(items)]
        dots = []
        for kind, *rest in page_slots(idx, n, self._window()):
            if kind == "gap":
                dots.append(span("…", className=self.class_gap, aria_hidden="true"))
                continue
            slot, band = rest
            dots.append(self._page_btn(slot, cur, keys, edge=band == "edge"))
        return div(
            span("Catalog", className=self.class_kicker),
            h2("The shelf", className=self.class_title),
            p(f"Page {idx + 1} of {n}", className=self.class_lede),
            ul(*lis, className=self.class_list),
            div(
                self._nav("left", self.prev, "Previous page", muted=idx == 0),
                div(
                    *dots,
                    className=self.class_pages,
                    id=f"{self.id}-pages",
                    role="navigation",
                    aria_label="Pages",
                ),
                self._nav("right", self.next, "Next page", muted=idx >= n - 1),
                className=self.class_bar,
            ),
            id=self.id,
            className=self.class_card,
            role="region",
            data_page=cur,
            data_of=str(n),
            data_window=str(self._window()),
            data_channel_id=self.id,
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
