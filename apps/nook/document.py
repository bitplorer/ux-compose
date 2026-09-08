"""Document SSoT — one HTML shell for every GET.

Document.use(XElement(), Csp.auto(), Channel.optional()) is the full
shell (CSP + Channel client tags). Channel is the ux_dom.runtime
alias — never ux_channel.Channel. Isolation: this module never imports
ux_channel.

Component.render() stays a fragment — never put the stylesheet link
inside render(). Missing ux-dom fails loud (Python ≥3.14).
"""
from __future__ import annotations

from ux_dom import Document
from ux_dom.runtime import XElement, Csp, Channel
from ux_dom.dom import link, meta, title

from .settings import OUTPUT_CSS

_plugins = (XElement(), Csp.auto(), Channel.optional())
document = Document(
    head=[
        meta(charset="utf-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1"),
        title("Nook"),
        link(rel="preconnect", href="https://fonts.googleapis.com"),
        link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            crossorigin="anonymous",
        ),
        link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:wght@400;500;600&display=swap",
        ),
        link(href=f"/css/{OUTPUT_CSS}", rel="stylesheet"),
    ],
    body=[],
    ensure_csrf_token=False,
).use(*[p for p in _plugins if p is not None])
