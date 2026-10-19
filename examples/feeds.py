"""Feeds — carousel, comments, timeline, empty/error, reorder, activity.

Collections that are not a shelf, table, or kanban. Encoding is unchanged:

    filter / phase / open     MorphState (names, never ints)
    items / order / index     RefState + dirty
    one-shot                  notify
    moderate / delete         Cap

Keyed ids (``id="cmt-1"``, ``id="tl-cut"``) are presence. Morph-then-Play
can later stagger survivors with zero rewrite.

Run:
  PYTHONPATH=src:. python examples/feeds.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.activityfeed import ActivityFeed
from ux_compose.components.carousel import Carousel
from ux_compose.components.comments import Comments
from ux_compose.components.emptyretry import EmptyRetry
from ux_compose.components.reorderlist import ReorderList
from ux_compose.components.timeline import Timeline


def demo() -> None:
    app = App.boot("Feeds")
    app.add(Carousel, Comments, Timeline, EmptyRetry, ReorderList, ActivityFeed)
    print("car", app.dispatch("carousel.next"))
    with app.trust():
        print("cmt", app.dispatch("comments.post", text="held"))
    print("tl", app.dispatch("timeline.choose", key="cut"))
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
