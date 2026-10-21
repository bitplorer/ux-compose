"""
Full progressive boot with Document SSoT (requires ux-dom, Python ≥3.14).

Demonstrates:
- Exactly one Document owns the HTML shell
- Progressive levels (attach on complete install): Behavior → Channel → Motion
- Unified Component (components.Badge) with MorphState + update_with
- Isolation: product code never imports channel/CEK

Run (Python 3.14 venv with specialists):
  /tmp/ux314venv/bin/python examples/document_boot.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)
from ux_compose.htmx import Htmx
from ux_dom import Csp, Document, XElement
from ux_compose.components.badge import Badge


if __name__ == "__main__":
    document = Document(head=[], body=[], ensure_csrf_token=False).use(
        XElement(),
        Htmx(),
        Csp.auto(),
    )

    app = (
        App.boot("Shop")
        .use_dom(document)
        .use_behavior()
        .use_channel()
        .use_motion()
    )
    app.add(Badge)

    print("Level:", int(app.level), f"({app.level.label})")
    print("Document SSoT: single Document attached:", app._document is document)
    ops = app.dispatch("badge.choose", key="make")
    print("Ops:")
    for op in ops:
        print(" ", op)

    # Doctor
    from ux_compose import doctor
    report = doctor([], fail=False)
    print("Doctor ok:", report.ok)
    print("Capabilities:", report.capabilities)
    print("Progressive level available: L" + str(report.level_available))
