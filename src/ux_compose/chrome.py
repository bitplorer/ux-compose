"""GET-only page chrome for Document-absent apps (Py3.13 / L1 HTML-string).

Clock A wraps ``render()`` with ``build(wrap=)`` / ``host.bind(wrap=)``.
Clock B morph payloads stay fragments — ``update_with`` reads
``Component.render()``, not this helper.

This is a **string shell**, the same law as ``live_client``: never synthesize
a ux-dom ``Document`` from strings (a positional ``str`` on ``<body>`` is
script ``src``). Py3.14 authors keep ``document.py`` as ``wrap``.

Authors who put brand / ``stunning-root`` / ``class="nav"`` inside
``routes/*.py`` ``render()`` reinvent EditorialShell middleware and nest
chrome on every morph. Doctor residual-teaches that shape.

Usage::

    from functools import partial
    from ux_compose.chrome import wrap_get_chrome

    app, asgi, bundle = build(
        PACKAGE,
        document=None,
        wrap=partial(wrap_get_chrome, brand="Acme"),
    )
"""
from __future__ import annotations

from html import escape
from typing import Any

GET_CHROME_ATTR = "data-uxcompose-get-chrome"
DEFAULT_BRAND = "App"

__all__ = [
    "GET_CHROME_ATTR",
    "DEFAULT_BRAND",
    "wrap_get_chrome",
    "get_chrome",
]


def _fragment_html(inner: Any) -> str:
    """Serialize a GET fragment without building a Document."""
    if inner is None:
        return ""
    if isinstance(inner, (bytes, bytearray, memoryview)):
        return bytes(inner).decode("utf-8")
    if isinstance(inner, str):
        return inner
    from ux_compose.helpers import _serialize_tree

    return _serialize_tree(inner)


def wrap_get_chrome(inner: Any = None, *, brand: str = DEFAULT_BRAND) -> str:
    """Wrap a GET fragment in brand chrome. Do not call from ``render()``.

    ``brand`` appears once (the nav label). Morph HTML must not include it.
    Safe as ``wrap=``: ``apply_html_document`` calls this with the fragment
    (string or ux-dom ``raw()`` node). Returns an HTML **string**, never a
    ``Document``.
    """
    label = escape(str(brand), quote=True)
    body = _fragment_html(inner)
    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"</head><body {GET_CHROME_ATTR}>"
        f'<nav class="nav" aria-label="Site"><span class="brand">{label}</span></nav>'
        f"{body}"
        "</body></html>"
    )


def get_chrome(*, brand: str = DEFAULT_BRAND):
    """Return a ``wrap=`` callable for ``build()`` / ``host.bind``.

    Equivalent to ``partial(wrap_get_chrome, brand=brand)`` with a ``None``
    inner default so empty GET still produces chrome.
    """

    def wrap(inner: Any = None) -> str:
        return wrap_get_chrome(inner, brand=brand)

    wrap.brand = brand  # type: ignore[attr-defined]
    return wrap
