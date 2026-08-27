"""Drop-in combobox — type to filter, then pick.

Query is RefState so the typed filter attaches on morph. Value is a name.
Host seam: override ``OPTIONS``.
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
    form,
    h2,
    input_,
    li,
    p,
    span,
    ul,
)


class Combobox(Component):
    """Filter a Host tuple, pick one value.

    ``OPTIONS`` is a tuple of labels (the label is the key). Override on the copy.
    """

    id = "combobox"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_input = (
        "min-h-11 w-full flex-1 rounded-2xl border border-stone-200 bg-stone-50 "
        "px-4 py-3 text-sm text-stone-900 outline-none focus:border-stone-400 "
        "focus:bg-white focus:ring-2 focus:ring-stone-900/10"
    )
    class_field = "relative"
    class_form = "flex gap-2"
    class_list = (
        "absolute left-0 right-0 top-[calc(100%+0.35rem)] z-20 m-0 flex list-none "
        "flex-col rounded-2xl border border-stone-200 bg-white p-1 shadow-lg"
    )
    class_row = (
        "min-h-11 cursor-pointer rounded-xl border-0 bg-transparent px-3 "
        "text-left text-sm text-inherit hover:bg-stone-100"
    )
    class_row_on = (
        "min-h-11 cursor-pointer rounded-xl border-0 bg-stone-100 px-3 "
        "text-left text-sm text-inherit"
    )
    class_empty = (
        "absolute left-0 right-0 top-[calc(100%+0.35rem)] z-20 m-0 rounded-2xl "
        "border border-stone-200 bg-white px-3 py-3 text-sm text-stone-500 shadow-lg"
    )
    class_sr = "sr-only"

    OPTIONS = (
        "Linen work shirt",
        "Oak serving board",
        "Wool throw",
        "Clay pourer",
        "Oak stool",
        "Wool cap",
    )

    query = RefState("")
    value = MorphState("")
    open = MorphState(False)
    stamp = MorphState("idle")

    def _options(self):
        return tuple(self.OPTIONS)

    def _hits(self):
        q = str(self.query or "").strip().lower()
        opts = self._options()
        if not q:
            return opts
        return tuple(x for x in opts if q in x.lower())

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _take_q(self, q: str = "", **kwargs):
        if q:
            self.query = str(q)
        elif kwargs.get("q") is not None:
            self.query = str(kwargs["q"])

    def render(self):
        q = str(self.query or "")
        val = str(self.value or "")
        is_open = bool(self.open)
        hits = self._hits()
        rows = [
            li(
                button(
                    x,
                    type="button",
                    className=self.class_row_on if x == val else self.class_row,
                    **bind(self.pick, key=x),
                ),
                id=f"combo-{i}",
            )
            for i, x in enumerate(hits[:6])
        ]
        listing = span("", className=self.class_sr)
        if is_open:
            listing = (
                ul(*rows, className=self.class_list, role="listbox")
                if rows
                else p(
                    f"No matches for “{q}”." if q else "No matches.",
                    className=self.class_empty,
                )
            )
        chosen = f"Chosen · {val}" if val else "Nothing chosen yet."
        return div(
            span("Find", className=self.class_kicker),
            h2("Search the catalog", className=self.class_title),
            p(chosen, className=self.class_lede),
            div(
                form(
                    input_(
                        type="search",
                        name="q",
                        value=q,
                        placeholder="Filter pieces",
                        autocomplete="off",
                        className=self.class_input,
                        **bind(self.set_field, field="q"),
                    ),
                    button(
                        "Filter",
                        type="button",
                        className=self.class_btn_primary,
                        **bind(self.type_query),
                    ),
                    id="combobox-form",
                    className=self.class_form,
                ),
                listing,
                className=self.class_field,
            ),
            button(
                "Clear",
                type="button",
                className=self.class_btn_ghost,
                **bind(self.clear),
            )
            if val or q
            else span("", className=self.class_sr),
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
        )

    @action(caps=())
    def type_query(self, q: str = ""):
        self._take_q(q=q)
        self.open = True
        self._tick()
        return update_with(self)

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("q", ""))
        if field in ("q", "query"):
            self.query = "" if raw is None else str(raw)
            self.open = True
            self._tick()
            return update_with(self)
        return None

    @action(caps=())
    def pick(self, key: str = "", q: str = ""):
        self._take_q(q=q)
        if key in self._options():
            self.value = key
            self.query = key
            self.open = False
            self._tick()
            return update_with(self, extra_ops=[notify(key)])
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.query = ""
        self.value = ""
        self.open = False
        self._tick()
        return update_with(self)
