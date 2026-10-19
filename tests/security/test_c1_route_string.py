"""C1: a route or fragment string is HTML, with runnable constructs dropped.

Kept today (and after the fix): a tag tree, ``markupsafe.Markup``, and an
explicit ux-dom ``raw()`` node stay verbatim. A plain ``str`` is the hole —
``routing/core.py`` ``_document_child``, ``brand.py`` ``_as_child`` and
``helpers.py`` ``_serialize_tree`` put it in the DOM unchanged, so
``<img src=x onerror=...>`` runs when the page has no CSP.

The plain-str test is the live check (apps/compose_c1, routes/[sku].py,
document + brand_wrap and no Document). It fails while that hole is open.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from ux_compose import Component, div, raw, span
from ux_compose.brand import _as_child, brand_wrap
from ux_compose.helpers import _serialize_tree
from ux_compose.routing.core import _document_child, apply_html_document

from tests.asgi_http import asgi_get

# Live payload from the C1 confirmation script.
PAY = '<img src=x onerror="window.PWN=1">'
# Same door, rest of the F-03 set (script, Alpine, javascript: URL).
RICH = (
    PAY
    + "<script>alert(1)</script>"
    + '<div x-init="pwn">x</div>'
    + '<a href="javascript:alert(1)">j</a>'
    + '<p>safe</p><a href="/shop">go</a>'
)
SAFE = '<p>hello</p><a href="/shop">go</a>'


def _html(value) -> str:
    """HTML a host would send. Strings pass through; trees use the product serializer."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "".join(_html(item) for item in value)
    return _serialize_tree(value)


def _pkg(tmp_path: Path, files: dict[str, str], name: str) -> Path:
    pkg = tmp_path / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    for rel, src in files.items():
        dest = pkg / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src, encoding="utf-8")
    return pkg


def _runnable(html: str) -> list[str]:
    """Constructs the F-03 path must drop. Empty means the string is safe markup."""
    found = []
    for needle in ("onerror", "<script", "x-init", "javascript:"):
        if needle in html.lower():
            found.append(needle)
    return found


def test_tag_tree_return_stays_markup():
    """Author tag trees are not re-parsed."""
    from ux_dom import Document

    tree = div(span("hi"), id="hello")
    doc = Document(head=[], body=[], ensure_csrf_token=False)
    wrapped = _html(apply_html_document(doc, tree))
    branded = _html(brand_wrap(doc, brand="Acme")(tree))
    fragment = _serialize_tree(tree)
    for html in (wrapped, branded, fragment):
        assert 'id="hello"' in html
        assert "hi" in html
    assert "Acme" in branded

    class Hello(Component):
        def render(self):
            return div(span("hi"), id="hello")

    rendered = Hello().__render__()
    assert 'id="hello"' in rendered
    assert "hi" in rendered


def test_markupsafe_markup_stays_verbatim():
    """An explicit Markup string is the trusted opt-out, same as raw()."""
    from markupsafe import Markup
    from ux_dom import Document

    marked = Markup(PAY)
    doc = Document(head=[], body=[], ensure_csrf_token=False)
    surfaces = (
        _html(_document_child(marked)),
        _html(_as_child(marked)),
        _serialize_tree(marked),
        _html(apply_html_document(doc, marked)),
        _html(brand_wrap(doc, brand="Acme")(marked)),
    )
    for html in surfaces:
        assert "onerror" in html
        assert "window.PWN=1" in html

    class Trusted(Component):
        def render(self):
            return Markup(PAY)

    assert "onerror" in Trusted().__render__()


def test_explicit_raw_node_stays_verbatim():
    """An explicit ux-dom raw() node is not parsed or sanitized."""
    from ux_dom import Document

    node = raw(PAY)
    doc = Document(head=[], body=[], ensure_csrf_token=False)
    surfaces = (
        _html(_document_child(node)),
        _html(_as_child(node)),
        _serialize_tree(node),
        _html(apply_html_document(doc, node)),
        _html(brand_wrap(doc, brand="Acme")(node)),
    )
    for html in surfaces:
        assert "onerror" in html
        assert "window.PWN=1" in html

    class RawFragment(Component):
        def render(self):
            return raw(PAY)

    assert "onerror" in RawFragment().__render__()


def test_plain_safe_html_string_stays_markup():
    """A plain string stays HTML markup, not escaped text."""
    from ux_dom import Document

    doc = Document(head=[], body=[], ensure_csrf_token=False)
    surfaces = (
        _html(_document_child(SAFE)),
        _html(_as_child(SAFE)),
        _serialize_tree(SAFE),
        _html(apply_html_document(doc, SAFE)),
        _html(brand_wrap(doc, brand="Acme")(SAFE)),
    )
    for html in surfaces:
        assert "<p" in html
        assert "hello" in html
        assert "/shop" in html
        assert "go" in html
        assert "&lt;p" not in html


def test_plain_string_helpers_and_fragment_drop_runnable_constructs():
    """Plain str through the three helpers and a fragment render is sanitized."""
    for label, html in (
        ("_document_child", _html(_document_child(RICH))),
        ("_as_child", _html(_as_child(RICH))),
        ("_serialize_tree", _html(_serialize_tree(RICH))),
    ):
        assert _runnable(html) == [], label
        assert "<img" in html, label
        assert 'src="x"' in html or "src=x" in html, label
        assert "safe" in html, label
        assert "/shop" in html, label

    class Frag(Component):
        def render(self):
            return RICH

    fragment = Frag().__render__()
    assert _runnable(fragment) == []
    assert "<img" in fragment
    assert "safe" in fragment


@pytest.mark.parametrize(
    "label",
    ["no document", "document + brand_wrap"],
)
def test_live_route_string_drops_runnable_constructs(tmp_path: Path, label: str):
    """Live C1: GET /<img onerror> on routes/[sku].py. Fails while the hole is open.

    Same shape as the confirmation script: no Document, and document + brand_wrap.
    """
    pytest.importorskip("fastapi")
    from ux_dom import Document
    from ux_compose.build import build

    sku_route = (
        "class Sku:\n"
        "    def render(self, sku='x'):\n"
        '        return f\'<div id="sku">{sku}</div>\'\n'
    )
    kw: dict = {}
    if label == "document + brand_wrap":
        doc = Document(head=[], body=[], ensure_csrf_token=False)
        kw = {"document": doc, "wrap": brand_wrap(doc, brand="Acme")}
    # ASGI scope["path"] is percent-decoded (the live script's HTTP client
    # decodes before the route sees ``sku``).
    pkg = _pkg(tmp_path, {"routes/[sku].py": sku_route}, name="skuapp")
    _app, asgi, _bundle = build(
        pkg, name="C1", host="fastapi", live="null", level=1, **kw
    )
    response = asgi_get(asgi, "/" + PAY)
    assert response.status_code == 200, label
    assert "text/html" in response.headers.get("content-type", ""), label
    assert _runnable(response.text) == [], label
    assert 'id="sku"' in response.text, label
    assert "<img" in response.text, label
    if kw:
        assert "Acme" in response.text, label


def test_plain_string_route_bytes_drop_runnable_constructs():
    """bytes are decoded HTML, same door as str."""
    html = _html(_document_child(PAY.encode("utf-8")))
    assert _runnable(html) == []
    assert "<img" in html
