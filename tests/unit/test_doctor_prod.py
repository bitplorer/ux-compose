"""``uxcompose doctor --prod``: product readiness rows, additive to the law scans."""
from __future__ import annotations

import importlib
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.cli.deploy import prepare_deploy
from ux_compose.doctor import SECRET_MISSING, main, scan_product_readiness
from ux_compose.scaffold import create_app

# ``ux_compose.doctor`` the attribute is the function; this is the module.
doctor_mod = importlib.import_module("ux_compose.doctor")

SECRET = "explicit-secret-0123456789abcdef"
PROD = {"UX_CHANNEL_SECRET": SECRET}


@pytest.fixture
def app(tmp_path):
    return create_app(tmp_path / "demo", name="demo")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in ("DEBUG", "UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL", "UXCOMPOSE_STATE_STORE"):
        monkeypatch.delenv(name, raising=False)


def _row(rows: list[str], name: str) -> str:
    found = [r for r in rows if r.split("] ", 1)[1].startswith(f"{name}: ")]
    assert len(found) == 1, rows
    return found[0]


def test_fixed_scaffold_is_all_ok(app):
    rows = scan_product_readiness(app, env=PROD)
    assert [r for r in rows if not r.startswith("[OK  ] ")] == [], rows
    names = [r.split("] ", 1)[1].split(": ", 1)[0] for r in rows]
    assert names == ["product", "dep:uvicorn", "dep:fastapi", "requirements", "secret", "DEBUG", ".env"]


# product


def test_empty_dir_fails_product_and_stops(tmp_path):
    rows = scan_product_readiness(tmp_path, env=PROD)
    assert rows == [
        f"[FAIL] product: no app.py in {tmp_path} — run uxcompose create-app, "
        "or pass the app root"
    ]


# dep:<name>


@pytest.mark.parametrize("module", ["uvicorn", "fastapi"])
def test_dep_fails_when_not_importable(app, monkeypatch, module):
    real = doctor_mod.find_spec
    monkeypatch.setattr(doctor_mod, "find_spec", lambda m: None if m == module else real(m))
    row = _row(scan_product_readiness(app, env=PROD), f"dep:{module}")
    assert row.startswith(f"[FAIL] dep:{module}: not importable in {sys.executable}")


@pytest.mark.parametrize("module", ["uvicorn", "fastapi"])
def test_dep_ok_when_importable(app, module):
    assert _row(scan_product_readiness(app, env=PROD), f"dep:{module}") == (
        f"[OK  ] dep:{module}: importable"
    )


# requirements


def test_requirements_missing_fails(app):
    (app / "requirements.txt").unlink()
    assert _row(scan_product_readiness(app, env=PROD), "requirements") == (
        "[FAIL] requirements: requirements.txt missing — deploys install from it"
    )


def test_requirements_without_ux_compose_fails(app):
    (app / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    assert _row(scan_product_readiness(app, env=PROD), "requirements") == (
        "[FAIL] requirements: requirements.txt does not name ux-compose"
    )


def test_requirements_naming_ux_compose_ok(app):
    assert _row(scan_product_readiness(app, env=PROD), "requirements") == (
        "[OK  ] requirements: names ux-compose"
    )


# secret (UC4 secret_readiness)


def test_secret_missing_fails_with_uc4_line(app):
    assert _row(scan_product_readiness(app, env={}), "secret") == f"[FAIL] secret: {SECRET_MISSING}"


@pytest.mark.parametrize("key", ["UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET"])
def test_secret_set_ok(app, key):
    assert _row(scan_product_readiness(app, env={key: SECRET}), "secret").startswith("[OK  ] secret:")


# DEBUG


@pytest.mark.parametrize("value", ["1", "true", " On "])
def test_debug_truthy_fails(app, value):
    row = _row(scan_product_readiness(app, env={"DEBUG": value, **PROD}), "DEBUG")
    assert row == f"[FAIL] DEBUG: DEBUG={value!r} is dev mode — unset it for prod"


@pytest.mark.parametrize("env", [PROD, {"DEBUG": "false", **PROD}, {"DEBUG": "0", **PROD}])
def test_debug_unset_or_falsy_ok(app, env):
    assert _row(scan_product_readiness(app, env=env), "DEBUG") == "[OK  ] DEBUG: prod mode"


# .env


def test_dotenv_absent_ok(app):
    assert _row(scan_product_readiness(app, env=PROD), ".env") == "[OK  ] .env: absent"


def test_dotenv_present_warns(app):
    (app / ".env").write_text(f"UX_CHANNEL_SECRET={SECRET}\n", encoding="utf-8")
    assert _row(scan_product_readiness(app, env=PROD), ".env") == (
        "[WARN] .env: present — do not ship; set secrets on the host"
    )


def test_dotenv_with_dockerfile_but_not_dockerignored_fails(app):
    (app / ".env").write_text("X=1\n", encoding="utf-8")
    (app / "Dockerfile").write_text("FROM python:3.14\nCOPY . .\n", encoding="utf-8")
    rows = scan_product_readiness(app, env=PROD)
    assert _row(rows, ".env") == (
        "[FAIL] .env: present and not in .dockerignore — docker build would copy it"
    )


def test_dotenv_with_deploy_docker_dockerignore_only_warns(app):
    (app / ".env").write_text("X=1\n", encoding="utf-8")
    prepare_deploy("docker", cwd=app)
    assert _row(scan_product_readiness(app, env=PROD), ".env").startswith("[WARN] .env:")


# deploy:<provider>


def test_deploy_render_declares_secret_ok(app):
    prepare_deploy("render", cwd=app)
    assert _row(scan_product_readiness(app, env=PROD), "deploy:render") == (
        "[OK  ] deploy:render: render.yaml declares UX_CHANNEL_SECRET"
    )


def test_deploy_render_without_secret_fails(app):
    (app / "render.yaml").write_text("services:\n  - type: web\n", encoding="utf-8")
    assert _row(scan_product_readiness(app, env=PROD), "deploy:render") == (
        "[FAIL] deploy:render: render.yaml does not declare UX_CHANNEL_SECRET"
    )


def test_deploy_vps_unit_with_environment_file_ok(app):
    prepare_deploy("vps", cwd=app)
    assert _row(scan_product_readiness(app, env=PROD), "deploy:vps") == (
        "[OK  ] deploy:vps: deploy/demo.service sets EnvironmentFile or "
        "Environment=UX_CHANNEL_SECRET"
    )


@pytest.mark.parametrize("line", ["", "Environment=UX_CHANNEL_SECRET=x\n"])
def test_deploy_vps_unit_secret_line(app, line):
    unit = app / "deploy" / "demo.service"
    unit.parent.mkdir()
    unit.write_text(f"[Service]\n{line}ExecStart=uvicorn app:asgi\n", encoding="utf-8")
    row = _row(scan_product_readiness(app, env=PROD), "deploy:vps")
    assert row.startswith("[OK  ]" if line else "[FAIL] deploy:vps: deploy/demo.service sets")


def test_no_deploy_files_no_deploy_rows(app):
    assert not [r for r in scan_product_readiness(app, env=PROD) if "deploy:" in r]


# port:<N> (owner decision D4: WARN)


def test_port_in_use_warns(app):
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]
        row = _row(scan_product_readiness(app, env=PROD, port=port), f"port:{port}")
    assert row == f"[WARN] port:{port}: in use on 127.0.0.1:{port}"


def test_port_free_ok(app):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    assert _row(scan_product_readiness(app, env=PROD, port=port), f"port:{port}") == (
        f"[OK  ] port:{port}: free on 127.0.0.1:{port}"
    )


def test_no_port_row_without_port(app):
    assert not [r for r in scan_product_readiness(app, env=PROD) if "port:" in r]


# CLI argv


def test_cli_prod_fresh_scaffold_fails_on_secret(app, capsys):
    assert main([str(app), "--prod"]) == 1
    out = capsys.readouterr().out
    assert f"  [FAIL] secret: {SECRET_MISSING}\n" in out
    assert "Product readiness:" in out


def test_cli_prod_fixed_env_passes(app, monkeypatch, capsys):
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)
    assert main([str(app), "--prod"]) == 0
    assert "[FAIL]" not in capsys.readouterr().out


def test_cli_prod_no_fail_exits_zero(app, capsys):
    assert main([str(app), "--prod", "--no-fail"]) == 0
    assert "[FAIL] secret:" in capsys.readouterr().out


def test_cli_prod_empty_dir_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)
    monkeypatch.chdir(tmp_path)
    assert main(["--prod"]) == 1
    assert "[FAIL] product: no app.py in ." in capsys.readouterr().out


def test_cli_port_warn_does_not_fail(app, monkeypatch, capsys):
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]
        assert main([str(app), "--prod", "--port", str(port)]) == 0
    assert f"[WARN] port:{port}: in use" in capsys.readouterr().out


def test_cli_port_needs_prod(app, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(app), "--port", "8080"])
    assert exc.value.code == 2
    assert "--port needs --prod" in capsys.readouterr().err


def test_help_lists_prod_and_port(capsys):
    from ux_compose.cli import main as cli_main

    assert cli_main(["--help"]) == 0
    assert "uxcompose doctor [paths...] [--no-fail] [--prod [--port N]]" in capsys.readouterr().out
