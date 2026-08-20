"""Document SSoT integration when ux-dom is installed (Python ≥3.14)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_DOM = importlib.util.find_spec("ux_dom") is not None

pytestmark = pytest.mark.skipif(not HAS_DOM, reason="ux-dom not installed (needs Python ≥3.14)")


def test_document_single_ssot():
    from ux_dom import Document
    from ux_dom.runtime import XElement, Htmx, Csp

    doc = Document(head=[], body=[], ensure_csrf_token=False).use(
        XElement(),
        Htmx(),
        Csp.auto(),
    )
    assert doc is not None
    assert hasattr(doc, "use")
    assert hasattr(doc, "mount")


def test_app_use_dom_attaches_document():
    from ux_dom import Document
    from ux_compose import App

    doc = Document(head=[], body=[], ensure_csrf_token=False)
    app = App.boot("Shop", strict_caps=False).use_dom(doc)
    assert app._document is doc


def test_app_use_dom_and_motion_attach_order():
    """Attach order: Document.use(Motion, MotionChannel) via controlled door."""
    from ux_dom import Document
    from ux_compose import App

    doc = Document(head=[], body=[], ensure_csrf_token=False)
    app = (
        App.boot("Shop", strict_caps=False)
        .use_dom(doc)
        .use_behavior()
        .use_channel()
        .use_motion()
    )
    assert int(app.level) >= 3
    assert app._document is doc
    assert app._motion is True


def test_component_render_returns_dom_compatible():
    """Unified Component render can return string or tree; Document accepts content."""
    from ux_compose import App, Component, MorphState, action

    class Hello(Component):
        id = "hello"
        n = MorphState(0)

        def render(self):
            return f'<div id="hello">{self.n}</div>'

        @action(caps=())
        def inc(self):
            self.n = int(self.n) + 1
            return None

    app = App.boot("T", strict_caps=False)
    app.add(Hello)
    ops = app.dispatch("hello.inc")
    assert ops
    # render produces markup
    inst = app._instances.get("hello") or Hello()
    html = inst.render()
    assert "hello" in str(html)
