"""ux-dom tag surface for Unified Component.render().

Authors write::

    from ux_compose import Component, div, h1, button, control

    class Cart(Component):
        def render(self):
            return div(h1(f"Items: {self.count}"), id=self.id)

This module re-exports tags when ux-dom is installed (Python ≥3.14).
It does **not** re-export ux-dom's Component class.

Why not inherit ux-dom Component?
    ux-dom Component.__init__ *is* render: it calls render() once, inserts
    the tree as children, and freezes. That is the right lifetime for a
    static SSR page unit.

    ux-compose Component is a Behavior unit: long-lived, MorphState-driven,
    re-rendered after every @action. Inheriting the ux-dom class would
    snapshot the empty tree at Behavior.add() time and never rebuild.

    Dual inheritance stays internal and invisible. The author surface is
    one class: Behavior protocol + render() returns ux-dom trees.
"""

from __future__ import annotations

from typing import Any

HAS_DOM = False

# Populated when ux-dom is installed. Stay None on the offline shim path.
div = span = h1 = h2 = h3 = p = a = button = form = input_ = None
ul = li = header = footer = aside = section = article = nav = main = None
label = svg = path = rect = circle = None

try:
    from ux_dom.dom import (  # type: ignore
        a,
        article,
        aside,
        button,
        circle,
        div,
        footer,
        form,
        h1,
        h2,
        h3,
        header,
        input_,
        label,
        li,
        main,
        nav,
        p,
        path,
        rect,
        section,
        span,
        svg,
        ul,
    )

    HAS_DOM = True
except ImportError:  # pragma: no cover
    pass


def require_dom() -> None:
    if not HAS_DOM:
        raise ImportError(
            "ux-dom is not installed. Tag trees need Python ≥3.14 and "
            "`pip install ux-dom`. HTML strings in render() still work at L1."
        )


__all__ = [
    "HAS_DOM",
    "require_dom",
    "div",
    "span",
    "h1",
    "h2",
    "h3",
    "p",
    "a",
    "button",
    "form",
    "input_",
    "ul",
    "li",
    "header",
    "footer",
    "aside",
    "section",
    "article",
    "nav",
    "main",
    "label",
    "svg",
    "path",
    "rect",
    "circle",
]
