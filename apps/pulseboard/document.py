"""Document SSoT — one HTML shell for every GET.

Document.use(XElement(), Csp.auto(), Channel.optional()) is the full
shell. Channel is the ux_dom.runtime alias — never ux_channel.Channel.
"""
from __future__ import annotations

from ux_dom import Document
from ux_dom.dom import link, meta, script, title
from ux_dom.runtime import Channel, Csp, XElement

from .settings import OUTPUT_CSS

_plugins = (
    XElement(),
    Csp.auto(
        style_hosts=("https://fonts.googleapis.com",),
        font_src=("'self'", "data:", "https://fonts.gstatic.com"),
    ),
    Channel.optional(),
)
document = Document(
    head=[
        meta(charset="utf-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1"),
        meta(name="color-scheme", content="dark light"),
        title("Pulseboard · Atelier Pulse"),
        meta(name="theme-color", content="#07090d"),
        link(rel="preconnect", href="https://fonts.googleapis.com"),
        link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            crossorigin="anonymous",
        ),
        link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap",
        ),
        link(href=f"/css/{OUTPUT_CSS}", rel="stylesheet"),
        link(rel="stylesheet", href="/static/css/pulseboard.css"),
        script(src="/static/pulseboard.js"),
    ],
    body=[],
    ensure_csrf_token=False,
).use(*[p for p in _plugins if p is not None])
