"""``uxcompose build --package`` / ``--archive``: the runnable bundle."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.cli import main
from ux_compose.cli.deploy import _DOCKERFILE
from ux_compose.scaffold import create_app

SECRET = "explicit-secret-0123456789abcdef"
SOURCE = {
    "app.py",
    "document.py",
    "settings.py",
    "requirements.txt",
    "README.md",
    "routes/__init__.py",
    "routes/hello.py",
    "routes/index.py",
    "assets/css/input.css",
    "components/__init__.py",
    "components/login.py",
}
GENERATED = {"run.sh", "README.RUN.txt", "MANIFEST.json"}
PLANTED_SECRETS = (".env", ".env.local", "server.pem", "routes/.env", "components/tls.key")


@pytest.fixture(autouse=True)
def _prod_env(monkeypatch):
    for name in ("DEBUG", "UX_BEHAVIOR_SECRET", "REDIS_URL", "UXCOMPOSE_STATE_STORE", "SOURCE_DATE_EPOCH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)


@pytest.fixture
def app(tmp_path, monkeypatch):
    root = create_app(tmp_path / "demo", name="demo")
    monkeypatch.chdir(root)
    assert main(["add", "login"]) == 0
    return root


def _package(*extra: str) -> int:
    return main(["build", "--skip-tailwind", "--package", *extra])


def _tree(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_flags_are_on_build_help(capsys):
    with pytest.raises(SystemExit):
        main(["build", "--help"])
    out = capsys.readouterr().out
    for flag in ("--package", "--archive", "--out", "--name"):
        assert flag in out


def test_file_set_and_exclusions(app, capsys):
    for rel in PLANTED_SECRETS:
        (app / rel).write_text("SECRET=1\n", encoding="utf-8")
    for junk in ("routes/__pycache__/hello.cpython-314.pyc", "assets/node_modules/x.js", "components/stale.pyc"):
        (app / junk).parent.mkdir(parents=True, exist_ok=True)
        (app / junk).write_text("x", encoding="utf-8")

    assert _package() == 0
    out = capsys.readouterr().out
    bundle = app / "dist" / "demo"
    assert _tree(bundle) == SOURCE | GENERATED
    assert "[OK  ] package: dist/demo" in out
    for rel in PLANTED_SECRETS:
        assert rel in out.split("excluded secrets:", 1)[1].splitlines()[0]


def test_rebuilt_from_scratch(app):
    stale = app / "dist" / "demo" / "stale.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")
    assert _package() == 0
    assert not stale.exists()


def test_out_and_name(app, tmp_path):
    assert _package("--out", str(tmp_path / "out"), "--name", "shop") == 0
    assert (tmp_path / "out" / "shop" / "app.py").is_file()
    assert not (app / "dist").exists()


def test_run_sh(app):
    assert _package() == 0
    run_sh = app / "dist" / "demo" / "run.sh"
    assert os.access(run_sh, os.X_OK)
    text = run_sh.read_text(encoding="utf-8")
    assert 'exec uvicorn app:asgi --app-dir . --host "$HOST" --port "$PORT"' in text
    assert "secret_readiness" in text
    assert "PYTHONPATH" not in text
    assert subprocess.run(["sh", "-n", str(run_sh)], check=False).returncode == 0


def test_run_sh_refuses_missing_secret_in_one_line(app):
    assert _package() == 0
    env = {k: v for k, v in os.environ.items() if k not in ("UX_CHANNEL_SECRET", "DEBUG")}
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env['PATH']}"
    proc = subprocess.run(
        ["sh", str(app / "dist" / "demo" / "run.sh")], check=False, env=env, capture_output=True, text=True, timeout=60
    )
    assert proc.returncode == 1
    assert proc.stderr.startswith("Channel secret refused: attach() requires UX_CHANNEL_SECRET")
    assert len(proc.stderr.strip().splitlines()) == 1
    assert "Traceback" not in proc.stderr


def test_manifest(app):
    assert _package() == 0
    bundle = app / "dist" / "demo"
    raw = (bundle / "MANIFEST.json").read_text(encoding="utf-8")
    manifest = json.loads(raw)

    def strings(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield k
                yield from strings(v)
        elif isinstance(node, list):
            for v in node:
                yield from strings(v)
        elif isinstance(node, str):
            yield node

    absolute = [s for s in strings(manifest) if s.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", s)]
    assert absolute == []
    assert "source_root" not in manifest
    for rel in GENERATED:
        assert str(app) not in (bundle / rel).read_text(encoding="utf-8")

    assert manifest["entrypoint"] == "app:asgi"
    assert manifest["static_model"] == "single_copy_from_site_packages"
    assert {f["path"] for f in manifest["files"]} == SOURCE
    for f in manifest["files"]:
        data = (bundle / f["path"]).read_bytes()
        assert f["sha256"] == hashlib.sha256(data).hexdigest()
        assert f["bytes"] == len(data)
    resolved = manifest["resolved"]
    assert set(resolved) == {"ux-compose", "ux-dom", "ux-channel", "ux-behavior", "ux-motion"}
    for dist, info in resolved.items():
        assert re.fullmatch(r"[0-9a-f]{40}", info["vcs_commit"]), (dist, info)
        assert info["version"], dist
    line = (bundle / "requirements.txt").read_text(encoding="utf-8").splitlines()[0]
    assert line.endswith("@" + resolved["ux-compose"]["vcs_commit"])


def test_archive_is_one_root_and_byte_identical(app, tmp_path):
    assert main(["build", "--skip-tailwind", "--archive"]) == 0
    tar_path = app / "dist" / "demo.tar.gz"
    first = tar_path.read_bytes()
    with tarfile.open(tar_path) as tf:
        members = tf.getmembers()
    files = {m.name for m in members if m.isfile()}
    assert files == {f"demo/{rel}" for rel in _tree(app / "dist" / "demo")}
    assert {m.name.split("/", 1)[0] for m in members} == {"demo"}
    assert [m.name for m in members] == sorted(m.name for m in members)
    assert {(m.mtime, m.uid, m.gid, m.uname, m.gname) for m in members} == {(0, 0, 0, "", "")}
    assert next(m for m in members if m.name == "demo/run.sh").mode == 0o755

    # Touch the sources: a second archive is still byte-identical.
    os.utime(app / "app.py", (1, 1))
    assert main(["build", "--skip-tailwind", "--archive"]) == 0
    assert tar_path.read_bytes() == first


def test_archive_mtime_from_source_date_epoch(app, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    assert main(["build", "--skip-tailwind", "--archive"]) == 0
    with tarfile.open(app / "dist" / "demo.tar.gz") as tf:
        assert {m.mtime for m in tf.getmembers()} == {1700000000}


def test_deploy_files_copied_only_if_present(app):
    assert main(["deploy", "-p", "docker"]) == 0
    assert main(["deploy", "-p", "render"]) == 0
    assert _package() == 0
    bundle = app / "dist" / "demo"
    assert (bundle / "Dockerfile").read_text(encoding="utf-8") == _DOCKERFILE
    assert {"Dockerfile", ".dockerignore", "render.yaml"} <= _tree(bundle)
    assert not (bundle / "fly.toml").exists()


def test_refuses_a_failing_build(app, capsys):
    assert main(["build", "--skip-tailwind", "--package", "--app", "nope:asgi"]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] package: skipped — earlier build steps failed" in out
    assert not (app / "dist").exists()


def test_refuses_missing_requirements(app, capsys):
    (app / "requirements.txt").unlink()
    assert _package() == 1
    out = capsys.readouterr().out
    assert "[FAIL] package: doctor --prod: [FAIL] requirements: requirements.txt missing" in out
    assert not (app / "dist" / "demo").exists()


def test_refuses_unresolvable_requirements(app, capsys):
    req = app / "requirements.txt"
    req.write_text(req.read_text(encoding="utf-8") + "ux-dom>=0.1.0\n", encoding="utf-8")
    assert _package() == 1
    out = capsys.readouterr().out
    assert "[FAIL] package: doctor --prod: [FAIL] requirements: ux-dom (requirements.txt:6) pinned beside ux-compose" in out
    assert not (app / "dist" / "demo").exists()


def test_refuses_a_compose_pin_this_build_did_not_run(app, capsys):
    req = app / "requirements.txt"
    lines = req.read_text(encoding="utf-8").splitlines()
    lines[0] = re.sub(r"@[0-9a-f]{40}$", "@" + "0" * 40, lines[0])
    req.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert _package() == 1
    out = capsys.readouterr().out
    assert "[FAIL] package: requirements.txt pins " in out
    assert "this build runs" in out
    assert not (app / "dist" / "demo").exists()


def test_refuses_on_doctor_prod_fail_row(app, capsys, monkeypatch):
    # The import step accepts dev mode; doctor --prod does not ship it.
    monkeypatch.delenv("UX_CHANNEL_SECRET")
    monkeypatch.setenv("DEBUG", "1")
    assert _package() == 1
    out = capsys.readouterr().out
    assert "[FAIL] package: doctor --prod: [FAIL] DEBUG: DEBUG='1' is dev mode" in out
    assert not (app / "dist" / "demo").exists()
