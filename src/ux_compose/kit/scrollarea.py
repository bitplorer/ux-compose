"""Drop-in scroll area — labelled overflow region, named jump.

Host seam: override ``BODY``. Jumping is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``which`` (top / mid / end). Caps: none.
A11y: region ``tabindex=0`` ``aria-label``; jump radiogroup.
Not a raw overflow atom — this is a composite card.
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


class ScrollArea(Component):
    """A tall note in a short window. The jump is a name."""

    id = "scrollarea"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_port = "max-h-32 overflow-y-auto rounded-2xl border border-stone-200 bg-stone-50 p-4 text-sm leading-relaxed"

    MARKS = (("top", "Top"), ("mid", "Middle"), ("end", "End"))
    BODY = (
        "The linen is cut to the shoulder. The oak is oiled, then rested. "
        "The wool is folded on the winter list. Nothing is due tonight. "
        "Caps stay off chrome. A named jump is not a quantity."
    )
    which = MorphState("top")

    def render(self):
        which = str(self.which or "top")
        chips = [
            button(
                lab,
                type="button",
                role="radio",
                aria_checked="true" if key == which else "false",
                className="rounded-full px-3 py-2 text-xs " + ("bg-stone-900 text-stone-50" if key == which else "bg-stone-100"),
                **bind(self.jump, key=key),
            )
            for key, lab in self.MARKS
        ]
        return div(
            span("Read", className=self.class_kicker),
            h2("The long note", className=self.class_title),
            p("A named jump. The pane is labelled.", className=self.class_lede),
            div(*chips, className="flex gap-2", role="radiogroup", aria_label="Jump"),
            div(
                p(self.BODY, id=f"{self.id}-p-{which}"),
                className=self.class_port,
                tabindex="0",
                aria_label="Note",
            ),
            id=self.id,
            className=self.class_card,
            data_which=which,
        )

    @action(caps=())
    def jump(self, key: str = ""):
        keys = {k for k, _ in self.MARKS}
        self.which = key if key in keys else "top"
        return update_with(self, extra_ops=[notify(str(self.which))])
