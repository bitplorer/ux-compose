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


@pytest.fixture(autouse=True)
def _prod_env(monkeypatch):
    for name in ("DEBUG", "UX_BEHAVIOR_SECRET", "REDIS_URL", "UXCOMPOSE_STATE_STORE", "SOURCE_DATE_EPOCH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)


@pytest.fixture(autouse=True)
def _stub_smoke_import(request, monkeypatch):
    """The real import from the bundle alone costs ~1s a build. File-set and --out tests stub it;
    ``real_smoke_import`` tests, test_build_check.py and tests/integration run it."""
    if request.node.get_closest_marker("real_smoke_import") is None:
        import ux_compose.cli.package as package

        monkeypatch.setattr(package, "_smoke_import", lambda bundle, entry: None)


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


def _excluded(out: str) -> list[str]:
    return out.split("excluded: ", 1)[1].split("; ", 1)[0].split(", ")


def test_file_set_is_an_allowlist_and_lists_every_exclusion(app, capsys):
    planted = {
        ".env": "SECRET=1",
        ".env.local": "SECRET=1",
        "id_rsa": "k",
        ".netrc": "machine x",
        "notes.txt": "n",
        "pyproject.toml": "[x]",
        "routes/notes.bin": "b",
        "assets/data.sqlite": "d",
        "components/stale.pyc": "x",
        "routes/__pycache__/hello.cpython-314.pyc": "x",
        "assets/node_modules/x.js": "x",
        "tests/fixture.json": "{}",
    }
    for rel, text in planted.items():
        (app / rel).parent.mkdir(parents=True, exist_ok=True)
        (app / rel).write_text(text, encoding="utf-8")

    assert _package() == 0
    out = capsys.readouterr().out
    bundle = app / "dist" / "demo"
    assert _tree(bundle) == SOURCE | GENERATED
    assert "[OK  ] package: dist/demo" in out
    assert "secret detection is best-effort: keep secrets in the environment, not in the app tree" in out
    assert set(_excluded(out)) == {
        ".env",
        ".env.local",
        ".netrc",
        "id_rsa",
        "notes.txt",
        "pyproject.toml",
        "tests/fixture.json",
        "routes/notes.bin",
        "routes/__pycache__/",
        "assets/data.sqlite",
        "assets/node_modules/",
        "components/stale.pyc",
    }


@pytest.mark.parametrize(
    "rel, text",
    [
        ("routes/.env", "SECRET=1"),
        ("deploy/id_rsa", "k"),
        ("deploy/id_ed25519.pub.txt", "k"),
        ("deploy/cert.p12", "k"),
        ("assets/site.pfx", "k"),
        ("deploy/.netrc", "machine x"),
        ("assets/.npmrc", "//registry/:_authToken=x"),
        ("components/tls.key", "k"),
        ("assets/sa.json", '{"type": "service_account", "private_key": "x"}'),
        ("deploy/notes.txt", "-----BEGIN OPENSSH PRIVATE KEY-----"),
        ("settings_key.py", "K = '-----BEGIN RSA PRIVATE KEY-----'"),
    ],
)
def test_refuses_key_shaped_files_in_allowed_dirs(app, capsys, rel, text):
    (app / rel).parent.mkdir(parents=True, exist_ok=True)
    (app / rel).write_text(text, encoding="utf-8")
    assert _package() == 1
    out = capsys.readouterr().out
    assert f"[FAIL] package: refusing to bundle: {rel} (" in out
    assert not (app / "dist").exists()


def test_refuses_every_symlink_in_the_tree(app, tmp_path, capsys):
    """The bundle copies regular files only; no link target is classified."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "creds.json").write_text('{"token": "x"}', encoding="utf-8")
    (app / ".env").write_text("SECRET=1", encoding="utf-8")
    (app / "routes" / "env.txt").symlink_to("../.env")
    (app / "routes" / "creds.json").symlink_to(outside / "creds.json")
    (app / "assets" / "css" / "alias.css").symlink_to("input.css")
    (app / "assets" / "css2").symlink_to("css", target_is_directory=True)
    (app / "shared").symlink_to(outside, target_is_directory=True)
    assert _package() == 1
    out = capsys.readouterr().out
    assert (
        "[FAIL] package: refusing to bundle: assets/css/alias.css (symlink), assets/css2 (symlink), "
        "routes/creds.json (symlink), routes/env.txt (symlink), shared (symlink)"
    ) in out
    assert not (app / "dist").exists()


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")


@pytest.mark.real_smoke_import
def test_ships_every_python_module_and_imports_from_the_bundle(app, capsys):
    """lib/, a nested package and relative imports: the bundle imports alone."""
    _write(
        app,
        {
            "lib/__init__.py": "from .sub import deep\nVALUE = deep.VALUE\n",
            "lib/sub/__init__.py": "",
            "lib/sub/deep.py": "from ..helpers import double\nVALUE = double(21)\n",
            "lib/helpers.py": "def double(x):\n    return 2 * x\n",
            "util.py": "NAME = 'util'\n",
        },
    )
    settings = app / "settings.py"
    settings.write_text(
        settings.read_text(encoding="utf-8") + "\nfrom lib import VALUE\nfrom util import NAME\nassert VALUE == 42\n",
        encoding="utf-8",
    )
    assert _package() == 0
    out = capsys.readouterr().out
    assert "[OK  ] package: dist/demo" in out
    bundle = app / "dist" / "demo"
    assert {"lib/__init__.py", "lib/sub/__init__.py", "lib/sub/deep.py", "lib/helpers.py", "util.py"} <= _tree(bundle)


@pytest.mark.real_smoke_import
def test_refuses_a_bundle_that_cannot_import_alone(app, capsys):
    """The smoke import runs with -I from the bundle dir: no source root on sys.path."""
    _write(app, {"lib/__init__.py": "", "lib/data.yaml": "x: 1\n"})
    settings = app / "settings.py"
    settings.write_text(
        settings.read_text(encoding="utf-8")
        + "\nDATA = (Path(__file__).resolve().parent / 'lib' / 'data.yaml').read_text()\n",
        encoding="utf-8",
    )
    assert _package() == 1
    out = capsys.readouterr().out
    assert "[FAIL] package: import app:asgi from the bundle alone failed: FileNotFoundError: " in out
    assert "lib/data.yaml" in out
    assert not (app / "dist").exists()


@pytest.mark.parametrize(
    "stray",
    [
        ("routes/pyvenv.cfg", "home = /usr/bin"),
        ("routes/MANIFEST.json", '{"generator": "uxcompose build --package", "files": []}'),
    ],
)
def test_a_stray_venv_or_bundle_marker_does_not_hide_a_source_dir(app, capsys, stray):
    _write(app, {stray[0]: stray[1]})
    assert _package() == 0
    out = capsys.readouterr().out
    assert "routes/" not in _excluded(out)
    tree = _tree(app / "dist" / "demo")
    assert "routes/hello.py" in tree
    assert (stray[0] in _excluded(out)) != (stray[0] in tree)  # an ordinary file: shipped or listed


def test_replaces_a_bundle_that_ran_but_not_one_holding_user_files(app, tmp_path, capsys):
    out_dir = str(tmp_path / "out")
    assert _package("--out", out_dir) == 0
    bundle = tmp_path / "out" / "demo"
    (bundle / "__pycache__").mkdir()
    (bundle / "__pycache__" / "app.cpython-314.pyc").write_bytes(b"x")
    (bundle / "assets" / "static" / "file" / "js").mkdir(parents=True)
    assert _package("--out", out_dir) == 0
    (bundle / ".env").write_text("SECRET=1", encoding="utf-8")
    assert _package("--out", out_dir) == 1
    out = capsys.readouterr().out
    assert f"{bundle} holds .env: not written by uxcompose, so it is not replaced" in out
    assert (bundle / ".env").read_text(encoding="utf-8") == "SECRET=1"
    (bundle / ".env").unlink()
    (bundle / "routes" / "hello.py").write_text("# edited", encoding="utf-8")
    assert _package("--out", out_dir) == 1
    assert (bundle / "routes" / "hello.py").read_text(encoding="utf-8") == "# edited"


def test_rebuilt_from_scratch(app):
    assert _package() == 0
    (app / "routes" / "hello.py").write_text("# v2\n" + (app / "routes" / "hello.py").read_text(encoding="utf-8"))
    (app / "util.py").write_text("X = 1\n", encoding="utf-8")
    assert _package() == 0
    bundle = app / "dist" / "demo"
    assert (bundle / "routes" / "hello.py").read_text(encoding="utf-8").startswith("# v2\n")
    (app / "util.py").unlink()
    assert _package() == 0
    assert not (bundle / "util.py").exists()


def test_an_edited_bundle_inside_the_app_is_source_again(app, capsys):
    """Not a pristine bundle: doctor scans it, and the dual Document fails the build."""
    assert _package() == 0
    (app / "dist" / "demo" / "notes.txt").write_text("mine", encoding="utf-8")
    assert _package() == 1
    out = capsys.readouterr().out
    assert "[FAIL] doctor: ok=False" in out
    assert "dual-Document" in out
    assert (app / "dist" / "demo" / "notes.txt").read_text(encoding="utf-8") == "mine"


def test_package_without_archive_drops_an_older_archive(app):
    assert main(["build", "--skip-tailwind", "--archive"]) == 0
    assert _package() == 0
    assert not (app / "dist" / "demo.tar.gz").exists()


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

    assert manifest["generator"] == "uxcompose build --package"
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


@pytest.mark.real_smoke_import
def test_refuses_a_failing_build(app, capsys):
    assert main(["build", "--skip-tailwind", "--package", "--app", "nope:asgi"]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] package: import nope:asgi from the bundle alone failed: ModuleNotFoundError" in out
    assert "import:" not in out  # --package imports the bundle copy only, not the source too
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


# --out safety: nothing is written or deleted unless the target is ours.


def _snapshot(path: Path) -> dict[str, bytes]:
    """Every file except the build's own import cache."""
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


@pytest.mark.parametrize(
    "out, name",
    [(".", None), ("..", None), ("/", None), ("~", None), (".", "routes"), ("routes", None), ("assets/x", None)],
)
def test_refuses_out_that_is_the_app_a_parent_or_its_source(app, capsys, monkeypatch, out, name):
    monkeypatch.setenv("HOME", str(app.parent))
    (app / ".git").mkdir()
    (app / ".git" / "HEAD").write_text("ref", encoding="utf-8")
    (app / ".env").write_text("SECRET=1", encoding="utf-8")
    before = _snapshot(app.parent)
    argv = ["--out", os.path.expanduser(out)] + (["--name", name] if name else [])
    assert _package(*argv) == 1
    printed = capsys.readouterr().out
    assert "[FAIL] package: --out " in printed
    assert _snapshot(app.parent) == before


def test_refuses_a_foreign_non_empty_out(app, tmp_path, capsys):
    foreign = tmp_path / "foreign"
    (foreign / "demo").mkdir(parents=True)
    (foreign / "demo" / "keep.txt").write_text("mine", encoding="utf-8")
    (foreign / "other.txt").write_text("mine", encoding="utf-8")
    assert _package("--out", str(foreign)) == 1
    out = capsys.readouterr().out
    assert "is not a dedicated bundle directory (it holds demo, other.txt)" in out
    assert (foreign / "demo" / "keep.txt").read_text(encoding="utf-8") == "mine"


def test_refuses_a_foreign_dir_with_the_bundle_name(app, tmp_path, capsys):
    out = tmp_path / "out"
    (out / "demo").mkdir(parents=True)
    (out / "demo" / "MANIFEST.json").write_text('{"name": "demo"}', encoding="utf-8")
    assert _package("--out", str(out)) == 1
    assert "not a dedicated bundle directory (it holds demo)" in capsys.readouterr().out
    assert (out / "demo" / "MANIFEST.json").is_file()


def test_refuses_a_symlinked_out_to_the_app_or_a_foreign_dir(app, tmp_path, capsys):
    (tmp_path / "to-parent").symlink_to(app.parent, target_is_directory=True)
    assert _package("--out", str(tmp_path / "to-parent")) == 1
    assert "is the app directory or one of its parents" in capsys.readouterr().out
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "x.txt").write_text("x", encoding="utf-8")
    (tmp_path / "to-foreign").symlink_to(foreign, target_is_directory=True)
    assert _package("--out", str(tmp_path / "to-foreign")) == 1
    assert "not a dedicated bundle directory (it holds x.txt)" in capsys.readouterr().out
    assert sorted(p.name for p in foreign.iterdir()) == ["x.txt"]


def test_refuses_a_symlink_inside_out(app, tmp_path, capsys):
    assert _package("--out", str(tmp_path / "out")) == 0
    (tmp_path / "out" / "elsewhere").symlink_to(app, target_is_directory=True)
    assert _package("--out", str(tmp_path / "out")) == 1
    assert "it holds elsewhere" in capsys.readouterr().out
    assert (app / "app.py").is_file()


@pytest.mark.parametrize("name", ["../x", "a/b", ".", "..", "", ".hidden"])
def test_refuses_a_name_that_is_not_one_segment(app, capsys, name):
    assert _package("--name", name) == 1
    assert "must be one plain path segment" in capsys.readouterr().out
    assert not (app / "dist").exists()


def test_replaces_only_its_own_bundles_and_keeps_siblings(app, tmp_path):
    out = tmp_path / "out"
    assert _package("--out", str(out), "--name", "a") == 0
    assert main(["build", "--skip-tailwind", "--archive", "--out", str(out), "--name", "b"]) == 0
    assert _package("--out", str(out), "--name", "a") == 0
    assert sorted(p.name for p in out.iterdir()) == ["a", "b", "b.tar.gz"]


def test_a_refused_build_creates_no_out_dir(app, capsys):
    (app / "requirements.txt").unlink()
    assert _package() == 1
    assert not (app / "dist").exists()


def test_custom_out_inside_app_does_not_break_the_next_build(app):
    """doctor skips a bundle by its MANIFEST marker, not by the dir name."""
    assert main(["build", "--skip-tailwind", "--archive", "--out", "out", "--name", "shop"]) == 0
    assert main(["build", "--skip-tailwind", "--archive", "--out", "out", "--name", "shop"]) == 0


def test_bad_source_date_epoch_is_one_line(app, capsys, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "soon")
    assert main(["build", "--skip-tailwind", "--archive"]) == 1
    assert "[FAIL] package: SOURCE_DATE_EPOCH must be a non-negative integer, got 'soon'" in capsys.readouterr().out


def test_refuses_requirement_includes(app, capsys):
    (app / "base.txt").write_text("fastapi\n", encoding="utf-8")
    req = app / "requirements.txt"
    req.write_text(req.read_text(encoding="utf-8").replace("fastapi\n", "-r base.txt\n"), encoding="utf-8")
    assert _package() == 1
    assert "requirements.txt includes other files (-r / -c)" in capsys.readouterr().out


def test_dirty_checkout_warns_loudly(app, capsys, monkeypatch):
    from ux_compose.cli import package

    monkeypatch.setattr(package, "_dirty_checkout", lambda: "/src/ux-compose")
    assert _package() == 0
    out = capsys.readouterr().out
    assert "  WARNING: the ux-compose checkout /src/ux-compose has uncommitted changes." in out
    assert "matches no commit" in out


# --- #131: follow-ups from the #130 review -----------------------------------


@pytest.mark.real_smoke_import
@pytest.mark.parametrize("where", ["import", "sync startup"])
def test_a_blocked_import_or_sync_startup_is_one_line(app, capsys, monkeypatch, where):
    """asyncio cannot time a blocking call, so the subprocess timeout fires: no traceback."""
    import ux_compose.cli.package as package

    monkeypatch.setattr(package, "IMPORT_TIMEOUT", 2.0)
    block = "import time\ntime.sleep(30)\n"
    if where == "sync startup":
        block = (
            "_served = asgi\n\n\nasync def asgi(scope, receive, send):\n"
            "    if scope['type'] == 'lifespan':\n        await receive()\n"
            "        import time\n        time.sleep(30)\n"
            "    await _served(scope, receive, send)\n"
        )
    (app / "app.py").write_text((app / "app.py").read_text(encoding="utf-8") + "\n" + block, encoding="utf-8")
    want = (
        "[FAIL] package: import app:asgi and its ASGI startup from the bundle alone did not finish "
        "within 2s; a blocking call at import time or in a sync startup handler?"
    )
    for argv in (["build", "--check"], ["build", "--skip-tailwind", "--skip-import", "--package"]):
        assert main(argv) == 1
        out = capsys.readouterr().out
        assert want in out.splitlines()[-3], out
        assert "Traceback" not in out


def test_a_planted_venv_does_not_hide_a_source_dir(app, capsys):
    """routes/pyvenv.cfg + routes/bin/python made routes/ a venv: skipped by doctor and the bundle."""
    _write(app, {"routes/pyvenv.cfg": "home = /usr/bin", "routes/bin/python": "", "routes/evil.py": "import ux_channel\n"})
    assert main(["doctor", "."]) == 1
    assert "evil.py" in capsys.readouterr().out
    assert _package() == 1
    out = capsys.readouterr().out
    assert "Isolation violation" in out and "evil.py" in out
    assert not (app / "dist").exists()
    (app / "routes" / "evil.py").unlink()
    assert _package() == 0
    out = capsys.readouterr().out
    assert {"routes/pyvenv.cfg", "routes/bin/python"} <= set(_excluded(out))
    assert "routes/hello.py" in _tree(app / "dist" / "demo")


def test_a_bundle_holding_user_files_names_them(app, capsys):
    assert _package() == 0
    bundle = app / "dist" / "demo"
    (bundle / ".env").write_text("SECRET=1", encoding="utf-8")
    (bundle / ".venv" / "bin").mkdir(parents=True)
    (bundle / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin", encoding="utf-8")
    (bundle / "routes" / "hello.py").write_text("# edited", encoding="utf-8")
    assert _package() == 1
    out = capsys.readouterr().out
    assert (
        "dist/demo holds .env, .venv/, routes/hello.py (changed): not written by uxcompose, "
        "so it is not replaced; move them out or pick another --out"
    ) in out
    assert (bundle / ".env").is_file() and (bundle / ".venv").is_dir()
    readme = " ".join((bundle / "README.RUN.txt").read_text(encoding="utf-8").split())
    assert "Keep a .venv in a copy of this directory or an unpacked archive, not here" in readme


def test_refuses_a_hardlinked_file(app, capsys):
    """A hardlink is the same file under another name: a copied file must have one link."""
    (app / ".env").write_text("SECRET=1", encoding="utf-8")
    os.link(app / ".env", app / "routes" / "env.txt")
    assert _package() == 1
    assert "[FAIL] package: refusing to bundle: routes/env.txt (hardlinked, 2 links)" in capsys.readouterr().out
    assert not (app / "dist").exists()


@pytest.mark.real_smoke_import
def test_package_imports_the_app_once(app, capsys, monkeypatch, tmp_path):
    """--package skips the source-tree import: the bundle import is the stricter one."""
    count = tmp_path / "imports"
    monkeypatch.setenv("UXC_COUNT", str(count))
    (app / "app.py").write_text(
        (app / "app.py").read_text(encoding="utf-8")
        + "\nimport os\nwith open(os.environ['UXC_COUNT'], 'a') as _f:\n    _f.write('x')\n",
        encoding="utf-8",
    )
    assert _package() == 0, capsys.readouterr().out
    assert count.read_text() == "x"
