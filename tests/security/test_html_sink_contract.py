"""One closed type contract at every HTML sink (``ux_compose.dom.html_value``).

trusted    ``__html__`` (Markup) and real ux-dom trees, rendered by ux-dom
sanitized  ``str``, and ``bytes`` as strict UTF-8, through ``sanitize_html``
``None``   empty HTML
otherwise  ``TypeError`` naming the sink (no ``str()`` coercion); bytes that
           are not UTF-8 raise ``ValueError``

Every value type below goes through every sink: route body and stream chunk
(both hosts), ``render()``, ``update_with(html=)``, ``ux_behavior.update``,
``morph`` / ``swap`` ops, motion ``enter`` html, ``brand_wrap``. The
reviewer's repros (#143 round 3) are rows here: list / tuple / dict /
``__str__`` objects to ``update()``, and ``bytes`` / list / ``__str__``
objects from ``render()``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from markupsafe import Markup
from ux_behavior import update
from ux_dom import Document
from ux_dom.dom import div
from ux_dom.response import sanitize_html, to_html_bytes

from tests.asgi_http import asgi_get
from ux_compose import Component
from ux_compose.brand import brand_wrap
from ux_compose.helpers import update_with
from ux_compose.wire.caps import ops_to_wire

ATTACK = '<b onmouseover="alert(1)">x</b><img src=x onerror=alert(2)>'
SANITIZED = sanitize_html(ATTACK)
TREE_ATTRS = {"hx-post": "/x", "x-data": "{open: false}"}


class Shown:
    """``__str__`` returns HTML: must not be trusted, or coerced."""

    def __str__(self) -> str:
        return ATTACK


def _tree():
    return div("t", id="t", **TREE_ATTRS)


TREE_HTML = to_html_bytes(_tree()).decode("utf-8")

# name -> (value factory, expected html | exception type)
CASES = {
    "str": (lambda: ATTACK, SANITIZED),
    "bytes": (lambda: ATTACK.encode(), SANITIZED),
    "bytearray": (lambda: bytearray(ATTACK.encode()), SANITIZED),
    "bad_bytes": (lambda: b"\xff<b>x</b>", ValueError),
    "markup": (lambda: Markup(ATTACK), ATTACK),
    "tree": (_tree, TREE_HTML),
    "none": (lambda: None, ""),
    "list": (lambda: [ATTACK], TypeError),
    "tuple": (lambda: (ATTACK,), TypeError),
    "dict": (lambda: {"html": ATTACK}, TypeError),
    "int": (lambda: 5, TypeError),
    "str_object": (Shown, TypeError),
}


class C(Component):
    id = "c"
    value = None

    def render(self):
        return type(self).value


def _render(value):
    C.value = value
    return C().__render__()


def _update_with(value):
    if value is None:
        pytest.skip("html=None means: render the component")
    return ops_to_wire(update_with(C(), html=value))[0]["html"]


def _update(value):
    return ops_to_wire([update("#c", value)])[0]["html"]


def _morph_op(value):
    return ops_to_wire([{"op": "morph", "target": "#c", "html": value}])[0]["html"]


def _swap_op(value):
    return ops_to_wire([{"op": "swap", "target": "#c", "html": value}])[0]["html"]


def _motion(value):
    if value is None:
        pytest.skip("a track without html is not an HTML sink")
    plan = {"kind": "plan", "tracks": [{"target": "#c", "role": "enter", "html": value}]}
    return ops_to_wire([{"op": "transition.play", "plan": plan}])[0]["plan"]["tracks"][0]["html"]


def _brand(value):
    page = to_html_bytes(brand_wrap(Document(head=[], body=[], ensure_csrf_token=False))(value))
    return page.decode("utf-8")


# sink -> (call, name in the error, output contains rather than equals)
SINKS = {
    "render": (_render, "C.render()", False),
    "update_with": (_update_with, "update_with(html=)", False),
    "update": (_update, "morph html", False),
    "morph_op": (_morph_op, "morph op html", False),
    "swap_op": (_swap_op, "swap op html", False),
    "motion_enter": (_motion, "motion enter html", False),
    "brand_wrap": (_brand, "brand_wrap child", True),
}


@pytest.mark.parametrize("sink", SINKS)
@pytest.mark.parametrize("case", CASES)
def test_every_type_at_every_python_sink(sink, case):
    call, label, contains = SINKS[sink]
    make, expected = CASES[case]
    if isinstance(expected, type):
        with pytest.raises(expected) as info:
            call(make())
        assert label in str(info.value)
        if expected is TypeError:
            assert type(make()).__name__ in str(info.value)
        return
    out = call(make())
    if contains:
        if case == "tree":
            assert all(f'{k}="{v}"' in out for k, v in TREE_ATTRS.items())
        else:
            assert expected in out
        if case != "markup":
            assert "onmouseover" not in out
    else:
        assert out == expected


# --- routes: body and stream chunk, both hosts --------------------------------

_HEADER = f'''
from markupsafe import Markup
from ux_dom.dom import div

ATTACK = {ATTACK!r}


class Shown:
    def __str__(self):
        return ATTACK


VALUES = {{
    "str": lambda: ATTACK,
    "bytes": lambda: ATTACK.encode(),
    "bytearray": lambda: bytearray(ATTACK.encode()),
    "bad_bytes": lambda: b"\\xff<b>x</b>",
    "markup": lambda: Markup(ATTACK),
    "tree": lambda: div("t", id="t", **{TREE_ATTRS!r}),
    "none": lambda: None,
    "list": lambda: [ATTACK],
    "tuple": lambda: (ATTACK,),
    "dict": lambda: {{"html": ATTACK}},
    "int": lambda: 5,
    "str_object": Shown,
}}
'''

_ROUTES = {
    "body/[name].py": "class Name:\n    def render(self, name='str'):\n        return VALUES[name]()\n",
    "chunk/[name].py": (
        "class Name:\n"
        "    def render(self, name='str'):\n"
        "        def gen():\n"
        "            yield VALUES[name]()\n"
        "        return gen()\n"
    ),
}


@pytest.fixture(scope="module", params=("fastapi", "asgi"))
def routes(request, tmp_path_factory):
    if request.param == "fastapi":
        pytest.importorskip("fastapi")
    from ux_compose.build import build

    pkg = Path(tmp_path_factory.mktemp(request.param)) / f"contract_{request.param}"
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    for rel, src in _ROUTES.items():
        dest = pkg / "routes" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_HEADER + "\n\n" + src, encoding="utf-8")
    _app, asgi, _bundle = build(pkg, name="Contract", host=request.param, live="null", level=1)
    return asgi


@pytest.mark.parametrize("kind", ("body", "chunk"))
@pytest.mark.parametrize("case", CASES)
def test_every_type_at_route_body_and_stream_chunk(routes, kind, case):
    _make, expected = CASES[case]
    try:
        r = asgi_get(routes, f"/{kind}/{case}")
    except (TypeError, ValueError) as exc:
        # FastAPI's ServerErrorMiddleware sends the 500, then re-raises.
        assert isinstance(expected, type) and isinstance(exc, expected), exc
        assert "route" in str(exc)
        return
    if kind == "body" and case == "dict":
        assert r.headers["content-type"].startswith("application/json")  # payload law
        return
    if isinstance(expected, type):
        assert r.status_code == 500, r.text
        assert "onmouseover" not in r.text
        return
    assert r.status_code == 200, r.text
    assert r.text == expected


def test_render_error_names_the_sink_and_type():
    C.value = [ATTACK]
    with pytest.raises(TypeError, match=r"C\.render\(\): HTML must be .* not list"):
        C().__render__()
