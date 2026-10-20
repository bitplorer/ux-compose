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
from ux_compose.scaffold import create_app, requirements_problem

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
        "[OK  ] requirements: one line per distribution; names ux-compose"
    )


# The exact UC1 failure: a specialist pinned beside the ux-compose line.
UC1_CONFLICT = (
    "ux-dom @ git+https://github.com/bitplorer/ux-dom.git@0440ccbf9b9a53a0ba11ae43b3d04b6079b330f4\n"
)


def test_requirements_specialist_beside_ux_compose_fails(app):
    req = app / "requirements.txt"
    req.write_text(req.read_text(encoding="utf-8") + UC1_CONFLICT, encoding="utf-8")
    assert _row(scan_product_readiness(app, env=PROD), "requirements") == (
        "[FAIL] requirements: requirements.txt pins ux-dom beside ux-compose; "
        "specialists come with the ux-compose line"
    )


@pytest.mark.parametrize(
    "text, problem",
    [
        ("ux-compose @ git+https://x/ux-compose.git@abc#subdirectory=py  # pinned\n", None),
        ("# header\n\nUX_Compose==0.2.0\nuvicorn[standard]>=0.30 ; python_version>='3.14'\n", None),
        ("ux-compose\nfastapi\nFastAPI>=0.115\n", "lists fastapi twice (lines 2 and 3); one line per distribution"),
        ("ux-compose\nux_compose @ https://x/a.zip\n", "lists ux-compose twice (lines 1 and 2); one line per distribution"),
        ("ux-compose\nux-motion\nux-channel\n", "pins ux-channel, ux-motion beside ux-compose; specialists come with the ux-compose line"),
        ("ux-compose\n-e .\n", "line 2 is not a requirement: '-e .'"),
        ("fastapi\n", "does not name ux-compose"),
    ],
)
def test_requirements_problem(text, problem):
    assert requirements_problem(text) == problem


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


# Expected values are Docker's: moby/patternmatcher v0.6.0 (ignorefile.ReadAll +
# MatchesOrParentMatches(".env")), the matcher the docker CLI uses for the context.
@pytest.mark.parametrize(
    "dockerignore, ignored",
    [
        (".env", True),
        ("/.env", True),
        ("./.env", True),
        (".env/", True),
        (".env*", True),
        ("**/.env", True),
        ("**", True),
        ("*", True),
        ("*.env", True),
        ("**/*.env", True),
        (".e?v", True),
        (".[e]nv", True),
        (".[^x]nv", True),
        ("  .env  ", True),
        ("\\.env", True),
        ("#.env", False),
        (" #.env", False),
        (".env\n!.env", False),
        ("!.env\n.env", True),
        ("*\n!.env", False),
        ("*\n!.env\n.env*", True),
        (".env\n# x\n!.e*", False),
        (".env.local", False),
        (".env.*", False),
        ("env", False),
        ("*/.env", False),
        ("a/.env", False),
        (".env/**", False),
        (".ENV", False),
        ("", False),
    ],
)
def test_dotenv_dockerignore_follows_docker(app, dockerignore, ignored):
    (app / ".env").write_text("X=1\n", encoding="utf-8")
    (app / "Dockerfile").write_text("FROM python:3.14\nCOPY . .\n", encoding="utf-8")
    (app / ".dockerignore").write_text(dockerignore, encoding="utf-8")
    row = _row(scan_product_readiness(app, env=PROD), ".env")
    assert row.startswith("[WARN] .env:" if ignored else "[FAIL] .env: present and not in")


def test_dotenv_dockerignore_pattern_docker_rejects_fails(app):
    (app / ".env").write_text("X=1\n", encoding="utf-8")
    (app / "Dockerfile").write_text("FROM python:3.14\n", encoding="utf-8")
    (app / ".dockerignore").write_text(".\\env\n", encoding="utf-8")
    assert _row(scan_product_readiness(app, env=PROD), ".env") == (
        "[FAIL] .env: present; .dockerignore pattern '.\\\\env' cannot be checked "
        "(backslash before a letter or digit)"
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


@pytest.mark.parametrize("listen_on", ["127.0.0.1", "127.0.0.2", "0.0.0.0"])
def test_port_in_use_warns_on_the_address_the_app_binds(app, listen_on):
    """serve prod and every deploy target bind 0.0.0.0; any listener on the port blocks it."""
    with socket.socket() as busy:
        busy.bind((listen_on, 0))
        busy.listen()
        port = busy.getsockname()[1]
        row = _row(scan_product_readiness(app, env=PROD, port=port), f"port:{port}")
    assert row == f"[WARN] port:{port}: in use on 0.0.0.0:{port}"


def test_port_free_ok(app):
    port = _free_port()
    assert _row(scan_product_readiness(app, env=PROD, port=port), f"port:{port}") == (
        f"[OK  ] port:{port}: free on 0.0.0.0:{port}"
    )


def test_port_in_time_wait_is_free(app):
    """Right after a server stops its port sits in TIME_WAIT; uvicorn (SO_REUSEADDR) binds it."""
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # as uvicorn's listener
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        client = socket.create_connection(("127.0.0.1", port))
        conn, _ = server.accept()
        conn.close()  # the server closes first, so its side holds TIME_WAIT
        client.recv(1)
        client.close()
    with socket.socket() as plain, pytest.raises(OSError):
        plain.bind(("0.0.0.0", port))  # the probe without SO_REUSEADDR would WARN here
    assert _row(scan_product_readiness(app, env=PROD, port=port), f"port:{port}").startswith(
        "[OK  ]"
    )


def test_port_probes_the_given_host(app):
    with socket.socket() as busy:
        busy.bind(("127.0.0.2", 0))
        busy.listen()
        port = busy.getsockname()[1]
        rows = scan_product_readiness(app, env=PROD, port=port, host="127.0.0.1")
    assert _row(rows, f"port:{port}") == f"[OK  ] port:{port}: free on 127.0.0.1:{port}"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]


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
    assert f"[FAIL] product: no app.py in {tmp_path.resolve()} —" in capsys.readouterr().out


def test_cli_port_warn_does_not_fail(app, monkeypatch, capsys):
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]
        assert main([str(app), "--prod", "--port", str(port)]) == 0
    assert f"[WARN] port:{port}: in use" in capsys.readouterr().out


def test_cli_host_needs_port(app, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(app), "--prod", "--host", "127.0.0.1"])
    assert exc.value.code == 2
    assert "--host needs --port" in capsys.readouterr().err


def test_cli_port_needs_prod(app, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(app), "--port", "8080"])
    assert exc.value.code == 2
    assert "--port needs --prod" in capsys.readouterr().err


def test_help_lists_prod_and_port(capsys):
    from ux_compose.cli import main as cli_main

    assert cli_main(["--help"]) == 0
    assert "uxcompose doctor [paths...] [--no-fail] [--prod [--port N [--host H]]]" in capsys.readouterr().out
