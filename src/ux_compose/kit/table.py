"""Drop-in data table — sort key MorphState, selection RefState.

Host seam: override ``ROWS`` / ``COLUMNS`` and ``on_archive(skus)``.
Archiving spends a Cap. Selecting is public.
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
    p,
    span,
)


class Table(Component):
    """Sortable rows with a selection set.

    ``COLUMNS`` is ``(key, label)``. ``ROWS`` is ``(sku, {col: value})``.
    Quantity never lives on MorphState.
    """

    id = "table"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_danger = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-rose-800 px-5 text-sm font-medium text-rose-50 hover:bg-rose-700"
    )
    class_btn_muted = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-400"
    )
    class_toolbar = "flex flex-wrap items-center justify-between gap-3"
    class_wrap = "overflow-x-auto"
    class_grid = "flex min-w-[28rem] flex-col gap-0.5"
    class_head = (
        "grid grid-cols-[2.75rem_1fr_5.5rem_4.2rem] items-center gap-2 px-1.5 pb-2"
    )
    class_th = (
        "min-h-11 cursor-pointer border-0 bg-transparent p-0 text-left text-xs "
        "font-semibold uppercase tracking-widest text-stone-400"
    )
    class_th_on = (
        "min-h-11 cursor-pointer border-0 bg-transparent p-0 text-left text-xs "
        "font-semibold uppercase tracking-widest text-stone-900"
    )
    class_tr = (
        "grid grid-cols-[2.75rem_1fr_5.5rem_4.2rem] items-center gap-2 rounded-xl "
        "px-1.5 py-1.5 hover:bg-stone-50"
    )
    class_tr_on = (
        "grid grid-cols-[2.75rem_1fr_5.5rem_4.2rem] items-center gap-2 rounded-xl "
        "bg-stone-100 px-1.5 py-1.5"
    )
    class_td = "text-sm"
    class_td_price = "text-sm tabular-nums"
    class_check = (
        "flex h-11 w-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent p-0"
    )
    class_box = (
        "flex h-5 w-5 items-center justify-center rounded-md border border-stone-300 "
        "bg-white text-[0.65rem] font-semibold text-white"
    )
    class_box_on = (
        "flex h-5 w-5 items-center justify-center rounded-md border-0 "
        "bg-stone-800 text-[0.65rem] font-semibold text-white"
    )
    class_sr = "sr-only"

    COLUMNS = (
        ("name", "Piece"),
        ("stage", "Stage"),
        ("price", "Price"),
    )
    ROWS = (
        ("linen-01", {"name": "Work shirt", "stage": "cut", "price": "48"}),
        ("oak-02", {"name": "Serving board", "stage": "make", "price": "72"}),
        ("wool-03", {"name": "Throw", "stage": "keep", "price": "96"}),
        ("clay-04", {"name": "Pourer", "stage": "cut", "price": "38"}),
    )

    items = RefState(())
    cleared = MorphState(False)
    sort = MorphState("name")
    selected = RefState(())
    stamp = MorphState("idle")

    def on_archive(self, skus: tuple[str, ...]) -> str:
        """Host seam. Return toast copy after the Cap spent."""
        n = len(skus)
        return f"Archived {n} piece" if n == 1 else f"Archived {n} pieces"

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _rows(self):
        key = str(self.sort or "name")
        if bool(self.cleared):
            rows = list(self.items or ())
        else:
            live = tuple(self.items or ())
            rows = list(live if live else self.ROWS)

        def val(row):
            return str((row[1] or {}).get(key, ""))

        return tuple(sorted(rows, key=val))

    def _cell(self, key: str, cols: dict) -> str:
        raw = str(cols.get(key, ""))
        if key == "price" and raw and not raw.startswith("$"):
            return f"${raw}"
        return raw

    def render(self):
        sel = set(self.selected or ())
        sort = str(self.sort or "name")
        heads = []
        for key, label in self.COLUMNS:
            on = key == sort
            heads.append(
                button(
                    f"{label} ▾" if on else label,
                    type="button",
                    className=self.class_th_on if on else self.class_th,
                    **bind(self.sort_by, key=key),
                )
            )
        body = []
        for sku, cols in self._rows():
            on = sku in sel
            cells = [
                span(
                    self._cell(k, cols),
                    className=self.class_td_price if k == "price" else self.class_td,
                )
                for k, _ in self.COLUMNS
            ]
            body.append(
                div(
                    button(
                        span("On" if on else "Off", className=self.class_sr),
                        span("✓" if on else "", className=self.class_box_on if on else self.class_box),
                        type="button",
                        className=self.class_check,
                        aria_pressed="true" if on else "false",
                        **bind(self.toggle_row, sku=sku),
                    ),
                    *cells,
                    id=f"row-{sku}",
                    className=self.class_tr_on if on else self.class_tr,
                )
            )
        empty = not body
        n = len(sel)
        return div(
            span("Catalog", className=self.class_kicker),
            h2("Pieces on the table", className=self.class_title),
            div(
                p(f"{n} selected", className=self.class_lede),
                button(
                    "Archive selected",
                    type="button",
                    className=self.class_btn_danger if n else self.class_btn_muted,
                    **bind(self.archive),
                ),
                className=self.class_toolbar,
            ),
            div(
                div(
                    div(*heads, className=self.class_head),
                    *body,
                    p("Nothing on the table.", className=self.class_lede) if empty else span("", className=self.class_sr),
                    className=self.class_grid,
                ),
                className=self.class_wrap,
            ),
            id=self.id,
            className=self.class_card,
        )

    @action(caps=())
    def sort_by(self, key: str = "name"):
        keys = {k for k, _ in self.COLUMNS}
        self.sort = key if key in keys else "name"
        return update_with(self)

    @action(caps=())
    def toggle_row(self, sku: str = ""):
        known = {row[0] for row in self._rows()}
        cur = set(self.selected or ())
        if sku in cur:
            cur.remove(sku)
        elif sku and sku in known:
            cur.add(sku)
        self.selected = tuple(sorted(cur))
        self._tick()
        return update_with(self)

    @action(caps=("items.archive",))
    def archive(self):
        skus = tuple(self.selected or ())
        if not skus:
            return update_with(self, extra_ops=[notify("Nothing selected")])
        remaining = tuple(row for row in self._rows() if row[0] not in set(skus))
        self.items = remaining
        self.cleared = True
        self.selected = ()
        self._tick()
        return update_with(self, extra_ops=[notify(self.on_archive(skus))])
