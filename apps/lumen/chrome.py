"""Lumen chrome — product shell. Isolation Law: no ux_channel import."""

from __future__ import annotations

from typing import Any

from ux_compose import a, div, footer, header, nav, p, span

from .theme import KICKER, LEDE, ROOM, SHELL, TITLE, WRAP

ROOMS = (
    ("/", "Hall", "hall"),
    ("/folio", "Folio", "folio"),
    ("/chase", "Chase", "chase"),
    ("/stone", "Stone", "stone"),
    ("/gate", "Gate", "gate"),
)

ROOM_TILES = (
    ("/", "Hall", "Who is here. The rooms. The numbers."),
    ("/folio", "Folio", "Slides, hearts, the table, the names."),
    ("/chase", "Chase", "Stars, lanes, the pour, the wait."),
    ("/stone", "Stone", "Steps, plans, the day, the ask."),
    ("/gate", "Gate", "Login and the six digits."),
)


def top_nav(*, room: str = "hall"):
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
                        "bg-[#c4a574] font-medium text-[#1c1915]"
                        if on
                        else "text-[#c8c2b8] hover:bg-white/5"
                    )
                ),
                **({"aria_current": "page"} if on else {}),
            )
        )
    return header(
        a(
            "Lumen",
            span(" · the press", className="text-[#7a746c]"),
            href="/",
            className="font-serif text-lg font-semibold tracking-tight text-[#f4f0e8]",
        ),
        nav(*links, className="flex min-w-0 flex-wrap items-center gap-1", aria_label="Rooms"),
        className=(
            "sticky top-0 z-30 flex min-w-0 items-center justify-between gap-3 "
            "border-b border-white/[0.06] bg-[#12110f]/90 px-4 py-3 backdrop-blur"
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
            span(lede, className="mt-1 block text-[0.85rem] leading-relaxed text-[#9a9388]"),
            href=href,
            className=ROOM,
        )
        for href, label, lede in ROOM_TILES
    ]
    return div(*tiles, className="grid grid-cols-1 gap-3 sm:grid-cols-2")


def foot():
    return footer(
        p(
            "Lumen · Clock A · Channel · kit seams · no app JavaScript",
            className="m-0 text-[0.68rem] uppercase tracking-[0.18em] text-[#6e685f]",
        ),
        className="py-6",
    )


def wrap(*kids: Any, room: str = "hall"):
    return div(
        top_nav(room=room),
        div(*kids, foot(), className=WRAP),
        className=SHELL,
    )
