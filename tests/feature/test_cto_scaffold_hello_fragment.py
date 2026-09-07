"""CTO gate 1: create-app scaffold hello is a Document-path fragment.

Official ROUTES_HELLO_PY is the correct author shape: id=hello root, no
document chrome. Stunning diverged; this gate locks the scaffold.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import ROUTES_HELLO_PY, DOCUMENT_PY, create_app

from tests.feature.morph import (
    KERNEL_SSOT_ID,
    SHELL_BRAND,
    SHELL_ROOT_ID,
    assert_html_is_fragment,
    first_id,
)


def _load_hello(root: Path):
    path = root / "routes" / "hello.py"
    spec = importlib.util.spec_from_file_location("cto_scaffold_hello", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _assert_hello_source_is_fragment(src: str, *, label: str) -> None:
    lower = src.lower()
    assert 'id="hello"' in src or "id='hello'" in src or "id=self.id" in src, (
        f"{label}: missing id=hello"
    )
    assert SHELL_ROOT_ID not in src, f"{label}: must not emit #{SHELL_ROOT_ID}"
    assert SHELL_BRAND not in src, f"{label}: must not emit brand {SHELL_BRAND!r}"
    assert KERNEL_SSOT_ID not in src, f"{label}: must not emit #{KERNEL_SSOT_ID}"
    assert "<html" not in lower, f"{label}: must not emit <html> chrome"
    assert "<head" not in lower, f"{label}: must not emit <head> chrome"
    assert "<body" not in lower, f"{label}: must not emit <body> chrome"
    assert "stylesheet" not in lower, f"{label}: stylesheet chrome belongs on Document"
    assert "<!doctype" not in lower, f"{label}: must not emit a document doctype"
    assert "HAS_DOM" not in src, f"{label}: Document path only — no HAS_DOM branch"
    assert 'f\'<div id="hello"' not in src, f"{label}: no HTML-string fallback"


def test_scaffold_routes_hello_py_source_is_fragment():
    _assert_hello_source_is_fragment(ROUTES_HELLO_PY, label="ROUTES_HELLO_PY")
    assert "def render(" in ROUTES_HELLO_PY
    assert "update_with(self" in ROUTES_HELLO_PY
    assert "id=self.id" in ROUTES_HELLO_PY or 'id="hello"' in ROUTES_HELLO_PY
    assert "from ux_compose import div" in ROUTES_HELLO_PY or "div," in ROUTES_HELLO_PY


def test_scaffold_hello_source_teaches_gated_pulse_without_shell_chrome():
    """Official hello: MorphState pulses + @action(caps=('pulse',)) + control mint."""
    src = ROUTES_HELLO_PY
    assert "pulses = MorphState" in src
    assert '@action(caps=("pulse",))' in src
    assert "def pulse" in src
    assert 'control("hello.pulse")' in src
    assert "import ux_channel" not in src
    assert "from ux_channel" not in src
    _assert_hello_source_is_fragment(src, label="ROUTES_HELLO_PY pulse")
    assert "nav(" not in src
    assert "<nav" not in src.lower()


def test_document_py_owns_stylesheet_chrome_not_hello():
    assert "/css/" in DOCUMENT_PY or "OUTPUT_CSS" in DOCUMENT_PY
    assert "stylesheet" in DOCUMENT_PY.lower() or 'rel="stylesheet"' in DOCUMENT_PY
    assert "stylesheet" not in ROUTES_HELLO_PY.lower()
    assert "except Exception" not in DOCUMENT_PY
    assert "document = None" not in DOCUMENT_PY


def test_create_app_emitted_hello_is_fragment(tmp_path):
    root = create_app(tmp_path / "demo", name="demo", level=1, host="asgi")
    hello = (root / "routes" / "hello.py").read_text(encoding="utf-8")
    _assert_hello_source_is_fragment(hello, label="emitted routes/hello.py")
    ast.parse(hello, filename="hello.py")
    assert "import ux_channel" not in hello
    assert "from ux_channel" not in hello
    assert not (root / "shell.py").exists()


def _hello_html(mod) -> str:
    tree = mod.Hello().render()
    if not isinstance(tree, str):
        from ux_compose.helpers import _serialize_tree

        return _serialize_tree(tree)
    return tree


def test_create_app_hello_render_is_document_path_fragment(tmp_path):
    """Runtime render() on the emitted Hello: DOM tree, fragment root id=hello."""
    root = create_app(tmp_path / "rt", name="rt", level=1, host="asgi")
    mod = _load_hello(root)
    tree = mod.Hello().render()
    assert not isinstance(tree, str)
    html = _hello_html(mod)
    assert_html_is_fragment(html, target_id="hello")
    assert first_id(html) == "hello"


def test_create_app_hello_document_path_emits_pulse_control(tmp_path):
    """Document path stamps hello.pulse. No HTML-string dual floor."""
    root = create_app(tmp_path / "pulse_paths", name="pulse_paths", level=1, host="asgi")
    mod = _load_hello(root)
    live = _hello_html(mod)
    assert "hello.pulse" in live
    assert 'data-channel-action="hello.pulse"' in live or "hello.pulse" in live
    assert_html_is_fragment(live, target_id="hello")
    assert "stunning-root" not in live
    assert "StunningCek" not in live
    assert not hasattr(mod.Hello(), "_render_html")
