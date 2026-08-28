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


class Presence(Component):
    """here / away / focus. Self is MorphState. Peer list is RefState.

    Counts of peers are derived, never MorphState(int). Typing belongs on chat.
    """

    id = "presence"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-5 "
        "overflow-x-hidden rounded-[1.75rem] border border-stone-200/90 bg-white p-6 text-stone-900 "
        "shadow-[0_1px_0_rgba(22,21,19,0.04),0_24px_48px_-28px_rgba(22,21,19,0.4)] "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-xs font-medium uppercase tracking-[0.2em] text-stone-500 "
        "dark:text-stone-400"
    )
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_me = (
        "flex items-center gap-4 rounded-2xl bg-stone-900 px-5 py-5 text-stone-50 "
        "dark:bg-stone-100 dark:text-stone-900"
    )
    class_avatar = (
        "relative flex h-14 w-14 items-center justify-center rounded-full "
        "bg-amber-200 font-serif text-xl font-semibold text-stone-900 "
        "dark:bg-amber-800 dark:text-amber-50"
    )
    class_ring_here = (
        "absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full border-2 "
        "border-stone-900 bg-emerald-400 dark:border-stone-100"
    )
    class_ring_away = (
        "absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full border-2 "
        "border-stone-900 bg-stone-400 dark:border-stone-100"
    )
    class_ring_focus = (
        "absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full border-2 "
        "border-stone-900 bg-amber-400 dark:border-stone-100"
    )
    class_me_name = "m-0 font-serif text-2xl font-medium tracking-tight"
    class_me_state = "m-0 text-sm text-stone-300 dark:text-stone-600"
    class_stack = "flex items-center"
    class_peer = (
        "relative -ml-2 flex h-11 w-11 items-center justify-center rounded-full "
        "border-2 border-white bg-stone-200 font-serif text-sm font-semibold "
        "text-stone-800 first:ml-0 dark:border-stone-950 dark:bg-stone-800 "
        "dark:text-stone-100"
    )
    class_peer_meta = "m-0 text-sm text-stone-600 dark:text-stone-400"
    class_seg = (
        "flex min-w-0 flex-wrap gap-1 rounded-full bg-stone-100 p-1 "
        "dark:bg-stone-900"
    )
    class_chip = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-transparent px-4 text-sm font-medium text-stone-500 "
        "hover:text-stone-900 focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:text-stone-400 dark:hover:text-stone-50"
    )
    class_chip_on = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-white px-4 text-sm font-medium text-stone-900 shadow-sm "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-800 dark:text-stone-50"
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
        for name, st in self._peers():
            avatars.append(
                span(
                    name[:1],
                    className=self.class_peer,
                    title=f"{name} · {st}",
                    id=f"{self.id}-peer-{name.lower()}",
                )
            )
        n = len(self._peers())
        return div(
            span("Floor", className=self.class_kicker),
            h2("Who is at the bench", className=self.class_title),
            p("Self is a name. Peers stay silent. Counts are derived.", className=self.class_lede),
            div(
                div(
                    span("You", className=self.class_sr),
                    span("Y", className="font-serif text-xl font-semibold"),
                    span("", className=self._ring(me), aria_hidden="true"),
                    className=self.class_avatar,
                    id=f"{self.id}-me",
                ),
                div(
                    p("You", className=self.class_me_name),
                    p(label, className=self.class_me_state),
                ),
                className=self.class_me,
            ),
            div(*segs, className=self.class_seg, role="group", aria_label="Your status"),
            div(
                div(*avatars, className=self.class_stack, aria_label="Peers"),
                p(f"{n} others on the floor", className=self.class_peer_meta),
                className="flex items-center gap-3",
            ),
            id=self.id,
            className=self.class_card,
            data_self=me,
        )

    @action(caps=())
    def set(self, key: str = "here"):
        keys = {row[0] for row in self._states()}
        self.self_state = key if key in keys else "here"
        return update_with(self, extra_ops=[notify(self.on_set(str(self.self_state)))])
