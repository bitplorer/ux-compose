"""Drop-in typeahead — live filter on ``input delay:``.

Unlike Combobox, there is no Filter submit. The field *is* the control.
Host seam: override ``OPTIONS`` and ``on_pick(label)``.
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
    input_,
    li,
    p,
    span,
    ul,
)


class Typeahead(Component):
    """Type. Hits morph. Pick is a name.

    The input carries ``data-channel-action`` + ``data-channel-on=\"input delay:300\"``.
    Live Results morph ``#{id}-hits`` only — the field is not in that HTML, so
    a pause-fired Result cannot rewrite what is still being typed.
    Query is RefState so pick / empty-q still know the string.
    """

    id = "typeahead"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_input = (
        "min-h-12 w-full rounded-2xl border border-stone-200 bg-stone-50 "
        "px-4 py-3 text-sm text-stone-900 outline-none focus:border-stone-400 "
        "focus:bg-white focus:ring-2 focus:ring-stone-900/10"
    )
    class_list = "m-0 flex max-h-56 list-none flex-col gap-0.5 overflow-auto p-0"
    class_row = (
        "flex min-h-11 w-full cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3 text-left text-sm text-stone-900 hover:bg-stone-100"
    )
    class_row_on = (
        "flex min-h-11 w-full cursor-pointer items-center rounded-xl border-0 "
        "bg-stone-100 px-3 text-left text-sm text-stone-900"
    )
    class_empty = "m-0 px-1 py-3 text-sm text-stone-500"
    class_choice = "m-0 text-sm text-stone-500"

    OPTIONS = (
        "Linen work shirt",
        "Oak serving board",
        "Wool throw",
        "Clay pourer",
        "Oak stool",
        "Wool cap",
        "Linen napkin",
        "Clay cup",
    )

    query = RefState("")
    value = MorphState("")
    stamp = MorphState("idle")

    def on_pick(self, label: str) -> str:
        return label

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _hits(self):
        q = str(self.query or "").strip().lower()
        opts = tuple(self.OPTIONS)
        if not q:
            return opts[:6]
        hits = []
        for x in opts:
            xl = x.lower()
            if xl.startswith(q) or any(w.startswith(q) for w in xl.split()):
                hits.append(x)
            if len(hits) >= 8:
                break
        return tuple(hits)

    def _listing(self):
        q = str(self.query or "")
        val = str(self.value or "")
        hits = self._hits()
        rows = [
            li(
                button(
                    x,
                    type="button",
                    className=self.class_row_on if x == val else self.class_row,
                    **bind(self.pick, key=x),
                ),
                id=f"hit-{i}",
            )
            for i, x in enumerate(hits)
        ]
        body = (
            ul(*rows, className=self.class_list, role="listbox")
            if rows
            else p(
                f"No pieces match “{q}”." if q else "Start typing a material.",
                className=self.class_empty,
            )
        )
        return div(body, id=f"{self.id}-hits")

    def render(self):
        q = str(self.query or "")
        val = str(self.value or "")
        return div(
            span("Live filter", className=self.class_kicker),
            h2("Typeahead", className=self.class_title),
            p(
                "The list follows after a 300ms pause. The field keeps what you type.",
                className=self.class_lede,
            ),
            p(f"Picked · {val}" if val else "Nothing picked.", className=self.class_choice),
            input_(
                type="search",
                id=f"{self.id}-q",
                name="q",
                value=q,
                placeholder="Linen, oak, wool…",
                autocomplete="off",
                className=self.class_input,
                aria_autocomplete="list",
                aria_controls=f"{self.id}-hits",
                data_channel_on="input delay:300",
                data_channel_target=f"#{self.id}-hits",
                **bind(self.query_hits),
            ),
            self._listing(),
            id=self.id,
            className=self.class_card,
        )

    def _take_q(self, q: str = "", **kwargs):
        if "q" in kwargs and kwargs["q"] is not None:
            self.query = str(kwargs["q"])
        else:
            self.query = str(q)

    def _hits_slot(self):
        tree = self._listing()
        slot_id = f"{self.id}-hits"

        class _Hits:
            id = slot_id

            def render(self):
                return tree

        return _Hits()

    @action(caps=())
    def query_hits(self, q: str = "", **kwargs):
        self._take_q(q=q, **kwargs)
        self._tick()
        return update_with(self._hits_slot())

    @action(caps=())
    def pick(self, key: str = "", q: str = "", **kwargs):
        self._take_q(q=q, **kwargs)
        opts = set(self.OPTIONS)
        if key not in opts:
            return update_with(self)
        self.value = key
        self.query = key
        self._tick()
        return update_with(self, extra_ops=[notify(self.on_pick(key))])
