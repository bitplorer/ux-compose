"""Cut 1: kit construct props + shell=False usable units.

Isolation: this file never imports ux_channel. No Cap kernel / cek-runtime / law.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.helpers import _serialize_tree
from ux_compose.kit.catalog import CATALOG
from ux_compose.kit.copy import copy_component
from ux_compose.kit.fab import Fab
from ux_compose.kit_construct import Kit, apply_kit_construct


def _html(inst) -> str:
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return _serialize_tree(inst.render())


def test_fab_construct_actions_shell_false_omits_demo_title():
    inst = Fab(actions=(("a", "A"),), shell=False)
    html = _html(inst)
    assert "A new thing" not in html
    assert "Make" not in html
    assert "The round button is the verb" not in html
    assert "A" in html
    assert 'role="menuitem"' in html
    assert 'id="fab"' in html
    assert inst.ACTIONS == (("a", "A"),)
    assert inst.shell is False


def test_fab_zero_arg_keeps_atelier_demo():
    inst = Fab()
    html = _html(inst)
    assert "A new thing" in html
    assert "New note" in html
    assert "New cut" in html
    assert inst.shell is True
    assert inst.ACTIONS == Fab.ACTIONS


def test_fab_unknown_kwarg_fails_closed():
    with pytest.raises(TypeError, match="unexpected construct"):
        Fab(nope=1)


def test_fab_subclass_const_then_instance_wins():
    class Mine(Fab):
        id = "fab"
        ACTIONS = (("x", "X"),)

    plain = Mine()
    assert plain.ACTIONS == (("x", "X"),)
    html = _html(plain)
    assert "X" in html

    inst = Mine(actions=(("z", "Z"),), shell=False)
    assert inst.ACTIONS == (("z", "Z"),)
    html = _html(inst)
    assert "Z" in html
    assert "X" not in html
    assert "A new thing" not in html


def test_fab_behavior_add_zero_arg_still_greens():
    app = App.boot("FabConstruct", strict_caps=False)
    app.add(Fab)
    inst = app.behavior.get("fab")
    html = _html(inst)
    assert "A new thing" in html
    assert "New note" in html
    app.dispatch("fab.toggle")
    html = _html(app.behavior.get("fab"))
    assert "New note" in html


def test_apply_kit_construct_unknown_fails_closed():
    class Probe(Kit):
        id = "probe"
        _SEAMS = {"actions": "ACTIONS"}
        ACTIONS = (("a", "A"),)

        def render(self):
            return ""

    apply_kit_construct(Probe(), seams={"actions": "ACTIONS"})
    with pytest.raises(TypeError, match="unexpected construct"):
        Probe(ghost=True)


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_catalog_zero_arg_still_renders():
    for stem, meta in CATALOG.items():
        if stem in {"overlay"}:
            continue
        mod = __import__(meta["module"], fromlist=[meta["name"]])
        cls = getattr(mod, meta["name"])
        inst = cls()
        tree = inst.render()
        assert tree is not None, stem
        html = _serialize_tree(tree)
        assert f'id="{cls.id}"' in html, stem


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_add_fab_unchanged(tmp_path: Path):
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    written = copy_component("fab", root=tmp_path)
    text = written["py"].read_text(encoding="utf-8")
    ast.parse(text)
    assert written["css"] is None
    assert written["base"] is None
    assert "from ux_compose.kit import" not in text
    assert "ux_channel" not in text
    assert not (tmp_path / "components" / "base.py").exists()


def test_kit_construct_never_imports_ux_channel():
    path = ROOT / "src" / "ux_compose" / "kit_construct.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("ux_channel", "cek_runtime", "cek_host")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(f) for f in forbidden)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(f) for f in forbidden)
