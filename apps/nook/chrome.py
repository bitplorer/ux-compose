"""Nook chrome — product shell. Isolation Law: no ux_channel import."""

from __future__ import annotations

from typing import Any

from ux_compose import a, div, footer, header, nav, p, span

from .theme import KICKER, LEDE, SHELL, TITLE, WRAP

ROOMS = (
    ("/", "Desk", "desk"),
    ("/house", "House", "house"),
    ("/visit", "Visit", "visit"),
    ("/enter", "Enter", "enter"),
)


def html_of(tree: Any) -> str:
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    try:
        from ux_compose.helpers import _serialize_tree

        return _serialize_tree(tree)
    except Exception:
        return str(tree)


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
                        "bg-stone-800 font-medium text-stone-50"
                        if on
                        else "text-stone-600 hover:bg-white"
                    )
                ),
                **({"aria_current": "page"} if on else {}),
            )
        )
    return header(
        a("Nook", href="/", className="font-serif text-lg font-semibold tracking-tight"),
        nav(*links, className="flex min-w-0 flex-wrap items-center gap-1", aria_label="Rooms"),
        className=(
            "sticky top-0 z-30 flex min-w-0 items-center justify-between gap-3 "
            "border-b border-stone-200/80 bg-[#f3efe6]/90 px-3.5 py-3 backdrop-blur"
        ),
    )


def hero(*, kicker: str, title: str, lede: str):
    return div(
        span(kicker, className=KICKER),
        p(title, className=TITLE),
        p(lede, className=LEDE),
        className="flex flex-col gap-1.5 px-0.5 pb-1",
    )


def foot():
    return footer(
        p(
            "Nook · ux-compose kit · named keys · Caps off chrome",
            className="m-0 text-xs uppercase tracking-widest text-stone-400",
        ),
        className="px-0.5 py-6",
    )


def wrap(*kids: Any, room: str = "desk"):
    return div(
        top_nav(room=room),
        div(*kids, foot(), className=WRAP),
        className=SHELL,
    )
