"""Document SSoT — one HTML shell for every GET."""

from __future__ import annotations

try:
    from ux_dom import Document
    from ux_dom.runtime import XElement, Csp
    from ux_dom.dom import link, meta, title

    document = Document(
        head=[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Nook"),
            link(href="/css/output.css", rel="stylesheet"),
        ],
        body=[],
        ensure_csrf_token=False,
    ).use(XElement(), Csp.auto())
except Exception:
    document = None
