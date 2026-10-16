"""Lock: the 0.1.x deprecation shims are gone (chore/remove-deprecations).

No PyPI release ever shipped ux-compose, so the shims protect nobody.
"""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "ux_compose"


@pytest.mark.parametrize(
    "mod", ["ux_compose.kit", "ux_compose.kit.catalog", "ux_compose.kit.copy", "ux_compose.kit_construct"]
)
def test_shim_module_is_removed(mod):
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(mod)


def test_kit_dir_and_shim_file_absent():
    # *.py, not the dir: a stale __pycache__ on a dev box is not a shim.
    assert list((SRC / "kit").rglob("*.py")) == []
    assert not (SRC / "kit_construct.py").exists()


def test_morph_play_has_no_deprecated_default():
    from ux_compose.helpers import morph_play

    param = inspect.signature(morph_play).parameters["component"]
    assert param.default is inspect.Parameter.empty
    assert "DeprecationWarning" not in inspect.getsource(morph_play)


@pytest.mark.parametrize(
    "name", ["form_validation", "list_stagger", "page_transition", "optimistic_list"]
)
def test_examples_back_compat_aliases_removed(name):
    examples = SRC.parents[1] / "examples"
    assert not (examples / f"{name}.py").exists()


def test_no_back_compat_paths_left_in_examples():
    examples = SRC.parents[1] / "examples"
    bad = [p.name for p in examples.rglob("*.py") if "Back-compat" in p.read_text(encoding="utf-8")]
    assert bad == []


def test_components_import_arrange_helpers_directly():
    bad = [p.name for p in (SRC / "components").glob("*.py") if "kit_construct" in p.read_text(encoding="utf-8")]
    assert bad == []


@pytest.mark.parametrize("mod", ["ux_compose.routing", "ux_compose.routing.core"])
def test_directory_router_error_alias_removed(mod):
    m = importlib.import_module(mod)
    assert not hasattr(m, "DirectoryRouterError")
    assert "DirectoryRouterError" not in getattr(m, "__all__", ())


def test_include_directory_router_alias_removed():
    from ux_compose.app import App
    from ux_compose.surfaces import mount_surfaces

    assert "include_directory_router" not in inspect.signature(App.mount).parameters
    assert "include_directory_router" not in inspect.signature(mount_surfaces).parameters
