"""CTO: Document-path brand chrome is GET-only. Morph and render() stay fragments.

P1-3: brand_wrap(document, brand=) returns wrap(child). GET brand=1, morph
brand=0. Component.render() never embeds nav brand / stunning-root.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import ROUTES_HELLO_PY, create_app

from tests.feature.morph import (
    KERNEL_SSOT_ID,
    SHELL_BRAND,
    SHELL_ROOT_ID,
    assert_html_is_fragment,
    morph_html_and_target,
)

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None
HAS_DOM = importlib.util.find_spec("ux_dom") is not None
BRAND = "AcmeBrand"


def _load_hello(root: Path):
    path = root / "routes" / "hello.py"
    spec = importlib.util.spec_from_file_location("cto_brand_hello", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _hello_html(mod) -> str:
    tree = mod.Hello().render()
    if not isinstance(tree, str):
        from ux_compose.algebra import _serialize_tree

        return _serialize_tree(tree)
    return tree


def test_scaffold_hello_render_has_no_brand_chrome():
    """Official hello.render() is fragment-only — never embed the GET shell."""
    src = ROUTES_HELLO_PY
    assert "nav(" not in src
    assert "<nav" not in src.lower()
    assert "stunning-root" not in src
    assert SHELL_BRAND not in src
    assert KERNEL_SSOT_ID not in src
    assert "brand_wrap" not in src
    assert "wrap_get_chrome" not in src
    assert "HAS_DOM" not in src


def test_create_app_hello_render_stays_fragment_with_brand_flag(tmp_path):
    root = create_app(
        tmp_path / "branded", name="branded", level=1, host="asgi", brand=BRAND
    )
    hello = (root / "routes" / "hello.py").read_text(encoding="utf-8")
    app_py = (root / "app.py").read_text(encoding="utf-8")
    ast.parse(hello, filename="hello.py")
    ast.parse(app_py, filename="app.py")
    assert "nav(" not in hello
    assert "<nav" not in hello.lower()
    assert SHELL_ROOT_ID not in hello
    assert BRAND not in hello
    assert "wrap_get_chrome" not in hello
    assert "wrap_get_chrome" not in app_py
    assert "from ux_compose.brand import brand_wrap" in app_py
    assert "brand_wrap(document" in app_py
    assert BRAND in app_py
    assert "shell.py" not in app_py
    assert not (root / "shell.py").exists()
    mod = _load_hello(root)
    html = _hello_html(mod)
    assert_html_is_fragment(html, target_id="hello")
    assert BRAND not in html
    assert "stunning-root" not in html


@pytest.mark.skipif(not HAS_FASTAPI or not HAS_DOM, reason="fastapi + ux-dom")
def test_brand_wrap_get_brand_once_morph_brand_zero(tmp_path):
    """Clock A GET includes brand once; Clock B morph HTML has brand=0."""
    from ux_dom import Document
    from ux_compose.build import build
    from ux_compose.brand import GET_CHROME_ATTR, brand_wrap
    from ux_compose.algebra import update_with
    from tests.asgi_http import asgi_get

    root = create_app(tmp_path / "livebrand", name="livebrand", level=1, host="fastapi")
    hello_src = (root / "routes" / "hello.py").read_text(encoding="utf-8")
    assert "nav(" not in hello_src
    assert BRAND not in hello_src

    document = Document(head=[], body=[], ensure_csrf_token=False)
    app, asgi, _bundle = build(
        root,
        name="livebrand",
        host="fastapi",
        live="null",
        level=1,
        document=document,
        wrap=brand_wrap(document, brand=BRAND),
        cek="off",
    )
    assert asgi is not None
    page = asgi_get(asgi, "/hello")
    assert page.status_code == 200, page.text[:400]
    assert page.text.count(BRAND) == 1
    assert GET_CHROME_ATTR in page.text
    assert 'id="hello"' in page.text
    assert SHELL_ROOT_ID not in page.text

    ops = app.dispatch("hello.inc")
    morph, target = morph_html_and_target(ops)
    assert "#hello" in (target or "#hello")
    assert morph.count(BRAND) == 0
    assert GET_CHROME_ATTR not in morph
    assert_html_is_fragment(morph, target_id="hello")

    mod = _load_hello(root)
    inst = mod.Hello()
    rendered = _hello_html(mod)
    assert BRAND not in rendered
    morph2, _ = morph_html_and_target(update_with(inst))
    assert morph2.count(BRAND) == 0
