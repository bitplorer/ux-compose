"""RED spec — retire ``ux_compose.kit`` (spec §5b).

Target:
- every widget is defined in ``ux_compose/components/<slug>.py``;
- ``ux_compose.kit`` is deleted (no shim: the package was never on PyPI);
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
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "ux_compose"


def _kit_public_classes():
    import ux_compose.components as kit
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


def test_kit_package_is_gone():
    try:
        kit = importlib.import_module("ux_compose.kit")
    except ModuleNotFoundError:
        pass
    else:  # stale empty dir => namespace package with no code
        assert kit.__spec__.origin is None
    for name, cls in _kit_public_classes().items():
        assert cls.__module__.startswith("ux_compose.components."), name
    assert list((SRC / "kit").rglob("*.py")) == []


def test_verb_named_helpers_exist_without_kit_construct():
    from ux_compose import arrange

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("ux_compose.kit_construct")
    assert callable(arrange.arrange_slots) and callable(arrange.wrap_in_card)
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
def test_tooling_moved_out_without_shim(new, old, names):
    mod_new = importlib.import_module(new)
    for n in names:
        assert hasattr(mod_new, n), n
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(old)

def test_add_copies_from_components_without_kit_imports(tmp_path):
    from ux_compose.cli.copy_component import copy_component

    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    written = copy_component("tabs", root=tmp_path)
    text = written["py"].read_text(encoding="utf-8")
    import re

    assert not re.search(r"ux_compose\.kit", text)


def test_add_copy_imports_match_canonical_component(tmp_path):
    """components/ is canonical (Q13): the copy imports exactly what the
    canonical component imports (verb helpers from ux_compose.arrange), and
    never the removed kit/ package or kit_construct.

    The base deferred ``from ux_compose.arrange import`` while components
    still imported the kit_construct shim. This branch deleted kit/ and
    kit_construct.py, so the copy must import arrange and must not mention
    kit_construct.
    """
    import re

    from ux_compose.cli.copy_component import copy_component

    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    text = copy_component("tabs", root=tmp_path)["py"].read_text(encoding="utf-8")
    canonical = (SRC / "components" / "tabs.py").read_text(encoding="utf-8")

    def imports(src):
        return [line for line in src.splitlines() if re.match(r"(from|import) ux_compose\b", line)]

    assert imports(text) == imports(canonical)
    assert "from ux_compose.arrange import" in text
    assert not re.search(r"\bux_compose\.kit\b(?!_)", text)
    assert "kit_construct" not in text
