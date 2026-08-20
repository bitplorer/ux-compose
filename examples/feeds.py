"""Feeds — carousel, comments, timeline, empty/error, reorder, activity.

Collections that are not a shelf, table, or kanban. Encoding is unchanged:

    filter / phase / open     MorphState (names, never ints)
    items / order / index     RefState + stamp
    one-shot                  notify
    moderate / delete         Cap

Keyed ids (``id="cmt-1"``, ``id="tl-cut"``) are presence. Morph-then-Play
can later stagger survivors with zero rewrite.

Run:
  PYTHONPATH=src:. python examples/feeds.py
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

from examples._common import act, field, tick, maybe_plan, status


class Carousel(Component):
    """Index is a magnitude — RefState + stamp. Captions are Host data."""

    id = "carousel"
    index = RefState(0)
    stamp = MorphState("idle")
    SLIDES = (
        ("linen", "Work shirt", "Washed flax, open collar."),
        ("oak", "Serving board", "Quarter-sawn, oil finish."),
        ("wool", "Throw", "Undyed merino, blanket stitch."),
        ("clay", "Pourer", "Stoneware lip, unglazed foot."),
    )

    def render(self):
        n = len(self.SLIDES)
        i = int(self.index or 0) % n
        sku, title, body = self.SLIDES[i]
        dots = [
            act(
                "carousel.go",
                str(k + 1),
                kind="primary" if k == i else "ghost",
                n=str(k),
            )
            for k in range(n)
        ]
        kids = (
            header(
                p("Index silent · keyed slide id", className="kicker"),
                h2("Carousel", className="widget-title"),
            ),
            div(
                p(title, className="widget-title"),
                p(body, className="lede"),
                id=f"slide-{sku}",
                className="tab-panel",
            ),
            div(
                act("carousel.prev", "Prev", kind="ghost"),
                act("carousel.next", "Next", kind="primary"),
                className="row-actions",
            ),
            div(*dots, className="seg"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{sku}</div>'

    @action(caps=())
    def next(self):
        self.index = (int(self.index or 0) + 1) % len(self.SLIDES)
        tick(self)
        return update_with(self, maybe_plan("car-next", f"#{self.id}", ms=100))

    @action(caps=())
    def prev(self):
        self.index = (int(self.index or 0) - 1) % len(self.SLIDES)
        tick(self)
        return update_with(self)

    @action(caps=())
    def go(self, n: str = "0"):
        try:
            self.index = int(n) % len(self.SLIDES)
        except ValueError:
            self.index = 0
        tick(self)
        return update_with(self)


class Comments(Component):
    """Thread. Lines in RefState. Reply-to is a named MorphState.

    Posting is public here. A moderated / billed post would take a Cap.
    Hide (moderate) is Cap-protected.
    """

    id = "comments"
    lines = RefState(
        (
            {"id": "c1", "who": "Noor", "text": "Hold the oil finish."},
            {"id": "c2", "who": "Atelier", "text": "Noted — batch on Friday."},
        )
    )
    reply_to = MorphState("")
    stamp = MorphState("idle")
    _seq = RefState(2)

    def render(self):
        rows = list(self.lines or ())
        lis = [
            li(
                span(row["who"], className="bag-line-name"),
                span(row["text"], className="muted"),
                act("comments.reply", "Reply", kind="text", key=row["id"]),
                id=f"cmt-{row['id']}",
                className="bag-line",
            )
            for row in rows
        ] or [li("No notes yet.", className="muted")]
        hint = f"Replying to {self.reply_to}." if self.reply_to else "New note on this piece."
        kids = (
            header(
                p("History silent · reply-to named", className="kicker"),
                h2("Comments", className="widget-title"),
            ),
            ul(*lis, className="bag-lines"),
            p(hint, className="muted"),
            form(
                field("text", "", placeholder="Write a note"),
                button("Post", type="submit", className="btn-primary", **control("comments.post")),
                method="post",
                action="/act/comments.post",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            div(
                act("comments.post", "Post a stand-in", kind="ghost", text="Ship to the house."),
                act("comments.moderate", "Hide last (Cap)", kind="text"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def reply(self, key: str = ""):
        self.reply_to = key
        return update_with(self)

    @action(caps=())
    def post(self, text: str = ""):
        text = (text or "").strip() or "…"
        self._seq = int(self._seq or 0) + 1
        row = {"id": f"c{self._seq}", "who": "You", "text": text}
        if self.reply_to:
            row["text"] = f"↳ {text}"
        self.lines = tuple(self.lines or ()) + (row,)
        self.reply_to = ""
        tick(self)
        return update_with(self, extra_ops=[notify("posted")])

    @action(caps=("comments.moderate",))
    def moderate(self):
        rows = list(self.lines or ())
        if rows:
            rows = rows[:-1]
        self.lines = tuple(rows)
        tick(self)
        return update_with(self, extra_ops=[notify("hidden")])


class Timeline(Component):
    """Ordered events. Filter is a named MorphState. Events in RefState."""

    id = "timeline"
    filt = MorphState("all")
    events = RefState(
        (
            ("cut", "Cut", "Shirt marked."),
            ("make", "Make", "Board oiled."),
            ("keep", "Keep", "Throw folded."),
            ("cut", "Cut", "Second shirt."),
        )
    )
    stamp = MorphState("idle")

    def render(self):
        f = str(self.filt or "all")
        rows = [e for e in (self.events or ()) if f == "all" or e[0] == f]
        lis = [
            li(
                span(kind, className="chip"),
                span(title, className="bag-line-name"),
                span(body, className="muted"),
                id=f"tl-{i}",
                className="bag-line",
            )
            for i, (kind, title, body) in enumerate(rows)
        ] or [li("Nothing in this lane.", className="muted")]
        kids = (
            header(
                p("Named filter · events silent", className="kicker"),
                h2("Timeline", className="widget-title"),
            ),
            div(
                act("timeline.filter", "All", kind="primary" if f == "all" else "ghost", key="all"),
                act("timeline.filter", "Cut", kind="primary" if f == "cut" else "ghost", key="cut"),
                act("timeline.filter", "Make", kind="primary" if f == "make" else "ghost", key="make"),
                className="seg",
            ),
            ul(*lis, className="bag-lines"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def filter(self, key: str = "all"):
        self.filt = key if key in {"all", "cut", "make", "keep"} else "all"
        tick(self)
        return update_with(self)


class EmptyRetry(Component):
    """Empty / loading / error / ready are first-class phases — named MorphState.

    Never ship a blank stage. Retry is public; a billed refetch would take a Cap.
    """

    id = "emptyretry"
    phase = MorphState("empty")
    body = RefState("")
    stamp = MorphState("idle")

    def render(self):
        phase = str(self.phase or "empty")
        if phase == "empty":
            inner = (
                p("The shelf is quiet.", className="lede"),
                act("emptyretry.load", "Load the table", kind="primary"),
            )
        elif phase == "loading":
            inner = (
                p("Fetching the table…", className="muted"),
                div(className="skel"),
                act("emptyretry.fail", "Simulate fail", kind="ghost"),
                act("emptyretry.ready", "Simulate ready", kind="secondary"),
            )
        elif phase == "error":
            inner = (
                p("The table could not be reached.", className="error", role="alert"),
                act("emptyretry.load", "Retry", kind="primary"),
            )
        else:
            inner = (
                p(str(self.body or "Four objects. Linen, oak, wool, clay."), className="lede"),
                status("Ready.", kind="ok"),
                act("emptyretry.reset", "Clear", kind="text"),
            )
        kids = (
            header(
                p("Named phase, never a blank stage", className="kicker"),
                h2("Empty / error / retry", className="widget-title"),
            ),
            *inner,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_phase=phase)
        return f'<div id="{self.id}">{phase}</div>'

    @action(caps=())
    def load(self):
        self.phase = "loading"
        self.body = ""
        tick(self)
        return update_with(self)

    @action(caps=())
    def fail(self):
        self.phase = "error"
        tick(self)
        return update_with(self, extra_ops=[notify("error")])

    @action(caps=())
    def ready(self):
        self.phase = "ready"
        self.body = "Quiet pieces for a working house."
        tick(self)
        return update_with(self)

    @action(caps=())
    def reset(self):
        self.phase = "empty"
        self.body = ""
        tick(self)
        return update_with(self)


class ReorderList(Component):
    """Order is a tuple of ids in RefState. Move is public. Presence ids stay stable."""

    id = "reorder"
    order = RefState(("linen", "oak", "wool", "clay"))
    stamp = MorphState("idle")
    NAMES = {"linen": "Work shirt", "oak": "Serving board", "wool": "Throw", "clay": "Pourer"}

    def render(self):
        rows = list(self.order or ())
        lis = []
        for i, sku in enumerate(rows):
            lis.append(
                li(
                    span(self.NAMES.get(sku, sku), className="bag-line-name"),
                    act("reorder.up", "Up", kind="text", sku=sku) if i else span(""),
                    act("reorder.down", "Down", kind="text", sku=sku)
                    if i < len(rows) - 1
                    else span(""),
                    id=f"ord-{sku}",
                    className="bag-line",
                )
            )
        kids = (
            header(
                p("Stable item ids · order silent", className="kicker"),
                h2("Reorder", className="widget-title"),
            ),
            p("Moving a row is public. Archiving it would take a Cap.", className="lede"),
            ul(*lis, className="bag-lines"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    def _move(self, sku: str, delta: int):
        rows = list(self.order or ())
        if sku not in rows:
            return
        i = rows.index(sku)
        j = max(0, min(len(rows) - 1, i + delta))
        rows.pop(i)
        rows.insert(j, sku)
        self.order = tuple(rows)
        tick(self)

    @action(caps=())
    def up(self, sku: str = ""):
        self._move(sku, -1)
        return update_with(self, extra_ops=[notify("up")])

    @action(caps=())
    def down(self, sku: str = ""):
        self._move(sku, 1)
        return update_with(self, extra_ops=[notify("down")])


class ActivityFeed(Component):
    """Infinite-ish feed. Cursor is an opaque string MorphState. Items RefState."""

    id = "actfeed"
    items = RefState(("Reserved the throw.", "Oiled the oak board."))
    cursor = MorphState("p1")
    has_more = MorphState(True)
    stamp = MorphState("idle")
    REST = ("Minted a Cap for checkout.", "Marked the work shirt.", "Folded the linen.")

    def render(self):
        rows = list(self.items or ())
        lis = [li(x, className="hit", id=f"act-{i}") for i, x in enumerate(rows)]
        more = (
            act("actfeed.more", "Load earlier", kind="primary")
            if self.has_more
            else p("Beginning of the house.", className="muted")
        )
        kids = (
            header(
                p("Opaque cursor · items silent", className="kicker"),
                h2("Activity", className="widget-title"),
            ),
            ul(*lis, className="hit-list"),
            more,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def more(self):
        have = list(self.items or ())
        rest = [x for x in self.REST if x not in have]
        take, rest = rest[:2], rest[2:]
        self.items = tuple(have + take)
        self.has_more = bool(rest)
        self.cursor = "end" if not rest else "p2"
        tick(self)
        return update_with(self, extra_ops=[notify("more")])


def demo() -> None:
    app = App.boot("Feeds", strict_caps=False)
    app.add(Carousel, Comments, Timeline, EmptyRetry, ReorderList, ActivityFeed)
    print("car", app.dispatch("carousel.next"))
    print("cmt", app.dispatch("comments.post", text="held"))
    print("tl", app.dispatch("timeline.filter", key="cut"))
    print("empty", app.dispatch("emptyretry.load"))
    print("ord", app.dispatch("reorder.up", sku="oak"))
    print("feed", app.dispatch("actfeed.more"))
    strict = App.boot("Feeds", strict_caps=True)
    strict.add(Comments)
    try:
        strict.dispatch("comments.moderate")
        print("UNEXPECTED moderate")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
