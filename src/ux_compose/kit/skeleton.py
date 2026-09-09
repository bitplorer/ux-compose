"""Drop-in skeleton — loading placeholder, busy region.

Host seam: render slots OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``loading``. Caps: none. A11y: ``aria-busy`` on the region;
placeholder bars ``aria-hidden``.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    MorphState,
    action,
    bind,
    update_with,
    button,
    div,
    h2,
    p,
    span,
)


class Skeleton(Component):
    """Pulse bars while the Host fills. Loading is presence, not a quantity."""

    id = "skeleton"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_bar = "h-3 animate-pulse rounded-full bg-stone-200"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium"
    )

    loading = MorphState(True)

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        loading = bool(self.loading)
        body = (
            div(
                div("", className=self.class_bar + " w-2/3"),
                div("", className=self.class_bar + " w-full"),
                div("", className=self.class_bar + " w-5/6"),
                className="flex flex-col gap-3",
                aria_hidden="true",
            )
            if loading
            else p("The catalog arrived. Bars were never content.", className=self.class_lede)
        )
        return kit_shell(self,
            body,
            button(
                "Show content" if loading else "Load again",
                type="button",
                className=self.class_btn,
                **bind(self.toggle),
            ),
            chrome=(
                span("Wait" if loading else "Ready", className=self.class_kicker),
                h2("Loading the desk" if loading else "On the desk", className=self.class_title),
            ),
            id=self.id,
            className=self.class_card,
            aria_busy="true" if loading else "false",
            data_loading="1" if loading else "0",
        )

    @action(caps=())
    def toggle(self):
        self.loading = not bool(self.loading)
        return update_with(self)
