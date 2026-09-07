"""CTO gate 1: create-app scaffold hello HTML fallback is a fragment.

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
    assert 'id="hello"' in src or "id='hello'" in src, f"{label}: missing id=hello"
    assert SHELL_ROOT_ID not in src, f"{label}: must not emit #{SHELL_ROOT_ID}"
    assert SHELL_BRAND not in src, f"{label}: must not emit brand {SHELL_BRAND!r}"
    assert KERNEL_SSOT_ID not in src, f"{label}: must not emit #{KERNEL_SSOT_ID}"
    assert "<html" not in lower, f"{label}: must not emit <html> chrome"
    assert "<head" not in lower, f"{label}: must not emit <head> chrome"
    assert "<body" not in lower, f"{label}: must not emit <body> chrome"
    assert "stylesheet" not in lower, f"{label}: stylesheet chrome belongs on Document"
    assert "<!doctype" not in lower, f"{label}: must not emit a document doctype"


def test_scaffold_routes_hello_py_source_is_fragment():
    _assert_hello_source_is_fragment(ROUTES_HELLO_PY, label="ROUTES_HELLO_PY")
    assert "def render(" in ROUTES_HELLO_PY
    assert "update_with(self" in ROUTES_HELLO_PY
    assert "id=self.id" in ROUTES_HELLO_PY or 'id="hello"' in ROUTES_HELLO_PY


def test_scaffold_html_fallback_root_is_hello_not_document():
    """L1 / Py3.13 string fallback: ``<div id="hello" …>`` — not a shell."""
    src = ROUTES_HELLO_PY
    # The HTML-string fallback (HAS_DOM=False) is the f-string with id="hello".
    assert 'f\'<div id="hello"' in src or '<div id="hello"' in src
    start = src.find('<div id="hello"')
    assert start != -1
    snippet = src[start : start + 280]
    assert first_id(snippet) == "hello"
    assert "stunning-root" not in snippet


def test_document_py_owns_stylesheet_chrome_not_hello():
    assert "/css/" in DOCUMENT_PY or "OUTPUT_CSS" in DOCUMENT_PY
    assert "stylesheet" in DOCUMENT_PY.lower() or "rel=\"stylesheet\"" in DOCUMENT_PY
    assert "stylesheet" not in ROUTES_HELLO_PY.lower()


def test_create_app_emitted_hello_is_fragment(tmp_path):
    root = create_app(tmp_path / "demo", name="demo", level=1, host="asgi")
    hello = (root / "routes" / "hello.py").read_text(encoding="utf-8")
    _assert_hello_source_is_fragment(hello, label="emitted routes/hello.py")
    ast.parse(hello, filename="hello.py")
    assert "import ux_channel" not in hello
    assert "from ux_channel" not in hello


def test_create_app_hello_render_html_fallback_is_fragment(tmp_path):
    """Runtime render() on the emitted Hello: fragment root id=hello."""
    root = create_app(tmp_path / "rt", name="rt", level=1, host="asgi")
    mod = _load_hello(root)
    hello_cls = getattr(mod, "Hello")
    inst = hello_cls()
    tree = inst.render()
    if not isinstance(tree, str):
        from ux_compose.helpers import _serialize_tree

        html = _serialize_tree(tree)
    else:
        html = tree
    assert_html_is_fragment(html, target_id="hello")
    assert first_id(html) == "hello"
