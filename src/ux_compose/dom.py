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
from ux_dom.dom import raw  # type: ignore

HAS_DOM = True


# --- HTML sink contract ------------------------------------------------------
#
# One closed type contract for every place compose turns a value into HTML
# for the client: route bodies, stream chunks, render(), update_with /
# ux_behavior.update morph html, morph / swap ops, motion enter html.
#
#   trusted    ``__html__`` (Markup, TrustedHtml) and real ux-dom tree nodes
#              (ux-dom ``dom_tag`` / ``Component``, ``Document``, compose
#              ``Component``), rendered by the ux-dom renderer
#   sanitized  ``str``, and ``bytes`` decoded as strict UTF-8, through
#              ux-dom ``sanitize_html``
#   ``None``   empty HTML
#   anything else (list, tuple, dict, numbers, other objects): TypeError
#              naming the sink. Nothing is ``str()``-coerced.


class TrustedHtml(str):
    """HTML that goes to the client as written (``__html__``, like ``Markup``).

    Only :func:`html_text` makes one: from ``sanitize_html`` output, from the
    ux-dom renderer, or from an ``__html__`` value.
    """

    __slots__ = ()

    def __html__(self) -> str:
        return str(self)


def _is_tree(value) -> bool:
    from ux_dom import Document
    from ux_dom.dom import Component as DomComponent
    from ux_dom.dom import dom_tag

    from ux_compose.component import Component

    return isinstance(value, (dom_tag, DomComponent, Document, Component))


def _bytes_text(value, *, sink: str) -> str:
    """``bytes`` → ``str``, strict UTF-8. Undecodable bytes raise ``ValueError``."""
    try:
        return bytes(value).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{sink}: bytes are not valid UTF-8 ({exc.reason})") from exc


def html_value(value, *, sink: str):
    """Apply the contract: a trusted tree node itself, or a :class:`TrustedHtml`.

    ``sink`` names the place in the ``TypeError`` / ``ValueError``.
    """
    from ux_dom.response import sanitize_html

    if value is None:
        return TrustedHtml("")
    html_method = getattr(value, "__html__", None)
    if callable(html_method):
        return TrustedHtml(html_method())
    if isinstance(value, (bytes, bytearray, memoryview)):
        value = _bytes_text(value, sink=sink)
    if isinstance(value, str):
        return TrustedHtml(sanitize_html(value))
    if _is_tree(value):
        return value
    raise TypeError(
        f"{sink}: HTML must be str, bytes, Markup (__html__) or a ux-dom tree, "
        f"not {type(value).__name__}"
    )


def html_text(value, *, sink: str) -> TrustedHtml:
    """:func:`html_value` as a string; a tree is rendered by ux-dom."""
    out = html_value(value, sink=sink)
    if isinstance(out, TrustedHtml):
        return out
    from ux_dom.response import to_html_bytes

    return TrustedHtml(to_html_bytes(out).decode("utf-8"))


def html_child(value, *, sink: str):
    """:func:`html_value` as a Document child: a tree, or ``raw()`` markup."""
    out = html_value(value, sink=sink)
    return raw(out) if isinstance(out, TrustedHtml) else out


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
