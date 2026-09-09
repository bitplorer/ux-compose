"""Drop-in feed — APG feed of named articles.

Host seam: construct kwargs OR subclass.
Accepted: ``seed``, ``more`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``items``. Caps: none.
A11y (APG Feed): ``role=feed``; each item ``role=article`` labelledby.
Not Chat (composer log) and not Timeline (filtered lanes).
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
    MorphState,
    RefState,
    action,
    bind,
    notify,
    update_with,
    article,
    button,
    div,
    h2,
    h3,
    p,
    span,
)


class Feed(Kit):
    """What the house did. Articles live on RefState."""

    id = "feed"
    _SEAMS = {'seed': 'SEED', 'more': 'MORE'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_item = "rounded-2xl bg-stone-50 px-4 py-3"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border "
        "border-stone-200 bg-white px-4 text-sm"
    )

    SEED = (("cut", "Shirt marked"),)
    MORE = ("Board oiled", "Throw folded", "List sent")

    items = RefState(("Shirt marked",))
    dirty = MorphState("idle")

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        items = tuple(self.items or ())
        posts = []
        for i, title in enumerate(items):
            hid = f"{self.id}-h-{i}"
            posts.append(
                article(
                    h3(title, id=hid, className="m-0 text-sm font-medium"),
                    p("On the winter list.", className=self.class_lede),
                    className=self.class_item,
                    role="article",
                    aria_labelledby=hid,
                )
            )
        return self.kit_shell(
            p(f"{len(items)} note" + ("" if len(items) == 1 else "s") + ".", className=self.class_lede),
            div(*posts, className="flex flex-col gap-2", role="feed", aria_label="Activity"),
            button("Load more", type="button", className=self.class_btn, **bind(self.append)),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("House", className=self.class_kicker),
                h2("Activity", className=self.class_title),
            ),
        )

    @action(caps=())
    def append(self):
        cur = tuple(self.items or ())
        nxt = self.MORE[len(cur) % len(self.MORE)]
        self.items = cur + (nxt,)
        self._mark()
        return update_with(self, extra_ops=[notify("more")])
