"""Packages ux_compose imports to serve pages must be declared dependencies.

Without them, `pip install ux-compose && uxcompose serve` fails with
"uvicorn required", and build(host="auto") silently picks a different host.
"""
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _declared() -> set[str]:
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    names = set()
    for spec in deps["project"]["dependencies"]:
        names.add(re.split(r"[\s<>=!~;\[@]", spec, maxsplit=1)[0].lower())
    return names


def test_http_host_stack_is_declared():
    missing = {"fastapi", "starlette", "uvicorn"} - _declared()
    assert not missing, f"undeclared runtime deps: {sorted(missing)}"
