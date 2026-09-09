"""Document-path GET brand chrome: brand on Clock A GET, never in morph HTML."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None
HAS_DOM = importlib.util.find_spec("ux_dom") is not None

from ux_compose.algebra import _serialize_tree, update_with
from ux_compose.routing.core import apply_html_document

from tests.asgi_http import asgi_get
from tests.feature.morph import morph_html_and_target

ROOT = Path(__file__).resolve().parents[2]
BRAND = "AcmeBrand"


def _html(tree) -> str:
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    return _serialize_tree(tree)


def _pkg(tmp_path: Path, files: dict[str, str], name: str = "chromedemo") -> Path:
    pkg = tmp_path / name
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    for rel, src in files.items():
        dest = pkg / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src, encoding="utf-8")
    return pkg


def test_chrome_source_is_document_path_not_string_shell():
    """Hard-deps Document path. Do not revive wrap_get_chrome / HAS_DOM shells."""
    src = (ROOT / "src" / "ux_compose" / "brand.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("ux_channel")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("ux_channel")
    assert "wrap_get_chrome" not in src
    assert "HAS_DOM" not in src
    assert "<!DOCTYPE html>" not in src
    assert "shell.py" not in src


def test_brand_wrap_requires_callable_document():
    from ux_compose.brand import brand_wrap

    with pytest.raises(TypeError):
        brand_wrap(None, brand=BRAND)


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom Document path")
def test_brand_wrap_puts_brand_once_outside_fragment():
    from ux_dom import Document
    from ux_compose import div, span
    from ux_compose.brand import GET_CHROME_ATTR, brand_wrap

    document = Document(head=[], body=[], ensure_csrf_token=False)
    wrap = brand_wrap(document, brand=BRAND)
    inner = div(span("hi"), id="hello")
    html = _html(wrap(inner))
    assert html.count(BRAND) == 1
    assert GET_CHROME_ATTR in html
    assert 'class="nav"' in html or "class='nav'" in html
    assert 'class="brand"' in html or "class='brand'" in html
    assert 'id="hello"' in html
    assert "stunning-root" not in html
    assert wrap.brand == BRAND


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom Document path")
def test_apply_html_document_brand_wrap_keeps_fragment():
    from ux_dom import Document
    from ux_compose.brand import GET_CHROME_ATTR, brand_wrap

    wrap = brand_wrap(Document(head=[], body=[], ensure_csrf_token=False), brand=BRAND)
    out = _html(apply_html_document(wrap, '<div id="hello">hi</div>'))
    assert out.count(BRAND) == 1
    assert GET_CHROME_ATTR in out
    assert "hi" in out
    assert 'id="hello"' in out


@pytest.mark.skipif(not HAS_FASTAPI or not HAS_DOM, reason="fastapi + ux-dom")
def test_build_brand_wrap_get_html_has_brand_once_morph_has_zero(tmp_path: Path):
    from ux_dom import Document
    from ux_compose.build import build
    from ux_compose.brand import GET_CHROME_ATTR, brand_wrap

    pkg = _pkg(
        tmp_path,
        {
            "routes/hello.py": (
                "from ux_compose import Component, MorphState, action, update_with\n"
                "from ux_compose import div, span\n"
                "\n"
                "class Hello(Component):\n"
                "    id = 'hello'\n"
                "    n = MorphState(0)\n"
                "\n"
                "    def render(self):\n"
                "        n = int(self.n or 0)\n"
                "        return div(span(str(n)), id=self.id)\n"
                "\n"
                "    @action(caps=())\n"
                "    def inc(self):\n"
                "        self.n = int(self.n or 0) + 1\n"
                "        return update_with(self)\n"
            )
        },
    )
    document = Document(head=[], body=[], ensure_csrf_token=False)
    app, asgi, _bundle = build(
        pkg,
        name="Demo",
        host="fastapi",
        live="null",
        level=1,
        document=document,
        wrap=brand_wrap(document, brand=BRAND),
        cek="off",
    )
    r = asgi_get(asgi, "/hello")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert r.text.count(BRAND) == 1
    assert GET_CHROME_ATTR in r.text
    assert 'id="hello"' in r.text
    assert "stunning-root" not in r.text

    ops = app.dispatch("hello.inc")
    morph, target = morph_html_and_target(ops)
    assert "#hello" in (target or "#hello")
    assert morph.count(BRAND) == 0
    assert GET_CHROME_ATTR not in morph
    assert "stunning-root" not in morph
    assert 'id="hello"' in morph


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom Document path")
def test_update_with_fragment_never_includes_wrap_brand():
    from ux_dom import Document
    from ux_compose import Component, MorphState, action, div, span
    from ux_compose.brand import GET_CHROME_ATTR, brand_wrap

    class Hello(Component):
        id = "hello"
        n = MorphState(0)

        def render(self):
            return div(span(str(int(self.n or 0))), id=self.id)

        @action(caps=())
        def inc(self):
            self.n = int(self.n or 0) + 1
            return update_with(self)

    inst = Hello()
    wrap = brand_wrap(Document(head=[], body=[], ensure_csrf_token=False), brand=BRAND)
    wrapped = _html(wrap(inst.render()))
    assert wrapped.count(BRAND) == 1
    html, _target = morph_html_and_target(update_with(inst))
    assert html.count(BRAND) == 0
    assert GET_CHROME_ATTR not in html
    assert "nav" not in html.lower() or 'id="hello"' in html
    assert BRAND not in _html(inst.render())
