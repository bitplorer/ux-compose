"""Drop-in kanban — three named lanes, ids silent.

Host seam: override ``CARDS`` / ``LANES`` and ``on_move`` / ``on_archive``.
Moving is public. Archiving spends a Cap.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
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


def _move_plan(cid: str, sku: str):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene("kanban-move").enter(f"#{cid}-card-{sku}", rise.enter(ms=140))
    except Exception:
        return None


class Kanban(Component):
    """Three columns of piece ids. Membership is RefState. Stamp dirties.

    ``LANES`` is ``(key, label, kicker)``. ``CARDS`` is ``(sku, title, lede)``.
    Lane fields ``cut`` / ``make`` / ``keep`` hold id tuples.
    """

    id = "kanban"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-[44rem] flex-col gap-5 "
        "overflow-x-hidden rounded-[1.75rem] border border-stone-200/90 bg-white p-6 text-stone-900 "
        "shadow-[0_1px_0_rgba(22,21,19,0.04),0_24px_48px_-28px_rgba(22,21,19,0.4)] "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-xs font-medium uppercase tracking-[0.2em] text-stone-500 "
        "dark:text-stone-400"
    )
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_board = "flex min-w-0 gap-3 overflow-x-auto pb-1"
    class_lane = (
        "flex min-w-[9.5rem] flex-1 flex-col gap-2 rounded-2xl bg-stone-50 p-3 "
        "dark:bg-stone-900"
    )
    class_lane_head = "flex items-baseline justify-between gap-2 px-1"
    class_lane_name = "m-0 font-serif text-lg font-medium tracking-tight"
    class_count = (
        "inline-flex min-h-7 min-w-7 items-center justify-center rounded-full "
        "bg-stone-900 px-2 text-xs font-semibold tabular-nums text-stone-50 "
        "dark:bg-stone-100 dark:text-stone-900"
    )
    class_piece = (
        "flex flex-col gap-1 rounded-xl border border-stone-200/80 bg-white px-3 py-3 "
        "shadow-sm transition hover:-translate-y-0.5 hover:shadow "
        "dark:border-stone-700 dark:bg-stone-950"
    )
    class_piece_title = "m-0 text-sm font-semibold tracking-tight"
    class_piece_lede = "m-0 text-xs leading-relaxed text-stone-500 dark:text-stone-400"
    class_actions = "mt-1 flex flex-wrap items-center gap-2"
    class_btn_text = (
        "min-h-11 cursor-pointer rounded-full border-0 bg-transparent px-1 "
        "text-xs font-semibold uppercase tracking-widest text-stone-500 "
        "hover:text-stone-900 dark:text-stone-400 dark:hover:text-stone-50 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_btn_danger = (
        "min-h-11 cursor-pointer rounded-full border-0 bg-transparent px-1 "
        "text-xs font-semibold uppercase tracking-widest text-rose-800 "
        "hover:text-rose-700 dark:text-rose-300 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-800/20"
    )

    LANES = (
        ("cut", "Cut", "Marked"),
        ("make", "Make", "On the bench"),
        ("keep", "Keep", "Held"),
    )
    CARDS = (
        ("linen-01", "Work shirt", "Cut to the shoulder."),
        ("oak-02", "Serving board", "Wax, then rest."),
        ("wool-03", "Throw", "Winter weight."),
        ("clay-04", "Pourer", "Brush, never soak."),
    )

    cut = RefState(("linen-01", "clay-04"))
    make = RefState(("oak-02",))
    keep = RefState(("wool-03",))
    stamp = MorphState("idle")

    def on_move(self, sku: str, to: str) -> str:
        """Host seam. Return toast copy."""
        return f"{sku} → {to}"

    def on_archive(self, sku: str) -> str:
        """Host seam. Called after the Cap spent."""
        return f"archived {sku}"

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _lanes(self):
        return tuple(self.LANES)

    def _cards(self):
        return {row[0]: row for row in self.CARDS}

    def _col(self, name: str):
        return list(getattr(self, name) or ())

    def _lane_keys(self):
        return tuple(row[0] for row in self._lanes())

    def render(self):
        catalog = self._cards()
        keys = self._lane_keys()
        lanes = []
        for key, label, kicker in self._lanes():
            skus = self._col(key)
            cards = []
            nxt = keys[(keys.index(key) + 1) % len(keys)] if keys else key
            for sku in skus:
                _sku, title, lede = catalog.get(sku, (sku, sku, ""))
                cards.append(
                    div(
                        h3(title, className=self.class_piece_title),
                        p(lede, className=self.class_piece_lede),
                        div(
                            button(
                                f"To {nxt}",
                                type="button",
                                className=self.class_btn_text,
                                **bind(self.move, sku=sku, to=nxt),
                            ),
                            button(
                                "Archive",
                                type="button",
                                className=self.class_btn_danger,
                                **bind(self.archive, sku=sku),
                            ),
                            className=self.class_actions,
                        ),
                        id=f"{self.id}-card-{sku}",
                        className=self.class_piece,
                    )
                )
            lanes.append(
                div(
                    div(
                        div(
                            span(kicker, className=self.class_kicker),
                            h3(label, className=self.class_lane_name),
                        ),
                        span(str(len(skus)), className=self.class_count),
                        className=self.class_lane_head,
                    ),
                    *cards,
                    id=f"{self.id}-lane-{key}",
                    className=self.class_lane,
                    data_lane=key,
                )
            )
        return div(
            span("Board", className=self.class_kicker),
            h2("What is open", className=self.class_title),
            p("Ids stay silent. Moving is public. Archive spends a Cap.", className=self.class_lede),
            div(*lanes, className=self.class_board, role="list"),
            id=self.id,
            className=self.class_card,
            data_stamp=str(self.stamp or "idle"),
        )

    @action(caps=())
    def move(self, sku: str = "", to: str = "make"):
        keys = self._lane_keys()
        if to not in keys or not sku:
            return update_with(self)
        for col in keys:
            setattr(self, col, tuple(x for x in self._col(col) if x != sku))
        setattr(self, to, tuple(self._col(to) + [sku]))
        self._tick()
        return update_with(
            self,
            _move_plan(self.id, sku),
            extra_ops=[notify(self.on_move(sku, to))],
        )

    @action(caps=("items.archive",))
    def archive(self, sku: str = ""):
        keys = self._lane_keys()
        for col in keys:
            setattr(self, col, tuple(x for x in self._col(col) if x != sku))
        self._tick()
        return update_with(self, extra_ops=[notify(self.on_archive(sku))])
