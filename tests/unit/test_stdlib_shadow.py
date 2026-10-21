"""An app module named like a stdlib module fails every product command (#131).

A top-level ``secrets.py`` at the app root is first on ``sys.path`` for every
library in the process: ux-dom's ``import secrets`` got it and the library JS
returned 404. Reordering ``sys.path`` would only move the breakage into the
app's own ``import secrets``, so the name itself is the error.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.cli import main
from ux_compose.scaffold import create_app

SECRET = "explicit-secret-0123456789abcdef"
LINE = (
    "app modules `email/`, `secrets.py`, `types.py` shadow the Python standard library "
    "modules `email`, `secrets`, `types`; rename them"
)


@pytest.fixture(autouse=True)
def _prod_env(monkeypatch):
    for name in ("DEBUG", "UX_BEHAVIOR_SECRET", "REDIS_URL", "UXCOMPOSE_STATE_STORE", "SOURCE_DATE_EPOCH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)


@pytest.fixture
def app(tmp_path, monkeypatch):
    root = create_app(tmp_path / "demo", name="demo")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def shadowing(app):
    (app / "secrets.py").write_text("X = 1\n", encoding="utf-8")
    (app / "types.py").write_text("", encoding="utf-8")
    (app / "email").mkdir()
    (app / "email" / "__init__.py").write_text("", encoding="utf-8")
    return app


@pytest.fixture
def no_server(monkeypatch):
    """serve must refuse before it starts anything; on a miss the test fails, not hangs."""
    import uvicorn

    import ux_compose.cli.serve_dev as serve_dev

    def started(*_a, **_k):
        raise AssertionError("serve started despite the stdlib shadow")

    monkeypatch.setattr(uvicorn, "run", started)
    monkeypatch.setattr(serve_dev, "run", started)


def test_one_module_is_the_singular_line(app):
    from ux_compose.doctor import stdlib_shadows

    (app / "secrets.py").write_text("", encoding="utf-8")
    assert stdlib_shadows(app) == (
        "app module `secrets.py` shadows the Python standard library module `secrets`; rename it"
    )


def test_top_level_modules_and_packages_only(app):
    from ux_compose.doctor import stdlib_shadows

    (app / "routes" / "json.py").write_text("", encoding="utf-8")  # routes.json: no shadow
    (app / "logging").mkdir()  # no __init__.py: a namespace portion never beats stdlib logging
    (app / "logging" / "x.py").write_text("", encoding="utf-8")
    (app / "queue.txt").write_text("", encoding="utf-8")
    assert stdlib_shadows(app) is None


def test_a_normal_app_passes_every_command(app, capsys):
    assert main(["doctor", "."]) == 0
    assert main(["build", "--skip-tailwind"]) == 0
    assert "shadows" not in capsys.readouterr().out


def test_doctor_fails_naming_every_offender(shadowing, capsys):
    assert main(["doctor", "."]) == 1
    assert f"    - {LINE}" in capsys.readouterr().out.splitlines()


def test_doctor_prod_fails_naming_every_offender(shadowing, capsys):
    assert main(["doctor", ".", "--prod"]) == 1
    assert f"  [FAIL] stdlib: {LINE}" in capsys.readouterr().out.splitlines()


@pytest.mark.parametrize(
    "argv",
    [
        ["build", "--skip-tailwind"],
        ["build", "--check"],
        ["build", "--skip-tailwind", "--package"],
    ],
    ids=["build", "check", "package"],
)
def test_build_fails_first_naming_every_offender(shadowing, capsys, argv):
    assert main(argv) == 1
    out = capsys.readouterr().out
    assert f"  [FAIL] stdlib: {LINE}" in out.splitlines(), out
    assert "import:" not in out and "package:" not in out  # nothing ran against the shadow
    assert not (shadowing / "dist").exists()


@pytest.mark.parametrize("mode", ["dev", "prod"])
def test_serve_refuses_in_one_line(shadowing, capsys, no_server, mode):
    assert main(["serve", mode]) == 2
    assert capsys.readouterr().err.strip() == LINE


# Module names apps commonly pick. The stdlib ones fail every command by name;
# the others (``test`` is not in sys.stdlib_module_names) still package, which
# boots the app and GETs the library JS with 200.
COMMON = ["secrets", "email", "logging", "types", "json", "http", "queue", "site", "test", "platform"]


@pytest.mark.parametrize("name", COMMON)
def test_common_module_names(app, capsys, no_server, name):
    (app / f"{name}.py").write_text("X = 1\n", encoding="utf-8")
    if name in sys.stdlib_module_names:
        line = f"app module `{name}.py` shadows the Python standard library module `{name}`; rename it"
        assert main(["doctor", "."]) == 1
        assert main(["serve", "prod"]) == 2
        assert line in capsys.readouterr().err
        return
    assert main(["build", "--skip-tailwind", "--package"]) == 0, capsys.readouterr().out
