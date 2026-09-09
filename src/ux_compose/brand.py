"""Document-path GET brand chrome.

Not OverlayChrome (``kit/overlay.py`` — dialog / sheet / action-sheet
ids and swipe). This module wraps GET. Overlay chrome wraps widgets.

Clock A wraps ``render()`` with ``build(wrap=)``. Clock B morph payloads
stay fragments — ``update_with`` reads ``Component.render()``, not this helper.

``brand_wrap(document, brand=...)`` returns ``wrap(child)`` that places nav
brand **outside** ``Component.render``. Product path is Document (Python
≥3.14). There is no Document-absent string shell.

Usage::

    from ux_compose.brand import brand_wrap
    from document import document

    app, asgi, bundle = build(
        PACKAGE,
        document=document,
        wrap=brand_wrap(document, brand="Acme"),
    )
"""
from __future__ import annotations

from typing import Any

from ux_compose.dom import nav, raw, span

GET_CHROME_ATTR = "data-uxcompose-get-chrome"
DEFAULT_BRAND = "App"

__all__ = [
    "GET_CHROME_ATTR",
    "DEFAULT_BRAND",
    "brand_wrap",
]


def _as_child(inner: Any) -> Any:
    """Accept a GET fragment (tag tree or HTML str via ``raw()``)."""
    if inner is None:
        return None
    if isinstance(inner, (bytes, bytearray, memoryview)):
        inner = bytes(inner).decode("utf-8")
    if isinstance(inner, str):
        return raw(inner)
    return inner


def brand_wrap(document: Any, *, brand: str = DEFAULT_BRAND):
    """Return ``wrap(child)`` that puts brand nav on the Document GET shell.

    Do not call from ``Component.render()``. Morph HTML must not include
    ``brand``. ``document`` must be a callable Document.
    """
    if document is None or not callable(document):
        raise TypeError(
            "brand_wrap requires a callable Document. "
            "Product path is build(document=, wrap=brand_wrap(document, brand=...)). "
            "There is no Document-absent string shell."
        )
    label = str(brand)

    def wrap(child: Any = None):
        chrome = nav(
            span(label, className="brand"),
            className="nav",
            aria_label="Site",
            **{GET_CHROME_ATTR: True},
        )
        node = _as_child(child)
        if node is None:
            return document(chrome)
        return document(chrome, node)

    wrap.brand = label  # type: ignore[attr-defined]
    return wrap
