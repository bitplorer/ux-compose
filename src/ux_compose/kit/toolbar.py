"""Drop-in toolbar — APG toolbar of named commands.

Host seam: override ``GROUPS``. Running a command is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value`` (last command). Caps: none. A11y (APG Toolbar):
``role=toolbar`` labelled; each cluster ``role=group``; ``role=separator``
between groups. Last command ``aria-current`` (not ``aria-pressed`` —
one-shot commands are not toggles). Overflow is a later polish —
this bar stays one row that wraps. Not ToggleGroup (exclusive radios) and
not Tabs (panels).
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
)


class Toolbar(Component):
    """Named commands in groups. The last run key is MorphState.

    ``GROUPS`` is ``(key, label, ((item_key, item_label), …))``.
    """

    id = "toolbar"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_bar = (
        "flex flex-wrap items-center gap-1 rounded-2xl bg-stone-100 p-1"
    )
    class_group = "flex items-center gap-1"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3 text-sm font-medium text-stone-700 hover:bg-white"
    )
    class_btn_on = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-white px-3 text-sm font-medium text-stone-900 shadow-sm"
    )
    class_sep = "mx-1 h-6 w-px bg-stone-300"

    GROUPS = (
        ("file", "File", (("new", "New"), ("open", "Open"))),
        ("edit", "Edit", (("undo", "Undo"), ("redo", "Redo"))),
        ("view", "View", (("preview", "Preview"),)),
    )

    value = MorphState("")

    def _groups(self):
        return tuple(self.GROUPS)

    def _keys(self):
        return {item[0] for _g, _l, items in self._groups() for item in items}

    def render(self):
        val = str(self.value or "")
        nodes = []
        groups = self._groups()
        for i, (gkey, glab, items) in enumerate(groups):
            btns = [
                button(
                    lab,
                    type="button",
                    className=self.class_btn_on if key == val else self.class_btn,
                    **({"aria_current": "true"} if key == val else {}),
                    **bind(self.run, key=key),
                )
                for key, lab in items
            ]
            nodes.append(
                div(*btns, className=self.class_group, role="group", aria_label=glab)
            )
            if i < len(groups) - 1:
                nodes.append(
                    span(
                        "",
                        className=self.class_sep,
                        role="separator",
                        aria_orientation="vertical",
                    )
                )
        shown = val or "none yet"
        return div(
            span("Tools", className=self.class_kicker),
            h2("The strip", className=self.class_title),
            p(f"Last run · {shown}. Commands are public.", className=self.class_lede),
            div(*nodes, className=self.class_bar, role="toolbar", aria_label="Desk tools"),
            id=self.id,
            className=self.class_card,
            data_value=val,
        )

    @action(caps=())
    def run(self, key: str = ""):
        if key in self._keys():
            self.value = key
        return update_with(self, extra_ops=[notify(str(self.value or "none"))])
