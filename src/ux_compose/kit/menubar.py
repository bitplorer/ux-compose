"""Drop-in menubar — horizontal APG menubar with named submenus.

Host seam: override ``MENUS``. Opening a menu and choosing are public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open`` (submenu key or ""), ``value`` (last command).
Caps: none. A11y (APG Menubar): ``role=menubar`` labelled; top items
``role=menuitem`` ``aria-haspopup=true`` ``aria-expanded`` ``aria-controls``
the submenu id ``{id}-m-{key}``. Submenus stay in the tree with ``hidden``
when closed (honest APG — not omitted). Submenu ``role=menu`` / ``menuitem``.
Escape on scrim. Not Navbar (landmark links) and not NavMenu (one disclosure).
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


class Menubar(Component):
    """Desk chrome. Submenus are presence. The last command is a name.

    ``MENUS`` is ``(key, label, ((item_key, item_label), …))``.
    """

    id = "menubar"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_bar = "relative z-20 flex flex-wrap gap-1 rounded-2xl bg-stone-100 p-1"
    class_top = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3 text-sm font-medium text-stone-700 hover:bg-white"
    )
    class_top_on = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-white px-3 text-sm font-medium text-stone-900 shadow-sm"
    )
    class_menu = (
        "absolute left-1 top-[calc(100%+0.35rem)] z-30 flex min-w-44 flex-col "
        "rounded-2xl border border-stone-200 bg-white p-1.5 shadow-lg"
    )
    class_item = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3.5 text-left text-sm hover:bg-stone-100"
    )
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"
    class_wrap = "relative z-20"

    MENUS = (
        (
            "file",
            "File",
            (("new", "New desk"), ("open", "Open"), ("save", "Save")),
        ),
        (
            "edit",
            "Edit",
            (("undo", "Undo"), ("redo", "Redo")),
        ),
        (
            "view",
            "View",
            (("preview", "Preview"), ("grid", "Grid")),
        ),
    )

    open = MorphState("")
    value = MorphState("")

    def _menus(self):
        return tuple(self.MENUS)

    def render(self):
        opened = str(self.open or "")
        val = str(self.value or "")
        tops = []
        panels = []
        for key, lab, items in self._menus():
            on = key == opened
            menu_id = f"{self.id}-m-{key}"
            tops.append(
                button(
                    lab,
                    type="button",
                    id=f"{self.id}-{key}",
                    role="menuitem",
                    aria_haspopup="true",
                    aria_expanded="true" if on else "false",
                    aria_controls=menu_id,
                    className=self.class_top_on if on else self.class_top,
                    **bind(self.open_menu, key=key),
                )
            )
            rows = [
                button(
                    item_lab,
                    type="button",
                    role="menuitem",
                    className=self.class_item,
                    **bind(self.choose, menu=key, item=item_key),
                )
                for item_key, item_lab in items
            ]
            menu_attrs = {
                "id": menu_id,
                "className": self.class_menu,
                "role": "menu",
                "aria_label": lab,
            }
            if not on:
                menu_attrs["hidden"] = True
            panels.append(div(*rows, **menu_attrs))
        scrim = (
            button(
                span("Close menu", className=self.class_sr),
                type="button",
                className=self.class_scrim,
                aria_label="Close menu",
                data_channel_on="click keydown.escape",
                **bind(self.close),
            )
            if opened
            else span("", className=self.class_sr)
        )
        chosen = val or "none yet"
        return div(
            span("Desk", className=self.class_kicker),
            h2("The bar", className=self.class_title),
            p(f"Last command · {chosen}. Opening a menu is public.", className=self.class_lede),
            scrim,
            div(
                div(*tops, className=self.class_bar, role="menubar", aria_label="Desk"),
                *panels,
                className=self.class_wrap,
            ),
            id=self.id,
            className=self.class_card,
            data_open=opened,
            data_value=val,
        )

    @action(caps=())
    def open_menu(self, key: str = ""):
        keys = {row[0] for row in self._menus()}
        if key not in keys:
            self.open = ""
        elif str(self.open or "") == key:
            self.open = ""
        else:
            self.open = key
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = ""
        return update_with(self)

    @action(caps=())
    def choose(self, menu: str = "", item: str = ""):
        for key, _lab, items in self._menus():
            if key == menu:
                allowed = {k for k, _ in items}
                if item in allowed:
                    self.value = item
                break
        self.open = ""
        return update_with(self, extra_ops=[notify(str(self.value or "none"))])
