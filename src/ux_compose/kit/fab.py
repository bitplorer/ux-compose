"""Drop-in FAB — floating action with an optional speed-dial menu.

Host seam: construct kwargs OR subclass.
Accepted: ``actions`` (tuple[tuple[str, str], ...] — same type as ``ACTIONS``),
``shell`` (bool; ``False`` is the FAB/menu only, no demo kicker/title/lede card).
Subclass may still override ``ACTIONS`` / ``on_run(key)``; instance attrs win.
Opening is public. Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``, ``value``. Caps: none. A11y: trigger ``aria-haspopup=menu``
``aria-expanded`` ``aria-controls`` the menu id ``{id}-menu``. The menu stays
in the tree with ``hidden`` when closed (honest APG — not omitted). Menu
``role=menu`` / ``menuitem``. Escape on scrim. Not Cta (page ask) and not
NavMenu (destination list).
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
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


class Fab(Kit):
    """A round verb in the corner. The last run key is MorphState."""

    id = "fab"
    _SEAMS = {"actions": "ACTIONS"}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex min-h-64 w-full max-w-xl flex-col "
        "gap-4 overflow-hidden rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_fab = (
        "absolute bottom-5 right-5 z-20 inline-flex h-14 w-14 cursor-pointer items-center "
        "justify-center rounded-full border-0 bg-stone-900 text-lg text-stone-50 shadow-lg"
    )
    class_menu = (
        "absolute bottom-20 right-5 z-30 flex flex-col gap-1 rounded-2xl border "
        "border-stone-200 bg-white p-1.5 shadow-lg"
    )
    class_item = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-transparent "
        "px-3.5 text-left text-sm hover:bg-stone-100"
    )
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"
    class_unit = "relative min-h-20 w-full"

    ACTIONS = (("note", "New note"), ("cut", "New cut"), ("invite", "Invite"))

    open = MorphState(False)
    value = MorphState("")

    def on_run(self, key: str) -> str:
        return key

    def render(self):
        is_open = bool(self.open)
        menu_id = f"{self.id}-menu"
        rows = [
            button(lab, type="button", role="menuitem", className=self.class_item, **bind(self.run, key=key))
            for key, lab in self.ACTIONS
        ]
        menu_attrs = {
            "id": menu_id,
            "className": self.class_menu,
            "role": "menu",
            "aria_label": "Create",
        }
        if not is_open:
            menu_attrs["hidden"] = True
        menu = div(*rows, **menu_attrs)
        scrim = (
            button(
                span("Close", className=self.class_sr),
                type="button",
                className=self.class_scrim,
                aria_label="Close menu",
                data_channel_on="click keydown.escape",
                **bind(self.toggle),
            )
            if is_open else span("", className=self.class_sr)
        )
        return self.kit_shell(
            scrim,
            menu,
            button(
                "+" if not is_open else "×",
                type="button",
                id=f"{self.id}-trigger",
                className=self.class_fab,
                aria_haspopup="menu",
                aria_expanded="true" if is_open else "false",
                aria_controls=menu_id,
                aria_label="Create",
                **bind(self.toggle),
            ),
            chrome=(
                span("Make", className=self.class_kicker),
                h2("A new thing", className=self.class_title),
                p("The round button is the verb. Opening is public.", className=self.class_lede),
            ),
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
            data_value=str(self.value or ""),
        )

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def run(self, key: str = ""):
        keys = {k for k, _ in self.ACTIONS}
        if key in keys:
            self.value = key
        self.open = False
        return update_with(self, extra_ops=[notify(self.on_run(str(self.value)))])
