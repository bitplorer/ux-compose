"""Drop-in presence — self named, peers silent.

Host seam: override ``PEERS`` and ``on_set(key)``. Status is public.
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
    p,
    span,
)


_WASH = (
    "bg-gradient-to-br from-[#e8dcc8] to-[#c9b89a]",
    "bg-gradient-to-br from-[#c4a574] to-[#8b6914]",
    "bg-gradient-to-br from-[#d4c4b0] to-[#9a8470]",
    "bg-gradient-to-br from-[#c9a882] to-[#a67c52]",
)


class Presence(Component):
    """here / away / focus. Self is MorphState. Peer list is RefState.

    Counts of peers are derived, never MorphState(int). Typing belongs on chat.
    """

    id = "presence"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-6 "
        "overflow-x-hidden rounded-[1.85rem] border border-stone-900/[0.07] bg-[#fdfcf8] p-7 text-stone-900 "
        "shadow-[0_0_0_1px_rgba(22,21,19,0.03),0_1px_2px_rgba(22,21,19,0.04),0_28px_56px_-24px_rgba(22,21,19,0.2)] "
        "dark:border-white/10 dark:bg-[#141311] dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-[0.6875rem] font-medium uppercase tracking-[0.22em] text-stone-400 "
        "dark:text-stone-500"
    )
    class_title = (
        "m-0 font-serif text-[1.85rem] font-semibold leading-[1.12] tracking-[-0.03em]"
    )
    class_lede = (
        "m-0 max-w-[36ch] text-[0.9375rem] leading-relaxed text-stone-500 "
        "dark:text-stone-400"
    )
    class_me = (
        "flex items-start gap-3.5 rounded-[1.2rem] bg-white/50 px-4 py-4 "
        "dark:bg-white/[0.04]"
    )
    class_avatar = (
        "relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full "
        "bg-gradient-to-br from-[#e8dcc8] to-[#c9b89a] font-serif text-xl font-light "
        "text-stone-900 ring-2 ring-[#fdfcf8] dark:ring-[#141311]"
    )
    class_ring_here = (
        "absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full border-2 "
        "border-[#fdfcf8] bg-emerald-500 dark:border-[#141311]"
    )
    class_ring_away = (
        "absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full border-2 "
        "border-[#fdfcf8] bg-stone-400 dark:border-[#141311]"
    )
    class_ring_focus = (
        "absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full border-2 "
        "border-[#fdfcf8] bg-amber-500 dark:border-[#141311]"
    )
    class_me_name = (
        "m-0 font-serif text-[1.35rem] font-light tracking-[-0.02em] "
        "text-stone-800 dark:text-stone-100"
    )
    class_me_state = "m-0 text-[0.82rem] text-stone-500 dark:text-stone-400"
    class_stack = "flex items-center"
    class_peer = (
        "relative -ml-2.5 flex h-11 w-11 items-center justify-center rounded-full "
        "font-serif text-sm font-light text-stone-900 ring-2 ring-[#fdfcf8] "
        "first:ml-0 dark:ring-[#141311]"
    )
    class_peer_meta = "m-0 ml-3 text-[0.8rem] text-stone-400"
    class_roster = (
        "flex flex-col divide-y divide-stone-900/[0.06] dark:divide-white/10"
    )
    class_row = "flex items-center gap-3 py-2.5"
    class_row_av = (
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full "
        "font-serif text-[0.78rem] font-light text-stone-900"
    )
    class_row_name = (
        "font-serif text-[1.02rem] font-light text-stone-800 dark:text-stone-100"
    )
    class_row_st = "ml-auto text-[0.72rem] text-stone-400"
    class_seg = (
        "flex min-w-0 flex-wrap gap-1.5 rounded-full bg-stone-900/[0.05] p-1 "
        "dark:bg-white/5"
    )
    class_chip = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-transparent px-4 text-[0.8rem] font-medium text-stone-500 "
        "transition hover:text-stone-900 focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:text-stone-400 dark:hover:text-stone-50"
    )
    class_chip_on = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-stone-900 px-4 text-[0.8rem] font-medium text-stone-50 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-100 dark:text-stone-900"
    )
    class_sr = "sr-only"

    STATES = (
        ("here", "Here"),
        ("away", "Away"),
        ("focus", "Focus"),
    )
    PEERS = (
        ("Noor", "here"),
        ("Atelier", "away"),
        ("House", "focus"),
    )
    _FACE = {
        "here": "The bench is yours.",
        "away": "Step back. The others hold it.",
        "focus": "Do not knock. The grain is going on.",
    }

    self_state = MorphState("here")
    peers = RefState(PEERS)
    stamp = MorphState("idle")

    def on_set(self, key: str) -> str:
        return key

    def _states(self):
        return tuple(self.STATES)

    def _peers(self):
        return tuple(self.peers or self.PEERS)

    def _ring(self, key: str):
        return {
            "here": self.class_ring_here,
            "away": self.class_ring_away,
            "focus": self.class_ring_focus,
        }.get(key, self.class_ring_away)

    def render(self):
        me = str(self.self_state or "here")
        states = self._states()
        keys = {row[0] for row in states}
        if me not in keys:
            me = "here"
        label = next((lab for k, lab in states if k == me), me)
        line = self._FACE.get(me, "")
        segs = [
            button(
                lab,
                type="button",
                className=self.class_chip_on if key == me else self.class_chip,
                aria_pressed="true" if key == me else "false",
                **bind(self.set, key=key),
            )
            for key, lab in states
        ]
        avatars = []
        rows = []
        for i, (name, st) in enumerate(self._peers()):
            wash = _WASH[(i + 1) % 4]
            avatars.append(
                span(
                    name[:1],
                    className=f"{self.class_peer} {wash}",
                    title=f"{name} · {st}",
                    id=f"{self.id}-peer-{name.lower()}",
                )
            )
            st_lab = next((lab for k, lab in states if k == st), st)
            rows.append(
                div(
                    span(name[:1], className=f"{self.class_row_av} {wash}"),
                    span(name, className=self.class_row_name),
                    span(st_lab, className=self.class_row_st),
                    className=self.class_row,
                )
            )
        n = len(self._peers())
        return div(
            span("Floor", className=self.class_kicker),
            h2("Who is at the bench", className=self.class_title),
            p(
                "Self is a name. Peers stay silent. Counts are derived.",
                className=self.class_lede,
            ),
            div(
                span("You", className=self.class_sr),
                span("Y", className="font-serif text-xl font-light"),
                span("", className=self._ring(me), aria_hidden="true"),
                className=self.class_avatar,
                id=f"{self.id}-me",
            ),
            div(
                div(*avatars, className=self.class_stack, aria_label="Peers"),
                p(f"{n} others on the floor", className=self.class_peer_meta),
                className="flex items-center",
            ),
            div(
                div(
                    p("You", className=self.class_me_name),
                    p(f"{label}. {line}", className=self.class_me_state),
                ),
                className=self.class_me,
            ),
            div(*segs, className=self.class_seg, role="group", aria_label="Your status"),
            div(*rows, className=self.class_roster),
            id=self.id,
            className=self.class_card,
            data_self=me,
        )

    @action(caps=())
    def set(self, key: str = "here"):
        keys = {row[0] for row in self._states()}
        self.self_state = key if key in keys else "here"
        return update_with(self, extra_ops=[notify(self.on_set(str(self.self_state)))])
