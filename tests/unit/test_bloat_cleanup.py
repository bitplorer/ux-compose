"""Bloat cleanup (0.3.0): dead helpers, ignored params and no-op extras stay gone.

ux-compose and its ux-* specialists are not on PyPI, so these were removed
outright with no shims.
"""
from __future__ import annotations

import inspect
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"


def test_dead_css_import_helper_removed():
    from ux_compose.cli import copy_component

    assert not hasattr(copy_component, "_wire_css_import")


def test_component_has_no_best_effort_dirty_api():
    from ux_compose import Component

    assert not hasattr(Component, "dirty_fields")
    assert not hasattr(Component, "clear_dirty")


def test_probe_has_no_dead_summary_or_ignored_level_param():
    from ux_compose.dx.probe import ProbeResult

    assert not hasattr(ProbeResult, "summary_lines")
    sig = inspect.signature(ProbeResult.incomplete_stack_messages)
    assert "requested_level" not in sig.parameters


def test_surface_registry_has_no_dead_action_names():
    import ux_compose.surfaces as s

    assert all(not hasattr(obj, "action_names") for obj in vars(s).values() if inspect.isclass(obj))


def test_file_url_has_no_ignored_param():
    from ux_compose.surfaces import _file_url

    assert list(inspect.signature(_file_url).parameters) == ["prefix", "stem"]


def test_attach_document_runtimes_has_no_ignored_channel_scripts():
    from ux_compose.wire.boot import attach_document_runtimes

    assert "channel_scripts" not in inspect.signature(attach_document_runtimes).parameters


def test_no_noop_extras():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = data["project"].get("optional-dependencies", {})
    assert not ({"dom", "behavior", "motion", "channel", "full"} & set(extras))
    assert all(extras.values()), "every extra must install something"


def test_python_tree_is_pyflakes_clean():
    r = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--isolated", "--select", "F", *(str(ROOT / d) for d in ("src", "tests", "apps", "examples"))],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout
