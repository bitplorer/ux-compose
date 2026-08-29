"""Floor chrome — product shell. Isolation Law: no ux_channel import."""

from __future__ import annotations

from typing import Any

from ux_compose import a, div, footer, header, nav, p, span

from .host import HOUSE
from .theme import KICKER, LEDE, LOOSE, ROOM, SHELL, TITLE, WRAP

ROOMS = (
    ("/", "Desk", "desk"),
    ("/shelf", "Shelf", "shelf"),
    ("/bench", "Bench", "bench"),
    ("/visit", "Visit", "visit"),
    ("/door", "Door", "door"),
)

ROOM_TILES = (
    ("/", "Desk", "The books, the ledger, who is here."),
    ("/shelf", "Shelf", "Slides, hearts, the table, the names."),
    ("/bench", "Bench", "Stars, lanes, the pour, the wait."),
    ("/visit", "Visit", "Steps, plans, the day, the ask."),
    ("/door", "Door", "Login and the six digits."),
)


def top_nav(*, room: str = "desk"):
    links = []
    for href, label, key in ROOMS:
        on = key == room
        links.append(
            a(
                label,
                href=href,
                className=(
                    "inline-flex min-h-11 items-center rounded-full px-3.5 text-sm "
                    + (
                        "bg-stone-900 font-medium text-stone-50"
                        if on
                        else "text-stone-600 hover:bg-white"
                    )
                ),
                **({"aria_current": "page"} if on else {}),
            )
        )
    return header(
        a(
            "Floor",
            span(" · the house", className="text-stone-400"),
            href="/",
            className="font-serif text-lg font-semibold tracking-tight",
        ),
        nav(*links, className="flex min-w-0 flex-wrap items-center gap-1", aria_label="Rooms"),
        className=(
            "sticky top-0 z-30 flex min-w-0 items-center justify-between gap-3 "
            "border-b border-stone-900/[0.06] bg-[#f3efe6]/90 px-4 py-3 backdrop-blur"
        ),
    )


def hero(*, kicker: str, title: str, lede: str):
    return div(
        span(kicker, className=KICKER),
        p(title, className=TITLE),
        p(lede, className=LEDE),
        className="flex flex-col gap-2",
    )


def rooms():
    tiles = [
        a(
            span(label, className="font-serif text-[1.45rem] font-light tracking-[-0.02em]"),
            span(lede, className="mt-1 block text-[0.85rem] leading-relaxed text-stone-500"),
            href=href,
            className=ROOM,
        )
        for href, label, lede in ROOM_TILES
    ]
    return div(*tiles, className="grid grid-cols-1 gap-3 sm:grid-cols-2")


def ledger():
    rows = list(HOUSE.ledger)[-6:]
    if not rows:
        body = p("The books are quiet.", className=LEDE)
    else:
        items = [
            p(
                f"{row.get('kind', '')}  ·  "
                + " ".join(f"{k}={v}" for k, v in row.items() if k != "kind"),
                className="m-0 font-mono text-[0.75rem] text-stone-500",
            )
            for row in reversed(rows)
        ]
        body = div(*items, className="flex flex-col gap-1.5")
    return div(
        span("Host ledger", className=KICKER),
        p("Writes land here. The kit only morphs a name.", className=LEDE),
        body,
        className=(
            "flex flex-col gap-3 rounded-[1.4rem] border border-stone-900/[0.07] "
            "bg-white/50 px-5 py-5"
        ),
        id="floor-ledger",
    )


def foot():
    return footer(
        p(
            "Floor · kit seams · Host books · polish stays on the copy",
            className="m-0 text-[0.68rem] uppercase tracking-[0.18em] text-stone-400",
        ),
        className="py-6",
    )


def wrap(*kids: Any, room: str = "desk"):
    return div(
        top_nav(room=room),
        div(*kids, foot(), className=WRAP),
        className=SHELL,
    )


def stack(*kids: Any):
    return div(*kids, className=LOOSE)
