"""RED spec — readymade example components live in the kit (spec §4).

Every catalogued example class whose name does not clash with an existing kit
class has a module ``ux_compose/components/<name.lower()>.py`` and a PORTS
entry, so ``uxcompose add <slug>`` drops an ownable copy that runs anywhere —
no ``examples`` import. The 16 name clashes resolved to the kit class (spec Q3):
components/ is canonical and examples/ import every class from it.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

import ux_compose.components as kit
from ux_compose.cli.copy_component import copy_component
from ux_compose.cli.registry import CATALOG, PORTS as PORT_ROWS, resolve

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from examples.catalog import all_components  # noqa: E402

# Catalogued demo classes (product apps own theirs). Since spec Q3 every one
# is imported from ux_compose.components, so select by catalog, not __module__.
EXAMPLE_CLASSES = sorted(
    {c.__name__ for c in all_components() if not c.__module__.startswith("apps.")}
)
KIT_NAMES = {n for n in kit.__all__ if isinstance(getattr(kit, n), type)}
CLASHES = sorted(set(EXAMPLE_CLASSES) & KIT_NAMES)
PORTS = [n for n in EXAMPLE_CLASSES if n not in KIT_NAMES]


def _fake_app(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "__init__.py").write_text("", encoding="utf-8")
    css = tmp_path / "assets" / "css"
    css.mkdir(parents=True)
    (css / "input.css").write_text('@import "tailwindcss";\n', encoding="utf-8")
    return tmp_path


def test_inventory_is_70_examples_16_clashes():  # GUARD
    assert len(EXAMPLE_CLASSES) == 70
    assert not [c for c in all_components() if c.__module__.startswith("examples.")]
    assert len(CLASHES) == 16
    assert len(PORTS) == 54


def test_kit_modules_never_import_examples():  # GUARD
    for py in (ROOT / "src" / "ux_compose" / "components").glob("*.py"):
        assert "from examples" not in py.read_text(encoding="utf-8"), py.name


def test_catalog_names_and_stems_unique():  # GUARD
    names = [m["name"] for m in CATALOG.values()]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("name", PORTS)
def test_example_is_in_kit_catalog(name):
    slug = name.lower()
    assert slug in PORT_ROWS, f"{name} has no component home"
    assert slug not in CATALOG  # ports are not bound by the kit widget contract (spec §4)
    assert resolve(slug)["module"] == f"ux_compose.components.{slug}"


@pytest.mark.parametrize("name", PORTS)
def test_add_copies_runnable_port(name, tmp_path):
    slug = name.lower()
    assert slug in PORT_ROWS, f"{name} has no component home"
    root = _fake_app(tmp_path)
    written = copy_component(slug, root=root)
    text = written["py"].read_text(encoding="utf-8")
    ast.parse(text)
    assert "examples" not in text
    spec = importlib.util.spec_from_file_location(f"port_{slug}", written["py"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    html = getattr(mod, name)().__render__()
    assert html.strip()


def test_add_list_shows_ports(capsys):
    from ux_compose.cli import main

    main(["add", "--list"])
    out = capsys.readouterr().out
    assert "example ports" in out and "wizard" in out and "counter" in out
