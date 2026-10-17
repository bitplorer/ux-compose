"""Kit Batch A presence P1: menubar, toolbar, toggle-group, spinbutton,
theme-switch, filterbar.

Isolation: this file never imports ux_channel. No Cap kernel / cek-runtime / law.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.cli.registry import CATALOG, resolve
from ux_compose.cli.copy_component import copy_component


KIT_DIR = ROOT / "src" / "ux_compose" / "components"

CHROME_A = (
    "menubar",
    "toolbar",
    "togglegroup",
    "spinbutton",
    "themeswitch",
    "filterbar",
)

# Cap names are labels: the runtime gates on "caps non-empty", never on the
# name (ux_behavior/root.py:_require_caps; ux-channel binds tokens to the
# action name). So the policy checks shape + fail-closed behaviour, not a
# hard-coded list of namespaces.
CAP_SHAPE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


def _boot(*classes, **kwargs):
    app = App.boot("KitChromeA", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def _cls(stem: str):
    meta = CATALOG[stem]
    mod = __import__(meta["module"], fromlist=[meta["name"]])
    return getattr(mod, meta["name"])


def _action_caps(path: Path) -> list[tuple[str, tuple[str, ...]]]:
    """Return (function_name, caps) for every @action on a kit module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[str, tuple[str, ...]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            fn = dec.func
            name = ""
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if name != "action":
                continue
            caps: tuple[str, ...] = ()
            for kw in dec.keywords:
                if kw.arg != "caps":
                    continue
                val = kw.value
                if isinstance(val, ast.Tuple):
                    caps = tuple(
                        elt.value
                        for elt in val.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    )
                elif isinstance(val, ast.Constant) and val.value == ():
                    caps = ()
            found.append((node.name, caps))
    return found


def test_presence_a_stems_resolve():
    for stem in CHROME_A:
        meta = resolve(stem)
        assert meta["stem"] == stem
        assert meta["css"] is False
        assert meta["page"] is True
        assert meta["module"] == f"ux_compose.components.{stem}"
    assert resolve("toggle-group")["stem"] == "togglegroup"
    assert resolve("theme-switch")["stem"] == "themeswitch"
    assert resolve("spin-button")["stem"] == "spinbutton"
    assert resolve("filter-bar")["stem"] == "filterbar"
    assert resolve("menu-bar")["stem"] == "menubar"


def test_presence_a_render_document_trees():
    from ux_compose.helpers import _serialize_tree

    for stem in CHROME_A:
        cls = _cls(stem)
        tree = cls().render()
        assert not isinstance(tree, str), stem
        html = _serialize_tree(tree)
        assert f'id="{cls.id}"' in html, stem
        lower = html.lower()
        assert "<html" not in lower
        assert "<!doctype" not in lower
        assert "ux_channel" not in html


def test_menubar_apg_and_choose():
    Menubar = _cls("menubar")
    app = _boot(Menubar, strict_caps=False)
    html = _html(app, "menubar")
    assert 'role="menubar"' in html
    assert 'aria-label="Desk"' in html or "aria-label=" in html
    assert 'role="menuitem"' in html
    assert "aria-haspopup" in html
    assert 'aria-expanded="false"' in html
    assert 'id="menubar-file"' in html
    assert 'aria-controls="menubar-m-file"' in html
    assert "File" in html
    # Closed: every submenu id stays in the tree (tabs-before-#60 dangling-id hole).
    assert 'id="menubar-m-file"' in html
    assert 'id="menubar-m-edit"' in html
    assert 'id="menubar-m-view"' in html
    assert html.count('role="menu"') == 3
    assert "hidden" in html

    app.dispatch("menubar.open_menu", key="file")
    html = _html(app, "menubar")
    assert 'aria-expanded="true"' in html
    assert 'id="menubar-m-file"' in html
    assert 'id="menubar-m-edit"' in html
    assert 'role="menu"' in html
    assert "New desk" in html
    assert "keydown.escape" in html

    app.dispatch("menubar.choose", menu="file", item="new")
    inst = app.behavior.get("menubar")
    assert str(inst.value) == "new"
    assert str(inst.open or "") == ""
    html = _html(app, "menubar")
    assert 'data-value="new"' in html
    assert 'aria-expanded="false"' in html
    assert 'id="menubar-m-file"' in html
    assert 'id="menubar-m-edit"' in html
    assert 'id="menubar-m-view"' in html


def test_toolbar_apg_and_run():
    Toolbar = _cls("toolbar")
    app = _boot(Toolbar, strict_caps=False)
    html = _html(app, "toolbar")
    assert 'role="toolbar"' in html
    assert "aria-label" in html
    assert 'role="separator"' in html
    assert 'role="group"' in html
    assert "toolbar.run" in html
    assert "New" in html

    app.dispatch("toolbar.run", key="undo")
    inst = app.behavior.get("toolbar")
    assert str(inst.value) == "undo"
    html = _html(app, "toolbar")
    assert 'data-value="undo"' in html
    assert "aria-pressed" not in html
    assert 'aria-current="true"' in html


def test_togglegroup_radiogroup_exclusive():
    ToggleGroup = _cls("togglegroup")
    app = _boot(ToggleGroup, strict_caps=False)
    html = _html(app, "togglegroup")
    assert 'role="radiogroup"' in html
    assert 'role="radio"' in html
    assert "aria-checked" in html
    assert "aria-labelledby" in html
    assert 'id="togglegroup-opt-week"' in html or "Week" in html

    app.dispatch("togglegroup.choose", key="month")
    inst = app.behavior.get("togglegroup")
    assert str(inst.value) == "month"
    html = _html(app, "togglegroup")
    assert 'aria-checked="true"' in html
    assert 'data-value="month"' in html
    app.dispatch("togglegroup.choose", key="nope")
    assert str(inst.value) == "day"


def test_spinbutton_refstate_not_morph_quantity():
    SpinButton = _cls("spinbutton")
    app = _boot(SpinButton, strict_caps=False)
    html = _html(app, "spinbutton")
    assert 'role="spinbutton"' in html
    assert "aria-valuenow" in html
    assert "aria-valuemin" in html
    assert "aria-valuemax" in html
    assert 'for="spinbutton-value"' in html or 'id="spinbutton-value"' in html
    assert "aria-labelledby" in html

    inst = app.behavior.get("spinbutton")
    assert int(inst.value or 0) == 2
    app.dispatch("spinbutton.inc")
    assert int(inst.value) == 3
    html = _html(app, "spinbutton")
    assert 'aria-valuenow="3"' in html
    app.dispatch("spinbutton.dec")
    app.dispatch("spinbutton.dec")
    app.dispatch("spinbutton.dec")
    assert int(inst.value) == 1
    app.dispatch("spinbutton.set_value", value="9")
    assert int(inst.value) == 9
    app.dispatch("spinbutton.inc")
    assert int(inst.value) == 9


def test_themeswitch_named_not_boolean_switch():
    ThemeSwitch = _cls("themeswitch")
    app = _boot(ThemeSwitch, strict_caps=False)
    html = _html(app, "themeswitch")
    assert 'role="radiogroup"' in html
    assert 'role="radio"' in html
    assert 'role="switch"' not in html
    assert "Light" in html and "Dark" in html and "System" in html
    assert 'data-theme="light"' in html

    app.dispatch("themeswitch.choose", key="dark")
    inst = app.behavior.get("themeswitch")
    assert str(inst.value) == "dark"
    html = _html(app, "themeswitch")
    assert 'data-theme="dark"' in html
    assert 'aria-checked="true"' in html


def test_filterbar_labeled_query_and_named_filter():
    FilterBar = _cls("filterbar")
    app = _boot(FilterBar, strict_caps=False)
    html = _html(app, "filterbar")
    assert 'role="search"' in html or 'role="toolbar"' in html
    assert 'for="filterbar-q"' in html or 'id="filterbar-q"' in html
    assert 'role="radiogroup"' in html
    assert "Linen" in html
    assert 'tabindex="0"' in html
    assert 'tabindex="-1"' in html

    app.dispatch("filterbar.choose", key="oak")
    inst = app.behavior.get("filterbar")
    assert str(inst.which) == "oak"
    html = _html(app, "filterbar")
    assert 'data-filter="oak"' in html
    assert "Oak serving board" in html
    assert "Linen work shirt" not in html

    app.dispatch("filterbar.choose", key="all")
    app.dispatch("filterbar.set_field", field="q", value="wool")
    html = _html(app, "filterbar")
    assert "Wool throw" in html
    assert "Oak serving board" not in html


def test_a11y_smoke_presence_a():
    app = _boot(*[_cls(s) for s in CHROME_A], strict_caps=False)
    menubar = _html(app, "menubar")
    assert 'role="menubar"' in menubar
    assert 'aria-controls="menubar-m-file"' in menubar
    assert 'id="menubar-m-file"' in menubar
    assert 'id="menubar-m-edit"' in menubar
    assert 'id="menubar-m-view"' in menubar
    app.dispatch("menubar.open_menu", key="edit")
    menubar = _html(app, "menubar")
    assert 'id="menubar-m-edit"' in menubar
    assert 'id="menubar-m-file"' in menubar
    assert 'role="menu"' in menubar

    toolbar = _html(app, "toolbar")
    assert 'role="toolbar"' in toolbar
    assert 'role="separator"' in toolbar
    assert "aria-pressed" not in toolbar

    group = _html(app, "togglegroup")
    assert 'role="radiogroup"' in group
    assert 'role="radio"' in group
    assert "aria-labelledby" in group

    spin = _html(app, "spinbutton")
    assert 'role="spinbutton"' in spin
    assert 'id="spinbutton-value"' in spin
    assert "aria-valuenow" in spin

    theme = _html(app, "themeswitch")
    assert 'role="radiogroup"' in theme
    assert 'role="switch"' not in theme

    filt = _html(app, "filterbar")
    assert 'id="filterbar-q"' in filt
    assert 'role="radiogroup"' in filt
    assert 'tabindex="0"' in filt
    assert 'tabindex="-1"' in filt


def test_presence_a_caps_are_empty():
    for stem in CHROME_A:
        path = KIT_DIR / f"{stem}.py"
        for fn, caps in _action_caps(path):
            assert caps == (), f"{stem}.{fn} spent {caps}; presence A is public"


def _runtime_actions():
    """(stem, cls, method_name, caps) from @action runtime metadata, every component."""
    import importlib
    import inspect

    from ux_compose import Component

    for path in sorted(KIT_DIR.glob("*.py")):
        if path.stem == "__init__":
            continue
        mod = importlib.import_module(f"ux_compose.components.{path.stem}")
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if cls.__module__ != mod.__name__ or not issubclass(cls, Component):
                continue
            for name, fn in vars(cls).items():
                if getattr(fn, "_ux_behavior_action", False):
                    caps = tuple(getattr(fn, "_ux_behavior_caps", ()) or ())
                    yield path.stem, cls, name, caps


def test_kit_caps_are_well_formed():
    """Every declared cap (runtime metadata) is a lowercase ``namespace.verb`` label."""
    rows = list(_runtime_actions())
    assert rows, "no @action metadata found"
    bad = [f"{s}.{n} cap {c!r}" for s, _, n, caps in rows for c in caps if not CAP_SHAPE.match(c)]
    assert not bad, bad
    capped = {s for s, _, _, caps in rows if caps}
    for stem in CHROME_A:
        assert stem not in capped


def test_kit_capped_actions_fail_closed_at_runtime():
    """Live: with the default App.boot(), every capped action refuses an untrusted call."""
    from ux_behavior import AuthorityError

    capped = [(s, c, n) for s, c, n, caps in _runtime_actions() if caps]
    assert capped, "no capped actions found"
    for stem, cls, fn in capped:
        app = App.boot(f"Cap_{stem}")
        app.add(cls)
        with pytest.raises(AuthorityError):
            app.dispatch(f"{cls.id}.{fn}")


def test_kit_modules_never_import_ux_channel():
    forbidden = ("ux_channel", "cek_runtime", "cek_host")
    for path in sorted(KIT_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(alias.name.startswith(f) for f in forbidden), path
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not any(node.module.startswith(f) for f in forbidden), path


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_copy_presence_a_stems(tmp_path: Path):
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    for stem in CHROME_A:
        written = copy_component(stem, root=tmp_path)
        assert written["py"].is_file(), stem
        ast.parse(written["py"].read_text(encoding="utf-8"))
        assert "from ux_compose.components import" not in written["py"].read_text(encoding="utf-8")
        assert "ux_channel" not in written["py"].read_text(encoding="utf-8")
