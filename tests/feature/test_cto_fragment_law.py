"""CTO gate 3: update_with / morph HTML fragment law.

Morph payload for target #X must not embed outer shell / brand chrome.

Nested-shell tests characterize FullShellHello (full shell in render(),
update_with targets #hello). Helpers must emit the #hello subtree — do not
rewrite the fixture into a fragment. Official scaffold hello stays a
fragment. Product floor is Python ≥3.14 with ux-dom.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import update_with
from ux_compose.scaffold import ROUTES_HELLO_PY, create_app

from tests.feature.morph import (
    KERNEL_SSOT_ID,
    SHELL_BRAND,
    SHELL_ROOT_ID,
    assert_html_is_fragment,
    assert_morph_fragment,
    first_id,
    morph_html_and_target,
)
from tests.feature.stunning_shell import (
    HELLO_ID,
    FragmentHello,
    FullShellHello,
    stunning_full_shell_html,
)

HAS_BEHAVIOR = importlib.util.find_spec("ux_behavior") is not None
HAS_DOM = importlib.util.find_spec("ux_dom") is not None
_DOM_TREES = sys.version_info >= (3, 14) and HAS_DOM


def _load_hello(root: Path):
    path = root / "routes" / "hello.py"
    spec = importlib.util.spec_from_file_location("cto_fragment_hello", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixture_mirrors_full_shell_in_render_pattern():
    """Stand-in for stunning/routes/hello.py:41-72 — full shell, not a fragment."""
    html = FullShellHello().render()
    assert isinstance(html, str)
    assert html == stunning_full_shell_html(0)
    assert first_id(html) == SHELL_ROOT_ID
    assert SHELL_BRAND in html
    assert KERNEL_SSOT_ID in html
    assert f'id="{HELLO_ID}"' in html


def test_fragment_law_correct_fragment_component_morph_has_no_shell_chrome():
    inst = FragmentHello()
    inst.n = 3
    ops = update_with(inst)
    html = assert_morph_fragment(ops, target_id=HELLO_ID)
    assert "3" in html
    assert SHELL_ROOT_ID not in html
    assert SHELL_BRAND not in html


def test_fragment_law_scaffold_hello_morph_stays_fragment(tmp_path):
    """Official create-app Hello: update_with HTML is the #hello fragment."""
    root = create_app(tmp_path / "frag", name="frag", level=1, host="asgi")
    hello_src = (root / "routes" / "hello.py").read_text(encoding="utf-8")
    assert hello_src.strip() == ROUTES_HELLO_PY.strip() or "id=\"hello\"" in hello_src
    mod = _load_hello(root)
    inst = mod.Hello()
    inst.n = 1
    ops = update_with(inst)
    html, target = morph_html_and_target(ops)
    assert "#hello" in (target or "#hello")
    if not isinstance(inst.render(), str):
        from ux_compose.algebra import _serialize_tree

        html = html or _serialize_tree(inst.render())
    assert_html_is_fragment(html, target_id=HELLO_ID)


@pytest.mark.cto_red
def test_fragment_law_nested_shell_morph_html_must_not_embed_outer_brand_chrome():
    """FullShellHello stays a full-shell fixture; morph payload must be #hello.

    Smoking gun: FullShellHello.render() is ``<div id="stunning-root">…brand
    StunningCek…`` while update_with targets ``#hello``. helpers must emit the
    #hello subtree, not the outer shell (live StunningCek nested brand +
    kernel_ssot on each click). Do not rewrite this fixture into a fragment.
    """
    inst = FullShellHello()
    inst.n = 3
    ops = update_with(inst)
    html, target = morph_html_and_target(ops)
    tid = target if str(target).startswith("#") else f"#{target}" if target else "#hello"
    assert tid == "#hello", f"update_with must target #hello, got {target!r}"
    assert html.strip(), f"morph HTML missing: {ops!r}"
    # Nested-shell / fragment-law assertion (RED on full-shell-in-render):
    assert_html_is_fragment(html, target_id=HELLO_ID)
    assert html.count(SHELL_BRAND) == 0
    assert html.count(SHELL_ROOT_ID) == 0


@pytest.mark.skipif(not HAS_BEHAVIOR, reason="ux-behavior")
@pytest.mark.cto_red
def test_fragment_law_nested_shell_dispatch_morph_must_not_embed_outer_brand_chrome():
    """Same fragment law via App.dispatch against the full-shell fixture."""
    from ux_compose import App

    app = App.boot("StunningPattern", strict_caps=False)
    app.add(FullShellHello)
    ops = app.dispatch("hello.inc")
    html, target = morph_html_and_target(ops)
    if target:
        got = target if str(target).startswith("#") else f"#{target}"
        assert got == "#hello"
    assert_html_is_fragment(html, target_id=HELLO_ID)


@pytest.mark.skipif(
    not _DOM_TREES,
    reason="Morph/L3 DOM trees require Python ≥3.14 + ux-dom",
)
def test_fragment_law_dom_tree_scaffold_hello_skips_below_314():
    """Py3.14-only: tag-tree Hello still morphs as a #hello fragment."""
    from ux_compose import Component, MorphState, action, div, span, update_with as uw

    class TreeHello(Component):
        id = "hello"
        n = MorphState(0)

        def render(self):
            return div(span(str(int(self.n or 0))), id=self.id)

        @action(caps=())
        def inc(self):
            return uw(self)

    ops = uw(TreeHello())
    assert_morph_fragment(ops, target_id="hello")
