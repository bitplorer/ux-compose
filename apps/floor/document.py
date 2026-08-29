"""Document SSoT — one HTML shell for every GET."""

from __future__ import annotations

try:
    from ux_dom import Document
    from ux_dom.runtime import XElement
    from ux_dom.dom import link, meta, script, title

    document = Document(
        head=[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Floor — the house"),
            link(
                href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,600&display=swap",
                rel="stylesheet",
            ),
            script(
                "tailwind.config = {corePlugins:{preflight:false},"
                "theme:{fontFamily:{serif:['Fraunces','Georgia','serif']}}}"
            ),
            script(src="https://cdn.tailwindcss.com"),
        ],
        body=[],
        ensure_csrf_token=False,
    ).use(XElement())
except Exception:
    document = None
