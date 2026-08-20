"""Systems — chat, notification center, tree, skeleton, consent, theme, stepper, rating, chips, inline edit.

These are the remaining 99% cases: each is still Morph/Ref + @action + update_with.
No new framework verbs.

Run:
  PYTHONPATH=src:. python examples/systems.py
"""
from __future__ import annotations

from ux_compose import (
    HAS_DOM,
    App,
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    header,
    ul,
    li,
    span,
    form,
    button,
    control,
)

from examples._common import act, field, tick


class Chat(Component):
    id = "chat"
    lines = RefState(("Atelier: the table is set.",))
    typing = MorphState(False)
    stamp = MorphState("idle")

    def render(self):
        lis = [li(x, className="hit") for x in (self.lines or ())]
        kids = (
            header(
                p("Typing is MorphState", className="kicker"),
                h2("Chat", className="widget-title"),
            ),
            ul(*lis, className="hit-list"),
            p("House is typing…", className="muted") if self.typing else p(""),
            form(
                field("text", "", placeholder="Write a line"),
                button("Send", type="submit", className="btn-primary", **control("chat.send")),
                method="post",
                action="/act/chat.send",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            div(
                act("chat.peer_type", "Peer types", kind="ghost"),
                act("chat.peer_done", "Peer sends", kind="secondary"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def send(self, text: str = ""):
        text = (text or "").strip() or "…"
        self.lines = tuple(self.lines or ()) + (f"You: {text}",)
        self.typing = False
        tick(self)
        return update_with(self, extra_ops=[notify("sent")])

    @action(caps=())
    def peer_type(self):
        self.typing = True
        return update_with(self)

    @action(caps=())
    def peer_done(self):
        self.typing = False
        self.lines = tuple(self.lines or ()) + ("Atelier: held until you place.",)
        tick(self)
        return update_with(self)


class NotifyCenter(Component):
    id = "inbox"
    open = MorphState(False)
    unread = RefState(3)
    items = RefState(("Order reserved.", "Throw restocked.", "Cap minted for checkout."))
    stamp = MorphState("idle")

    def render(self):
        n = int(self.unread or 0)
        panel = (
            ul(*[li(x) for x in (self.items or ())], className="hit-list")
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Badge is derived from RefState", className="kicker"),
                h2("Notifications", className="widget-title"),
            ),
            div(
                act(
                    "inbox.toggle",
                    f"Inbox · {n}",
                    kind="primary" if n else "ghost",
                ),
                act("inbox.mark_read", "Mark read", kind="text"),
                className="row-actions",
            ),
            panel,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_unread=str(n))
        return f'<div id="{self.id}">{n}</div>'

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def mark_read(self):
        self.unread = 0
        tick(self)
        return update_with(self)


class Tree(Component):
    id = "tree"
    expanded = MorphState(("house",))
    selected = MorphState("linen")
    NODES = (
        ("house", None, "House"),
        ("linen", "house", "Linen"),
        ("oak", "house", "Oak"),
        ("wool", "house", "Wool"),
    )

    def render(self):
        opened = set(self.expanded or ())
        items = []
        for key, parent, label in self.NODES:
            if parent and parent not in opened:
                continue
            items.append(
                li(
                    span(label, className="bag-line-name"),
                    act("tree.toggle", "Open" if key not in opened else "Close", kind="text", id=key)
                    if parent is None
                    else act("tree.select", "Select", kind="text", id=key),
                    id=f"node-{key}",
                    className="bag-line" + (" is-on" if self.selected == key else ""),
                )
            )
        kids = (
            header(
                p("Expanded ids MorphState", className="kicker"),
                h2("Tree", className="widget-title"),
            ),
            ul(*items, className="bag-lines"),
            p(f"Selected {self.selected}", className="muted"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def toggle(self, id: str = ""):
        cur = set(self.expanded or ())
        if id in cur:
            cur.remove(id)
        elif id:
            cur.add(id)
        self.expanded = tuple(sorted(cur))
        return update_with(self)

    @action(caps=())
    def select(self, id: str = ""):
        self.selected = id
        return update_with(self)


class Skeleton(Component):
    id = "skeleton"
    loading = MorphState(True)
    body = RefState("")

    def render(self):
        if self.loading:
            kids = (
                header(h2("Skeleton")),
                p("Loading the table…", className="muted"),
                div(className="skel"),
                act("skeleton.arrive", "Data arrives", kind="primary"),
            )
        else:
            kids = (
                header(h2("Skeleton")),
                p(str(self.body or "Four objects. Linen, oak, wool, clay."), className="lede"),
                act("skeleton.reload", "Reload", kind="ghost"),
            )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def arrive(self):
        self.loading = False
        self.body = "Quiet pieces for a working house."
        return update_with(self)

    @action(caps=())
    def reload(self):
        self.loading = True
        self.body = ""
        return update_with(self)


class Consent(Component):
    id = "consent"
    choice = MorphState("ask")

    def render(self):
        if self.choice != "ask":
            kids = (
                header(h2("Consent")),
                p(f"Recorded as {self.choice}.", className="lede"),
                act("consent.reset", "Ask again", kind="text"),
            )
        else:
            kids = (
                header(
                    p("Cookie / consent gate", className="kicker"),
                    h2("Consent", className="widget-title"),
                ),
                p("Motion recipes stay off until you allow them.", className="lede"),
                div(
                    act("consent.decide", "Allow", kind="primary", value="allow"),
                    act("consent.decide", "Essential only", kind="ghost", value="essential"),
                    className="row-actions",
                ),
            )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{self.choice}</div>'

    @action(caps=())
    def decide(self, value: str = "allow"):
        self.choice = value
        return update_with(self, extra_ops=[notify(value)])

    @action(caps=())
    def reset(self):
        self.choice = "ask"
        return update_with(self)


class Theme(Component):
    """Paper house is light-only. This still shows a locale/theme MorphState."""

    id = "theme"
    locale = MorphState("en")

    def render(self):
        copy = {
            "en": "Quiet pieces for a working house.",
            "hi": "कामकाजी घर के शांत टुकड़े।",
        }[str(self.locale or "en")]
        kids = (
            header(
                p("Locale MorphState", className="kicker"),
                h2("Locale", className="widget-title"),
            ),
            p(copy, className="lede"),
            div(
                act("theme.set_locale", "English", kind="ghost", locale="en"),
                act("theme.set_locale", "हिंदी", kind="ghost", locale="hi"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{self.locale}</div>'

    @action(caps=())
    def set_locale(self, locale: str = "en"):
        self.locale = locale if locale in {"en", "hi"} else "en"
        return update_with(self)


class Stepper(Component):
    """PDP quantity. Magnitude in RefState. Stamp dirties."""

    id = "stepper"
    qty = RefState(1)
    stamp = MorphState("idle")

    def render(self):
        q = int(self.qty or 1)
        kids = (
            header(
                p("Never MorphState(int) on Channel session", className="kicker"),
                h2("Quantity stepper", className="widget-title"),
            ),
            p(span(str(q), className="num"), span(" on the board", className="muted"), className="counter-face"),
            div(
                act("stepper.dec", "−", kind="ghost"),
                act("stepper.inc", "+", kind="primary"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{q}</div>'

    @action(caps=())
    def inc(self):
        self.qty = min(9, int(self.qty or 1) + 1)
        tick(self)
        return update_with(self)

    @action(caps=())
    def dec(self):
        self.qty = max(1, int(self.qty or 1) - 1)
        tick(self)
        return update_with(self)


class Rating(Component):
    id = "rating"
    stars = MorphState("three")
    MAP = ("one", "two", "three", "four", "five")

    def render(self):
        cur = str(self.stars or "three")
        i = self.MAP.index(cur) + 1 if cur in self.MAP else 3
        kids = (
            header(
                p("Named, not numeric, MorphState", className="kicker"),
                h2("Rating", className="widget-title"),
            ),
            p(f"{i} of 5", className="num"),
            div(
                *[
                    act("rating.set", str(n), kind="primary" if n == i else "ghost", value=self.MAP[n - 1])
                    for n in range(1, 6)
                ],
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{cur}</div>'

    @action(caps=())
    def set(self, value: str = "three"):
        self.stars = value if value in self.MAP else "three"
        return update_with(self)


class Chips(Component):
    id = "chips"
    tags = RefState(("linen", "quiet"))
    stamp = MorphState("idle")

    def render(self):
        chips = [
            li(
                span(t),
                act("chips.remove", "×", kind="text", tag=t),
                className="chip",
                id=f"chip-{t}",
            )
            for t in (self.tags or ())
        ]
        kids = (
            header(
                p("Tag set as RefState", className="kicker"),
                h2("Chips", className="widget-title"),
            ),
            ul(*chips, className="chip-row"),
            div(
                act("chips.add", "Add oak", kind="secondary", tag="oak"),
                act("chips.add", "Add wool", kind="secondary", tag="wool"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def add(self, tag: str = ""):
        if tag and tag not in (self.tags or ()):
            self.tags = tuple(self.tags or ()) + (tag,)
        tick(self)
        return update_with(self)

    @action(caps=())
    def remove(self, tag: str = ""):
        self.tags = tuple(t for t in (self.tags or ()) if t != tag)
        tick(self)
        return update_with(self)


class InlineEdit(Component):
    id = "inline"
    editing = MorphState(False)
    text = RefState("Work shirt")
    stamp = MorphState("idle")

    def render(self):
        if self.editing:
            body = form(
                field("text", str(self.text or "")),
                button("Save", type="submit", className="btn-primary", **control("inline.save")),
                method="post",
                action="/act/inline.save",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ) if HAS_DOM else p("")
        else:
            body = div(
                p(str(self.text or ""), className="lede"),
                act("inline.edit", "Edit", kind="ghost"),
            )
        kids = (
            header(
                p("Pencil / contenteditable stand-in", className="kicker"),
                h2("Inline edit", className="widget-title"),
            ),
            body,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def edit(self):
        self.editing = True
        return update_with(self)

    @action(caps=())
    def save(self, text: str = ""):
        if text:
            self.text = text
        self.editing = False
        tick(self)
        return update_with(self, extra_ops=[notify("saved")])


def demo() -> None:
    app = App.boot("Systems", strict_caps=False)
    app.add(
        Chat, NotifyCenter, Tree, Skeleton, Consent, Theme, Stepper, Rating, Chips, InlineEdit
    )
    print("chat", app.dispatch("chat.send", text="held"))
    print("tree", app.dispatch("tree.select", id="oak"))
    print("step", app.dispatch("stepper.inc"))
    print("rate", app.dispatch("rating.set", value="five"))


if __name__ == "__main__":
    demo()
