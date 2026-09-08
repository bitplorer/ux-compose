"""ux-dom tag surface for Unified Component.render().

Authors write::

    from ux_compose import Component, div, h1, button, control

    class Cart(Component):
        def render(self):
            return div(h1(f"Items: {self.count}"), id=self.id)

This module re-exports tags from ux-dom (hard dependency, Python ≥3.14).
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

from ux_dom.dom import (  # type: ignore
    a,
    article,
    aside,
    body,
    button,
    circle,
    div,
    dl,
    dt,
    dd,
    fieldset,
    footer,
    form,
    h1,
    h2,
    h3,
    head,
    header,
    hr,
    html,
    img,
    input_,
    label,
    legend,
    li,
    link,
    main,
    meta,
    nav,
    p,
    path,
    progress,
    rect,
    script,
    section,
    span,
    style,
    svg,
    table,
    tbody,
    td,
    th,
    thead,
    title,
    tr,
    ul,
)
from ux_dom.dom.src.utils.dom_util import raw  # type: ignore

HAS_DOM = True


def require_dom() -> None:
    """Fail loud if ux-dom is not importable. Hard-dep: this is a no-op on
    a complete install; tests may monkeypatch ``HAS_DOM``.
    """
    if not HAS_DOM:
        raise ImportError(
            "ux-dom is not installed. ux-compose hard-depends on ux-dom "
            "(Python ≥3.14). Install the pinned specialists."
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
    "dl",
    "dt",
    "dd",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "fieldset",
    "legend",
    "hr",
    "img",
    "progress",
]
