"""Studio chrome — tokens, catalog page, pattern page. Isolation-safe."""
from __future__ import annotations

from typing import Any

from ux_compose import (
    a,
    div,
    footer,
    h1,
    h2,
    header,
    input_,
    p,
    section,
    span,
)
from ux_compose.helpers import _serialize_tree

from examples.catalog import GROUPS, PATTERNS


# Styles: apps/atelier_studio/static/css/atelier.css (linked by host).
# Do NOT put CSS or client JS strings here — specialists + static assets only.
# Progressive base = native form POST. Channel/Motion via Document contributions.

def html_of(tree: Any) -> str:
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    return _serialize_tree(tree)


def nav(*, level: int, label: str):
    return header(
        a("Atelier", span("of Patterns"), href="/", className="brand"),
        div(
            a("Shop", href="/shop"),
            span(f"L{level} {label}", className="level-chip"),
            className="nav-meta",
        ),
        className="top wrap",
    )


def catalog_page():
    groups = []
    jumps = []
    for name in GROUPS:
        rows = [r for r in PATTERNS if r["group"] == name]
        if not rows:
            continue
        gid = f"g-{name.lower().replace(' ', '-')}"
        jumps.append(a(name, href=f"#{gid}"))
        cards = []
        for row in rows:
            laws = [span(x, className="law") for x in row["laws"][:3]]
            cards.append(
                a(
                    p(row["kicker"], className="kicker"),
                    h2(row["title"]),
                    p(row["summary"]),
                    div(*laws, className="chip-row"),
                    href=f"/p/{row['slug']}",
                    className="cat-card",
                )
            )
        groups.append(
            section(
                div(
                    h2(name),
                    span(str(len(rows)), className="muted"),
                    className="group-head",
                ),
                div(*cards, className="grid cards"),
                className="group",
                id=gid,
            )
        )
    filter_row = []
    if input_ is not None:
        filter_row = [
            div(
                input_(
                    id="catalog-filter",
                    type="search",
                    placeholder="Filter patterns — rating, kanban, lightbox…",
                    autocomplete="off",
                    aria_label="Filter patterns",
                ),
                className="filter-row",
            )
        ]
    return (
        section(
            p("99% of product UI", className="kicker"),
            h1("Every pattern is a Component."),
            p(
                f"{len(PATTERNS)} full-length cases. One class each. MorphState, "
                "RefState, @action. Tags from render(). Open a card and press it — "
                "the morph lands, then motion plays.",
                className="lede",
            ),
            className="hero",
        ),
        div(*jumps, className="jump"),
        *filter_row,
        *groups,
    )


def pattern_page(row: dict[str, Any], widget: Any):
    laws = [span(x, className="law") for x in row["laws"]]
    brief = div(
        p("The contract", className="kicker"),
        h2(row["title"]),
        p(row["detail"]),
        div(*laws, className="chip-row"),
        p(row["file"], className="file"),
        className="brief",
    )
    stage = div(widget, id="stage", className="stage")
    return (
        section(
            a("← All patterns", href="/", className="back"),
            p(row["group"], className="kicker"),
            h1(row["title"]),
            p(row["summary"], className="lede"),
            className="pattern-hero",
        ),
        div(stage, brief, className="layout"),
    )


def foot():
    return footer(
        span("ux-compose · tags are the return type"),
        span("No React. Caps on the wire. Morph then play."),
        className="foot wrap",
    )


def toast_host():
    return div(id="ux-toasts", className="toast-host", aria_live="polite")
