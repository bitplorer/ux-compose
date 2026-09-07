"""GET-only chrome: brand on Clock A GET, never inside update_with morph HTML."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None

from ux_compose.chrome import (
    DEFAULT_BRAND,
    GET_CHROME_ATTR,
    get_chrome,
    wrap_get_chrome,
)
from ux_compose.helpers import update_with
from ux_compose.routing.core import apply_html_document

from tests.asgi_http import asgi_get
from tests.feature.morph import morph_html_and_target

ROOT = Path(__file__).resolve().parents[2]
BRAND = "AcmeBrand"


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


def test_chrome_source_does_not_import_ux_channel_or_document():
    src = (ROOT / "src" / "ux_compose" / "chrome.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("ux_channel")
                assert alias.name != "ux_dom"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("ux_channel")
            assert mod != "ux_dom"
            assert not mod.startswith("ux_dom.")
    assert "Document(" not in src


def test_wrap_get_chrome_puts_brand_once_around_fragment():
    inner = '<div id="hello"><span>hi</span></div>'
    html = wrap_get_chrome(inner, brand=BRAND)
    assert isinstance(html, str)
    assert html.count(BRAND) == 1
    assert GET_CHROME_ATTR in html
    assert 'class="nav"' in html
    assert 'class="brand"' in html
    assert 'id="hello"' in html
    assert "stunning-root" not in html
    assert "Document" not in html


def test_wrap_get_chrome_default_brand_and_empty_inner():
    html = wrap_get_chrome()
    assert html.count(DEFAULT_BRAND) == 1
    assert GET_CHROME_ATTR in html


def test_get_chrome_factory_is_wrap_callable():
    wrap = get_chrome(brand=BRAND)
    html = wrap('<div id="hello">x</div>')
    assert html.count(BRAND) == 1
    assert apply_html_document(wrap, '<div id="hello">x</div>').count(BRAND) == 1


def test_apply_html_document_string_shell_keeps_fragment():
    out = apply_html_document(
        get_chrome(brand=BRAND),
        '<div id="hello">hi</div>',
    )
    assert isinstance(out, str)
    assert out.count(BRAND) == 1
    assert "hi" in out
    assert 'id="hello"' in out


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi")
def test_build_wrap_get_html_has_brand_once_morph_has_zero(tmp_path: Path):
    pkg = _pkg(
        tmp_path,
        {
            "routes/hello.py": (
                "from ux_compose import Component, MorphState, action, update_with\n"
                "\n"
                "class Hello(Component):\n"
                "    id = 'hello'\n"
                "    n = MorphState(0)\n"
                "\n"
                "    def render(self):\n"
                "        n = int(self.n or 0)\n"
                "        return f'<div id=\"hello\"><span>{n}</span></div>'\n"
                "\n"
                "    @action(caps=())\n"
                "    def inc(self):\n"
                "        self.n = int(self.n or 0) + 1\n"
                "        return update_with(self)\n"
            )
        },
    )
    from ux_compose.build import build

    app, asgi, _bundle = build(
        pkg,
        name="Demo",
        host="fastapi",
        live="null",
        level=1,
        document=None,
        wrap=get_chrome(brand=BRAND),
    )
    r = asgi_get(asgi, "/hello")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert r.text.count(BRAND) == 1
    assert GET_CHROME_ATTR in r.text
    assert 'id="hello"' in r.text

    ops = app.dispatch("hello.inc")
    morph, target = morph_html_and_target(ops)
    assert "#hello" in (target or "#hello")
    assert morph.count(BRAND) == 0
    assert GET_CHROME_ATTR not in morph
    assert "stunning-root" not in morph
    assert 'id="hello"' in morph


def test_update_with_fragment_never_includes_wrap_brand():
    from ux_compose import Component, MorphState, action

    class Hello(Component):
        id = "hello"
        n = MorphState(0)

        def render(self):
            return f'<div id="hello"><span>{int(self.n or 0)}</span></div>'

        @action(caps=())
        def inc(self):
            self.n = int(self.n or 0) + 1
            return update_with(self)

    inst = Hello()
    wrapped = wrap_get_chrome(inst.render(), brand=BRAND)
    assert wrapped.count(BRAND) == 1
    html, _target = morph_html_and_target(update_with(inst))
    assert html.count(BRAND) == 0
    assert GET_CHROME_ATTR not in html
