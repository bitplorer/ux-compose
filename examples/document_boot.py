"""
Full progressive boot with Document SSoT (requires ux-dom, Python ≥3.14).

Demonstrates:
- Exactly one Document owns the HTML shell
- Progressive unlock: Behavior → Channel → Motion
- Unified Component with MorphState + update_with + optional scene
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
    HAS_DOM as COMPOSE_HAS_DOM,
    div,
    span,
    button,
)

try:
    from ux_dom import Document
    from ux_dom.runtime import XElement, Htmx, Csp
    from ux_dom.dom import div, h1, button, span
    HAS_DOM = True
except ImportError:
    HAS_DOM = False

try:
    from ux_compose import scene, rise
except Exception:
    scene = rise = None


class Badge(Component):
    id = "badge"
    count = RefState(0)
    stamp = MorphState("idle")

    def render(self):
        n = int(self.count or 0)
        if COMPOSE_HAS_DOM or HAS_DOM:
            return div(
                span(str(n)),
                button("+1", **control("inc")),
                id=self.id,
                className="badge",
            )
        return f'<div id="{self.id}" class="badge">{n}</div>'

    @action(caps=())
    def inc(self):
        self.count = int(self.count or 0) + 1
        self.stamp = "tock" if self.stamp == "tick" else "tick"
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("badge-pop").enter(f"#{self.id}", rise.enter(ms=120))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"count={self.count}")])


if __name__ == "__main__":
    if not HAS_DOM:
        print("ux-dom not installed — Document SSoT path skipped (needs Python ≥3.14)")
        app = App.boot("Shop", strict_caps=False)
        app.add(Badge)
        print("Level:", int(app.level), app.level.label)
        print(app.dispatch("badge.inc"))
        raise SystemExit(0)

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
