"""Drop-in user menu — identity chrome, Cap on sign-out.

Host seam: override ``on_sign_out()``. Opening is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``. RefState: ``name``, ``email``. Caps: ``auth.logout``
on ``sign_out``. A11y: ``aria-haspopup=menu``, ``role=menu`` / ``menuitem``.
Escape on scrim.
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


class UserMenu(Component):
    """Avatar trigger + named actions. Sign-out spends identity."""

    id = "usermenu"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_wrap = "relative z-20 max-w-72"
    class_trigger = (
        "flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-2xl "
        "border border-stone-200 bg-stone-50 px-3 text-left text-sm"
    )
    class_mark = (
        "flex h-8 w-8 items-center justify-center rounded-full bg-stone-800 "
        "text-xs font-semibold text-stone-50"
    )
    class_menu = (
        "absolute left-0 right-0 top-[calc(100%+0.35rem)] z-30 flex flex-col "
        "rounded-2xl border border-stone-200 bg-white p-1.5 shadow-lg"
    )
    class_item = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3.5 text-left text-sm hover:bg-stone-100"
    )
    class_danger = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3.5 text-left text-sm text-rose-700 hover:bg-rose-50"
    )
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"

    open = MorphState(False)
    name = RefState("Ada Lovelace")
    email = RefState("ada@atelier.test")

    def on_sign_out(self) -> str:
        return "Signed out"

    def render(self):
        is_open = bool(self.open)
        who = str(self.name or "You")
        initial = (who[:1] or "Y").upper()
        menu = span("", className=self.class_sr)
        if is_open:
            menu = div(
                button("Profile", type="button", role="menuitem", className=self.class_item, **bind(self.close)),
                button("Settings", type="button", role="menuitem", className=self.class_item, **bind(self.close)),
                button(
                    "Sign out",
                    type="button",
                    role="menuitem",
                    className=self.class_danger,
                    **bind(self.sign_out),
                ),
                id=f"{self.id}-menu",
                className=self.class_menu,
                role="menu",
                aria_label=who,
            )
        scrim = (
            button(
                span("Close", className=self.class_sr),
                type="button",
                className=self.class_scrim,
                aria_label="Close menu",
                data_channel_on="click keydown.escape",
                **bind(self.close),
            )
            if is_open else span("", className=self.class_sr)
        )
        return div(
            span("Session", className=self.class_kicker),
            h2("You", className=self.class_title),
            p(str(self.email or ""), className=self.class_lede),
            scrim,
            div(
                button(
                    span(initial, className=self.class_mark, aria_hidden="true"),
                    span(who),
                    type="button",
                    id=f"{self.id}-trigger",
                    className=self.class_trigger,
                    aria_haspopup="menu",
                    aria_expanded="true" if is_open else "false",
                    aria_controls=f"{self.id}-menu",
                    **bind(self.toggle),
                ),
                menu,
                className=self.class_wrap,
            ),
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
        )

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=("auth.logout",))
    def sign_out(self):
        self.open = False
        return update_with(self, extra_ops=[notify(self.on_sign_out())])
