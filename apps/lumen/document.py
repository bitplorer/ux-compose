"""Document SSoT — one HTML shell for every GET.

Runtimes are library contributions: XElement, Channel scripts, CSP.
There is no app ``.js``. Isolation: this module never imports ``ux_channel``.
"""

from __future__ import annotations

try:
    from ux_dom import Document
    from ux_dom.dom import link, meta, title
    from ux_dom.runtime import Channel, Csp, XElement

    from apps.lumen.settings import OUTPUT_CSS

    runtimes: list = [XElement(), Csp.auto()]
    channel_scripts = Channel.optional(inspector=False)
    if channel_scripts is not None:
        runtimes.insert(1, channel_scripts)

    document = Document(
        head=[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Lumen"),
            link(href=f"/css/{OUTPUT_CSS}", rel="stylesheet"),
        ],
        body=[],
        ensure_csrf_token=False,
    ).use(*runtimes)
except Exception:
    document = None
