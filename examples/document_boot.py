"""
Full progressive boot with Document SSoT (requires ux-dom, Python ≥3.14).

Demonstrates:
- Exactly one Document owns the HTML shell
- Progressive levels (attach on complete install): Behavior → Channel → Motion
- Unified Component with MorphState + update_with + scene Plan
- Isolation: product code never imports channel/CEK

Run (Python 3.14 venv with specialists):
  /tmp/ux314venv/bin/python examples/document_boot.py
"""
from __future__ import annotations

from ux_compose import (
    App,
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    control,
    scene,
    rise,
    div,
    span,
    button,
)
from ux_dom import Document
from ux_dom.runtime import XElement, Htmx, Csp


class Badge(Component):
    id = "badge"
    count = RefState(0)
    dirty = MorphState("idle")

    def render(self):
        n = int(self.count or 0)
        return div(
            span(str(n)),
            button("+1", **control("inc")),
            id=self.id,
            className="badge",
        )

    @action(caps=())
    def inc(self):
        self.count = int(self.count or 0) + 1
        self.dirty = "tock" if self.dirty == "tick" else "tick"
        plan = scene("badge-pop").enter(f"#{self.id}", rise.enter(ms=120))
        return update_with(self, plan, extra_ops=[notify(f"count={self.count}")])


if __name__ == "__main__":
    document = Document(head=[], body=[], ensure_csrf_token=False).use(
        XElement(),
        Htmx(),
        Csp.auto(),
    )

    app = (
        App.boot("Shop", strict_caps=False)
        .use_dom(document)
        .use_behavior()
        .use_channel()
        .use_motion()
    )
    app.add(Badge)

    print("Level:", int(app.level), f"({app.level.label})")
    print("Document SSoT: single Document attached:", app._document is document)
    ops = app.dispatch("badge.inc")
    print("Ops:")
    for op in ops:
        print(" ", op)

    # Doctor
    from ux_compose import doctor
    report = doctor([], fail=False)
    print("Doctor ok:", report.ok)
    print("Capabilities:", report.capabilities)
    print("Progressive level available: L" + str(report.level_available))
