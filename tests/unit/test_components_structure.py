"""RED spec — retire ``ux_compose.kit`` (spec §5b).

Target:
- every widget is defined in ``ux_compose/components/<slug>.py``;
- ``ux_compose.kit`` becomes a re-export shim that emits DeprecationWarning
  for one release, then is deleted;
- repeated widget scaffolding lives in verb-named helpers in
  ``ux_compose/arrange.py``: arrange_slots, wrap_in_card, build_heading;
- the registry/copier leave the widget package: ``ux_compose.cli.registry``,
  ``ux_compose.cli.copy_component``;
- ``uxcompose add`` copies from components/ and the copy imports no ``kit``.
GUARD tests already pass on main.
"""
from __future__ import annotations

import ast
import importlib
import sys
import warnings
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "ux_compose"


def _kit_public_classes():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import ux_compose.kit as kit
    return {n: getattr(kit, n) for n in kit.__all__ if isinstance(getattr(kit, n), type)}


def test_public_kit_surface_unchanged():  # GUARD
    assert len(_kit_public_classes()) >= 81


def test_every_module_has_one_line_purpose():  # GUARD
    bad = [
        str(p.relative_to(SRC))
        for p in SRC.rglob("*.py")
        if not (ast.get_docstring(ast.parse(p.read_text(encoding="utf-8"))) or "").strip()
    ]
    assert bad == []


def test_components_package_defines_every_widget():
    from ux_compose.cli.registry import CATALOG

    for slug, meta in CATALOG.items():
        mod = importlib.import_module(f"ux_compose.components.{slug}")
        cls = getattr(mod, meta["name"])
        assert cls.__module__.startswith("ux_compose.components."), slug  # Drawer lives in sheet


def test_kit_is_a_warning_reexport_shim(monkeypatch):
    # monkeypatch restores sys.modules afterwards: no duplicate class identities leak (R1 P1-3)
    for m in [k for k in sys.modules if k == "ux_compose.kit" or k.startswith("ux_compose.kit.")]:
        monkeypatch.delitem(sys.modules, m)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import ux_compose.kit as kit
    assert any(issubclass(x.category, DeprecationWarning) for x in w)
    for name, cls in _kit_public_classes().items():
        assert cls.__module__.startswith("ux_compose.components."), name
    assert len((SRC / "kit" / "__init__.py").read_text(encoding="utf-8").splitlines()) < 60


def test_verb_named_helpers_exist_and_kit_construct_shims_them():
    from ux_compose import arrange, kit_construct

    assert kit_construct.apply_slots is arrange.arrange_slots
    assert kit_construct.kit_shell is arrange.wrap_in_card
    heading = arrange.build_heading("Stage", "Status", "A named chip.")
    html = "".join(str(n) for n in heading)
    assert "Stage" in html and "Status" in html and "A named chip." in html


def test_widgets_use_build_heading_not_inline_preface():
    assert (SRC / "components").is_dir()
    offenders = [
        p.name
        for p in (SRC / "components").glob("*.py")
        if "preface=(" in p.read_text(encoding="utf-8")
    ]
    assert offenders == []


@pytest.mark.parametrize(
    "new, old, names",
    [
        ("ux_compose.cli.registry", "ux_compose.kit.catalog", ("CATALOG", "list_components", "resolve")),
        ("ux_compose.cli.copy_component", "ux_compose.kit.copy", ("copy_component", "KitCopyError", "find_app_root")),
    ],
)
def test_tooling_moved_out_with_shim(new, old, names, monkeypatch):
    mod_new = importlib.import_module(new)
    monkeypatch.delitem(sys.modules, old, raising=False)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mod_old = importlib.import_module(old)
    assert any(issubclass(x.category, DeprecationWarning) for x in w), old
    for n in names:
        assert getattr(mod_old, n) is getattr(mod_new, n), n


def test_add_copies_from_components_without_kit_imports(tmp_path):
    from ux_compose.cli.copy_component import copy_component

    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    written = copy_component("tabs", root=tmp_path)
    text = written["py"].read_text(encoding="utf-8")
    import re

    assert not re.search(r"ux_compose\.kit\b(?!_)", text)  # kit_construct is the Q9 shim


def test_add_copies_import_verb_helpers(tmp_path):
    """Pending Q13: old locks require widgets to import kit_construct."""
    from ux_compose.cli.copy_component import copy_component

    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    text = copy_component("tabs", root=tmp_path)["py"].read_text(encoding="utf-8")
    assert "from ux_compose.arrange import" in text
