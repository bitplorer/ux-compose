"""Drop-in tree — APG treeview of named nodes.

Host seam: render slots OR subclass.
Accepted: ``nodes`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``expanded`` (tuple of names), ``selected``. Caps: none.
A11y (APG Tree View): ``role=tree`` / ``treeitem`` ``aria-expanded``
``aria-selected``. ``uxcompose add treeview`` resolves here.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
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


class Tree(Component):
    """House → rooms. Expanded ids are a set of names.

    ``NODES`` is ``(key, parent_or_None, label)``.
    """

    id = "tree"
    _SEAMS = {'nodes': 'NODES'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_list = "m-0 flex list-none flex-col gap-1 p-0"
    class_item = "flex min-h-11 items-center gap-2 rounded-xl px-2 text-sm"
    class_btn = "min-h-11 cursor-pointer rounded-lg border-0 bg-transparent px-2 text-left text-sm"

    NODES = (
        ("house", None, "House"),
        ("linen", "house", "Linen"),
        ("oak", "house", "Oak"),
        ("wool", "house", "Wool"),
    )

    expanded = MorphState(("house",))
    selected = MorphState("linen")

    def _nodes(self):
        return tuple(self.NODES)

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        opened = set(self.expanded or ())
        sel = str(self.selected or "")
        items = []
        for key, parent, lab in self._nodes():
            if parent and parent not in opened:
                continue
            is_parent = any(p == key for _k, p, _l in self._nodes())
            kids = []
            if is_parent:
                kids.append(
                    button(
                        "Close" if key in opened else "Open",
                        type="button",
                        className=self.class_btn,
                        **bind(self.toggle, key=key),
                    )
                )
            kids.append(
                button(
                    lab,
                    type="button",
                    className=self.class_btn + (" font-medium" if key == sel else ""),
                    **bind(self.select, key=key),
                )
            )
            items.append(
                li(
                    *kids,
                    id=f"{self.id}-n-{key}",
                    role="treeitem",
                    aria_selected="true" if key == sel else "false",
                    **({"aria_expanded": "true" if key in opened else "false"} if is_parent else {}),
                    className=self.class_item + (" pl-6" if parent else ""),
                )
            )
        return kit_shell(self,
            p(f"Selected · {sel}. Opening is public.", className=self.class_lede),
            ul(*items, className=self.class_list, role="tree", aria_label="House"),
            id=self.id,
            className=self.class_card,
            data_selected=sel,
            chrome=(
                span("House", className=self.class_kicker),
                h2("Rooms", className=self.class_title),
            ),
        )

    @action(caps=())
    def toggle(self, key: str = ""):
        cur = set(self.expanded or ())
        if key in cur:
            cur.remove(key)
        elif key:
            cur.add(key)
        self.expanded = tuple(sorted(cur))
        return update_with(self)

    @action(caps=())
    def select(self, key: str = ""):
        keys = {row[0] for row in self._nodes()}
        if key in keys:
            self.selected = key
        return update_with(self, extra_ops=[notify(str(self.selected))])
