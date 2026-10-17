"""Comments — Thread. Lines in RefState. Reply-to is a named MorphState.

Ported from the ``feeds`` example module (spec §4); this module is canonical and the example imports it.
"""
from __future__ import annotations

from ux_compose import (
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

from ux_compose.author import act, field, mark_dirty

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
    dirty = MorphState("idle")
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
            ),

            div(
                act("comments.post", "Post a stand-in", kind="ghost", text="Ship to the house."),
                act("comments.moderate", "Hide last (Cap)", kind="text"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def reply(self, key: str = ""):
        self.reply_to = key
        return update_with(self)

    @action(caps=("comments.post",))
    def post(self, text: str = ""):
        text = (text or "").strip() or "…"
        self._seq = int(self._seq or 0) + 1
        row = {"id": f"c{self._seq}", "who": "You", "text": text}
        if self.reply_to:
            row["text"] = f"↳ {text}"
        self.lines = tuple(self.lines or ()) + (row,)
        self.reply_to = ""
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("posted")])

    @action(caps=("comments.moderate",))
    def moderate(self):
        rows = list(self.lines or ())
        if rows:
            rows = rows[:-1]
        self.lines = tuple(rows)
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("hidden")])


__all__ = ["Comments"]
