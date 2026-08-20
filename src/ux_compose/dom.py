"""ux-dom tag surface for Unified Component.render().

Authors write::

    from ux_compose import Component, div, h1, button, control

    class Cart(Component):
        def render(self):
            return div(h1(f"Items: {self.count}"), id=self.id)

This module re-exports tags when ux-dom is installed (Python ≥3.14).
It does **not** re-export ux-dom's Component class.

Why not inherit ux-dom Component (or Tags)?
    Freeze is fixable: skip construct render(), republish _entry from live
    render(). That is not the reason.

    The MRO is the reason. Tree verbs (add/remove/get/clear, and whatever
    ux-dom adds next) live on the same instance as @action names. A shared
    MRO collides now or later. Fail closed: Component.__init_subclass__
    rejects ux-dom tree bases.

    Dual inheritance stays forbidden from product code. Authors return tags.
"""

from __future__ import annotations

HAS_DOM = False

# Populated when ux-dom is installed. Stay None on the offline shim path.
div = span = h1 = h2 = h3 = p = a = button = form = input_ = None
ul = li = header = footer = aside = section = article = nav = main = None
label = svg = path = rect = circle = None
html = head = body = title = style = meta = link = script = None
raw = None

try:
    from ux_dom.dom import (  # type: ignore
        a,
        article,
        aside,
        body,
        button,
        circle,
        div,
        footer,
        form,
        h1,
        h2,
        h3,
        head,
        header,
        html,
        input_,
        label,
        li,
        link,
        main,
        meta,
        nav,
        p,
        path,
        rect,
        script,
        section,
        span,
        style,
        svg,
        title,
        ul,
    )
    from ux_dom.dom.src.utils.dom_util import raw  # type: ignore

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
    "raw",
    "html",
    "head",
    "body",
    "title",
    "style",
    "meta",
    "link",
    "script",
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
