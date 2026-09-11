"""Console script uxcompose must import-resolve to the live CLI owner.

Loads ``cli.py`` from disk so the lock stays green without specialists
(package ``__init__`` pulls ux-behavior). The script target string is
the same door ``import ux_compose.cli:main`` uses when the stack is in.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
PYPROJECT = ROOT / "pyproject.toml"


def _project_scripts(text: str) -> dict[str, str]:
    scripts: dict[str, str] = {}
    in_scripts = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_scripts = line == "[project.scripts]"
            continue
        if not in_scripts or "=" not in line or line.startswith("#"):
            continue
        name, _, rest = line.partition("=")
        scripts[name.strip()] = rest.strip().strip('"').strip("'")
    return scripts


def test_uxcompose_console_script_import_resolves():
    text = PYPROJECT.read_text(encoding="utf-8")
    target = _project_scripts(text).get("uxcompose")
    assert target == "ux_compose.cli:main", target
    module_name, sep, attr = target.partition(":")
    assert sep and module_name == "ux_compose.cli" and attr == "main", target
    path = SRC / "cli.py"
    assert path.is_file()
    spec = importlib.util.spec_from_file_location("ux_compose_cli_honesty", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, attr)
    assert callable(fn)
    assert not (SRC / "cli").exists()
    assert not (SRC / "services").exists()
    assert not (SRC / "serve").exists()
