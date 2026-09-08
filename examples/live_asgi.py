"""
Live ASGI boot — Document SSoT + build() (full stack).

Requires Python ≥3.14 and specialists:
  ux-dom, ux-behavior, ux-channel, ux-motion, fastapi

Run:
  PYTHONPATH=src:. python examples/live_asgi.py

Isolation Law: this module does not import ux_channel directly.
Channel attaches only through build() → App.use_channel → wire/boot.
Clock A GET is the product host pipeline (routes/ page unit via build()),
not a handmade HTMLResponse.
"""
from __future__ import annotations

from pathlib import Path

from ux_compose import doctor
from ux_compose.build import build

PACKAGE = Path(__file__).resolve().parent / "live_asgi_app"

from ux_dom import Document
from ux_dom.runtime import XElement, Htmx, Csp


def build_app():
    """Compose Document + App via build(). Returns (app, asgi, bundle, document)."""
    document = Document(head=[], body=[], ensure_csrf_token=False).use(
        XElement(),
        Htmx(),
        Csp.auto(),
    )

    app, asgi, bundle = build(
        PACKAGE,
        name="LiveDemo",
        host="auto",
        live="auto",
        document=document,
    )

    # Extra APIs live on the FastAPI process, not on the page class.
    if asgi is not None and callable(getattr(asgi, "get", None)):

        @asgi.get("/health")
        def health():
            return {
                "level": int(app.level),
                "label": app.level.label,
                "document": True,
            }

    return app, asgi, bundle, document


app, asgi, bundle, document = build_app()


if __name__ == "__main__":
    print("Level:", int(app.level), f"({app.level.label})")
    print("Document SSoT:", app._document is document)
    print("ASGI:", type(asgi).__name__)

    ops = app.dispatch("livecounter.inc")
    print("Dispatch ops:")
    for op in ops:
        print(" ", op)

    report = doctor([], fail=False, bundle=bundle)
    print("Doctor capabilities:", report.capabilities)
    print("Progressive L" + str(report.level_available))
    print("Routes:", [r.get("path") for r in (bundle.route_table or [])])

    print("Serve with: uxcompose serve examples.live_asgi:asgi")
