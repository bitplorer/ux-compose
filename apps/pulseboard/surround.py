"""Pulseboard surround — rail, desk, and document wrap. Isolation: no ux_channel."""

from __future__ import annotations

from typing import Any

from ux_compose import a, div, footer, header, main, nav, p, span
from ux_compose.brand import GET_BRAND_ATTR
from ux_compose.helpers import _serialize_tree

from apps.pulseboard.registry import live, theme_key
from apps.pulseboard.theme import KICKER, LEDE, RAIL, SHELL, TITLE, TOP, WRAP


ROOMS = (
    ("/", "Overview", "overview"),
    ("/pipeline", "Pipeline", "pipeline"),
    ("/signals", "Signals", "signals"),
)


def html_of(tree: Any) -> str:
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    return _serialize_tree(tree)


def _unit(sid: str, fallback: str = ""):
    inst = live(sid)
    if inst is None:
        return p(fallback or f"Missing {sid}", className="text-sm text-slate-500")
    render = getattr(inst, "render", None)
    if not callable(render):
        return p(fallback)
    try:
        return render(shell=False)
    except TypeError:
        return render()


def rail(*, room: str = "overview", atelier: bool = False, prefix: str = ""):
    links = []
    for href, label, key in ROOMS:
        dest = (prefix + ("" if href == "/" else href)) if prefix else href
        if not dest:
            dest = prefix or "/"
        on = key == room
        links.append(
            a(
                label,
                href=dest,
                className=(
                    "flex min-h-11 items-center rounded-xl px-3 text-sm "
                    + (
                        "bg-slate-900 font-medium text-white dark:bg-teal-400 dark:text-slate-950"
                        if on
                        else "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/5"
                    )
                ),
                **({"aria_current": "page"} if on else {}),
            )
        )
    return nav(
        a(
            span("Atelier", className="block text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400"),
            span("Pulseboard", className="block font-serif text-xl font-semibold tracking-tight"),
            href=prefix or "/",
            className="mb-4 px-2 no-underline text-inherit",
        ),
        *links,
        *(
            [
                a(
                    "← Atelier of Patterns",
                    href="/",
                    className="mt-4 px-3 text-xs text-slate-500 hover:text-teal-600 dark:hover:text-teal-300",
                )
            ]
            if atelier
            else []
        ),
        p(
            "Kit Stats · Timeline · Rating · Progress · Slider · Empty · Skeleton · Badge · Feed · Theme · Avatar",
            className="mt-auto px-2 text-[11px] leading-relaxed text-slate-400",
        ),
        className=RAIL,
        aria_label="Pulseboard",
    )


def top_bar():
    return header(
        div(
            span("Sunday desk", className=KICKER),
            p("Revenue, paper, and who is on the floor.", className="m-0 text-sm text-slate-500 dark:text-slate-400"),
            className="min-w-0",
        ),
        div(
            _unit("desk_avatar"),
            _unit("desk_theme"),
            className="flex min-w-0 flex-wrap items-center gap-3",
        ),
        className="flex min-w-0 flex-wrap items-end justify-between gap-4",
    )


def hero():
    return div(
        span("Command center", className=KICKER),
        p("Pulseboard", className=TITLE + " text-4xl"),
        p(
            "A live SaaS desk composed from the ownable kit. Magnitudes stay on RefState. "
            "Named lanes are MorphState. Close quarter spends a Cap.",
            className=LEDE + " max-w-2xl",
        ),
        className="flex flex-col gap-2 pb-1",
    )


def overview_main():
    return div(
        hero(),
        _unit("desk_kpis"),
        div(
            _unit("desk_kanban"),
            _unit("desk_timeline"),
            className="grid gap-5 min-[980px]:grid-cols-2",
        ),
        div(
            _unit("desk_rating"),
            _unit("desk_progress"),
            _unit("desk_horizon"),
            className="grid gap-5 min-[860px]:grid-cols-3",
        ),
        div(
            _unit("desk_chips"),
            _unit("desk_empty"),
            className="grid gap-5 min-[860px]:grid-cols-2",
        ),
        div(
            _unit("desk_skeleton"),
            _unit("desk_feed"),
            className="grid gap-5 min-[860px]:grid-cols-2",
        ),
        div(
            _unit("desk_presence"),
            _unit("desk_watch"),
            _unit("desk_close"),
            className="grid gap-5 min-[860px]:grid-cols-3",
        ),
        className="flex min-w-0 flex-col gap-5",
        id="board",
    )


def pipeline_main():
    return div(
        span("Pipeline", className=KICKER),
        p("Move paper without remounting the desk.", className=TITLE),
        p("Three RefState columns. id=deal-{sku} is presence.", className=LEDE),
        _unit("desk_kanban"),
        _unit("desk_chips"),
        _unit("desk_watch"),
        className="flex min-w-0 flex-col gap-5",
        id="board",
    )


def signals_main():
    return div(
        span("Signals", className=KICKER),
        p("What landed since dusk.", className=TITLE),
        p("Timeline lanes are names. Feed articles live on RefState.", className=LEDE),
        div(
            _unit("desk_timeline"),
            _unit("desk_feed"),
            className="grid gap-5 min-[980px]:grid-cols-2",
        ),
        div(
            _unit("desk_skeleton"),
            _unit("desk_presence"),
            className="grid gap-5 min-[860px]:grid-cols-2",
        ),
        className="flex min-w-0 flex-col gap-5",
        id="board",
    )


def foot():
    return footer(
        p(
            "Pulseboard · ux-compose kit · Caps on the wire · Morph then play",
            className="m-0 text-[11px] uppercase tracking-[0.16em] text-slate-400",
        ),
        className="px-0.5 py-6",
    )


def compose(*, room: str = "overview", atelier: bool = False, prefix: str = ""):
    if room == "pipeline":
        body = pipeline_main()
    elif room == "signals":
        body = signals_main()
    else:
        body = overview_main()
    night = theme_key() == "dark"
    return div(
        rail(room=room, atelier=atelier, prefix=prefix),
        div(
            top_bar(),
            body,
            foot(),
            className=WRAP + " flex-1",
        ),
        className=(
            "flex min-h-dvh w-full min-w-0 "
            + SHELL
            + (" dark" if night else "")
        ),
        data_theme=theme_key(),
        id="pulseboard",
    )


def document_wrap(document: Any):
    """GET Document wrap. Page units already compose the rail — do not nest it.

    Morph payloads stay fragments. ``document`` must be a callable Document.
    """
    if document is None or not callable(document):
        raise TypeError(
            "document_wrap requires a callable Document. "
            "Product path is build(document=, wrap=document_wrap(document))."
        )

    def _wrap(child: Any = None):
        night = theme_key() == "dark"
        inner = child if child is not None else div(id="board")
        return document(
            div(
                inner,
                className=SHELL + (" dark" if night else ""),
                data_theme=theme_key(),
                **{GET_BRAND_ATTR: True},
            )
        )

    return _wrap
