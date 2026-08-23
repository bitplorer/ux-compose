"""
Live ASGI boot — Document SSoT + Behavior + Channel + Motion (full stack).

Requires Python ≥3.14 and specialists:
  ux-dom, ux-behavior, ux-channel, ux-motion, fastapi

Run:
  /tmp/ux314venv/bin/python examples/live_asgi.py
  # then: uvicorn-style — script boots FastAPI and prints routes; optional serve

Isolation Law: this module does not import ux_channel directly.
Channel attaches only through App.use_channel → wire/boot.
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
    doctor,
    div,
    h1,
    span,
    button,
)

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from ux_dom import Document
    from ux_dom.dom import div, h1, span, button as dom_button
    from ux_dom.runtime import XElement, Htmx, Csp
    HAS_DOM = True
except ImportError:
    HAS_DOM = False

try:
    from ux_compose import scene, rise
except Exception:
    scene = rise = None


class Counter(Component):
    id = "livecounter"
    n = RefState(0)
    stamp = MorphState("idle")

    def render(self):
        val = int(self.n or 0)
        if HAS_DOM:
            return div(
                h1(f"Count: {val}"),
                span("+ via Channel Intent when live"),
                button("+1", **control("inc")),
                id=self.id,
                className="counter",
            )
        return f'<div id="{self.id}"><h1>Count: {val}</h1></div>'

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        self.stamp = "tock" if self.stamp == "tick" else "tick"
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("inc").enter(f"#{self.id}", rise.enter(ms=100))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"n={self.n}")])


def build_app():
    """Compose Document + progressive App. Returns (fastapi_app|None, ux_app, document|None)."""
    document = None
    if HAS_DOM:
        document = Document(head=[], body=[], ensure_csrf_token=False).use(
            XElement(),
            Htmx(),
            Csp.auto(),
        )

    ux = App.boot("LiveDemo", strict_caps=False)
    if document is not None:
        ux.use_dom(document)
    ux.use_behavior()

    fastapi_app = None
    if HAS_FASTAPI:
        fastapi_app = FastAPI(title="LiveDemo")
        # Channel via wire door — Isolation held
        ux.use_channel(asgi_app=fastapi_app)
        ux.use_motion()

        @fastapi_app.get("/", response_class=HTMLResponse)
        def index():
            inst = None
            get = getattr(ux.behavior, "get", None)
            if callable(get):
                try:
                    inst = get("livecounter")
                except Exception:
                    inst = None
            body = inst.render() if inst is not None else Counter().render()
            if document is not None:
                page = document(body if not hasattr(body, "__render__") else body)
                return HTMLResponse(str(page))
            return HTMLResponse(f"<html><body>{body}</body></html>")

        @fastapi_app.get("/health")
        def health():
            return {
                "level": int(ux.level),
                "label": ux.level.label,
                "document": document is not None,
            }

    else:
        ux.use_channel()
        ux.use_motion()

    ux.add(Counter)
    return fastapi_app, ux, document


if __name__ == "__main__":
    fastapi_app, ux, document = build_app()
    print("Level:", int(ux.level), f"({ux.level.label})")
    print("Document SSoT:", document is not None)
    print("FastAPI:", fastapi_app is not None)

    ops = ux.dispatch("livecounter.inc")
    print("Dispatch ops:")
    for op in ops:
        print(" ", op)

    report = doctor([], fail=False)
    print("Doctor capabilities:", report.capabilities)
    print("Progressive L" + str(report.level_available))

    if fastapi_app is not None:
        print("Routes:", [r.path for r in fastapi_app.routes if hasattr(r, "path")])
        print("Serve with: uxcompose serve examples.live_asgi:fastapi_app")
        # Expose for uvicorn
        # fastapi_app already built

# Module-level app for uvicorn when specialists present
try:
    fastapi_app, _ux, _doc = build_app()
except Exception:
    fastapi_app = None
