"""Drop-in navbar — primary landmark with a mobile menu MorphState.

Host seam: render slots OR subclass.
Accepted: ``links`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``, ``active``. Caps: none. A11y (APG Navigation):
``nav`` ``aria-label``, hamburger ``aria-expanded`` ``aria-controls``,
``aria-current=page`` on the active link. Desktop links and the mobile
menu are two trees — never reuse one VDOM list.
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
    a,
    button,
    div,
    nav,
    span,
)


class Navbar(Component):
    """Site chrome. Active key is MorphState. Mobile drawer is presence."""

    id = "navbar"
    _SEAMS = {'links': 'LINKS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] flex-col "
        "overflow-hidden rounded-3xl border border-stone-200 bg-white text-stone-900 shadow-sm"
    )
    class_bar = "flex items-center justify-between gap-3 px-4 py-3"
    class_brand = "text-sm font-semibold tracking-tight"
    class_links = "hidden items-center gap-1 sm:flex"
    class_link = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border-0 "
        "bg-transparent px-3 text-sm text-stone-600 hover:bg-stone-100"
    )
    class_link_on = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border-0 "
        "bg-stone-900 px-3 text-sm font-medium text-stone-50"
    )
    class_burger = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-200 bg-white text-sm sm:hidden"
    )
    class_panel = "flex flex-col gap-1 border-t border-stone-100 px-3 py-3 sm:hidden"
    class_sr = "sr-only"

    LINKS = (
        ("desk", "Desk", "/desk"),
        ("catalog", "Catalog", "/catalog"),
        ("billing", "Billing", "/billing"),
    )

    open = MorphState(False)
    active = MorphState("desk")

    def _links(self):
        return tuple(self.LINKS)

    def _link_nodes(self, cur: str):
        nodes = []
        for key, lab, href in self._links():
            on = key == cur
            nodes.append(
                a(
                    lab,
                    href=href,
                    className=self.class_link_on if on else self.class_link,
                    **({"aria_current": "page"} if on else {}),
                    **bind(self.select, key=key),
                )
            )
        return nodes

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        cur = str(self.active or self._links()[0][0])
        is_open = bool(self.open)
        panel_id = f"{self.id}-menu"
        panel = (
            div(*self._link_nodes(cur), id=panel_id, className=self.class_panel, role="menu")
            if is_open
            else span("", id=panel_id, className=self.class_sr)
        )
        return kit_shell(self,
            nav(
                span("Lumen", className=self.class_brand),
                div(*self._link_nodes(cur), className=self.class_links),
                button(
                    "Menu" if not is_open else "Close",
                    type="button",
                    className=self.class_burger,
                    aria_expanded="true" if is_open else "false",
                    aria_controls=panel_id,
                    **bind(self.toggle),
                ),
                className=self.class_bar,
                aria_label="Primary",
            ),
            panel,
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
            data_active=cur,
        )

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def select(self, key: str = ""):
        keys = {row[0] for row in self._links()}
        self.active = key if key in keys else self._links()[0][0]
        self.open = False
        return update_with(self, extra_ops=[notify(str(self.active))])
