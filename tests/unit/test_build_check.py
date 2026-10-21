"""``uxcompose build --check``: every build check, nothing written."""
from __future__ import annotations

import hashlib
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

import ux_compose.tailwind as tw
from ux_compose.cli import main
from ux_compose.scaffold import create_app

SECRET = "explicit-secret-0123456789abcdef"
CSS = "assets/static/file/css/output.css"

# A Tailwind stand-in: the output depends on input.css and every *.py source,
# the way Tailwind's class scan does; nothing else is written.
FAKE_TAILWIND = """\
import hashlib, sys
from pathlib import Path
args = sys.argv[1:]
src, out = Path(args[args.index("-i") + 1]), Path(args[args.index("-o") + 1])
h = hashlib.sha256(src.read_bytes())
for p in sorted(Path.cwd().rglob("*.py")):
    if "__pycache__" not in p.parts:
        h.update(p.read_bytes())
out.write_text("/*" + h.hexdigest() + ("min" if "--minify" in args else "") + "*/")
"""


@pytest.fixture(autouse=True)
def _prod_env(monkeypatch, tmp_path):
    for name in ("DEBUG", "UX_BEHAVIOR_SECRET", "REDIS_URL", "UXCOMPOSE_STATE_STORE", "SOURCE_DATE_EPOCH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("UX_CHANNEL_SECRET", SECRET)
    fake = tmp_path / "bin" / "fake_tailwind.py"
    fake.parent.mkdir()
    fake.write_text(FAKE_TAILWIND, encoding="utf-8")
    monkeypatch.setenv("UXCOMPOSE_TAILWIND", f"{sys.executable} -B {fake}")


@pytest.fixture
def app(tmp_path, monkeypatch):
    root = create_app(tmp_path / "demo", name="demo")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def built(app, capsys):
    assert main(["build"]) == 0
    capsys.readouterr()
    return app


def _snapshot(root: Path) -> dict[str, tuple]:
    """Every path under root (dirs too, so a new ``__pycache__`` shows): mode, mtime, sha256."""
    snap = {}
    for p in [root, *root.rglob("*")]:
        st = p.lstat()
        digest = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        snap[p.relative_to(root).as_posix()] = (stat.S_IMODE(st.st_mode), st.st_mtime_ns, digest)
    return snap


def _rows(out: str) -> dict[str, str]:
    return {
        line.split("] ", 1)[1].split(": ", 1)[0]: line.strip()
        for line in out.splitlines()
        if line.startswith("  [")
    }


def test_help_lists_check(capsys):
    with pytest.raises(SystemExit):
        main(["build", "--help"])
    assert "--check" in capsys.readouterr().out


def test_check_writes_nothing_and_passes(built, capsys):
    before = _snapshot(built)
    assert main(["build", "--check"]) == 0
    out = capsys.readouterr().out
    assert _snapshot(built) == before
    assert list(_rows(out)) == ["app.py", "tailwind", "doctor", "package"]
    assert f"[OK  ] tailwind: {CSS} matches a fresh env compile" in out
    assert "[OK  ] package: would pass: doctor --prod, import app:asgi, ASGI startup, GET /ux-dom/static/x_element.js, /css/output.css from the bundle alone" in out
    assert out.rstrip().endswith("BUILD OK (--check: nothing written)")


def test_check_passes_on_a_read_only_tree(built, capsys):
    before = _snapshot(built)
    paths = [built, *built.rglob("*")]
    for p in paths:
        p.chmod(stat.S_IMODE(p.stat().st_mode) & ~0o222)
    try:
        assert main(["build", "--check"]) == 0, capsys.readouterr().out
    finally:
        for p in paths:
            p.chmod(stat.S_IMODE(p.stat().st_mode) | stat.S_IWUSR)
    after = _snapshot(built)
    # chmod back restores the write bit; everything else must be untouched.
    assert {k: v[1:] for k, v in after.items()} == {k: v[1:] for k, v in before.items()}


def test_stale_css_after_a_template_edit(built, capsys):
    hello = built / "routes" / "hello.py"
    hello.write_text(hello.read_text(encoding="utf-8") + "\n# class_='text-red-500'\n", encoding="utf-8")
    before = _snapshot(built)
    assert main(["build", "--check"]) == 1
    out = capsys.readouterr().out
    assert _snapshot(built) == before
    assert f"[FAIL] tailwind: {CSS} is stale: a fresh env compile differs — run uxcompose build" in out
    assert main(["build"]) == 0
    assert main(["build", "--check"]) == 0


def test_no_minify_is_compared_as_built(built, capsys):
    assert main(["build", "--check", "--no-minify"]) == 1
    assert "is stale" in capsys.readouterr().out
    assert main(["build", "--no-minify"]) == 0
    assert main(["build", "--check", "--no-minify"]) == 0


def test_missing_css_fails(app, capsys):
    before = _snapshot(app)
    assert main(["build", "--check"]) == 1
    assert f"[FAIL] tailwind: {CSS} missing — run uxcompose build" in capsys.readouterr().out
    assert _snapshot(app) == before


def test_check_never_touches_the_tailwind_cache(built, capsys, monkeypatch, tmp_path):
    monkeypatch.delenv("UXCOMPOSE_TAILWIND")
    monkeypatch.setattr(tw, "_from_path", lambda: None)
    monkeypatch.setattr(tw, "_from_pytailwindcss", lambda: None)
    monkeypatch.setattr(tw, "_from_node_modules", lambda start=None: None)
    monkeypatch.setattr(tw, "_download_standalone", lambda **_: pytest.fail("--check downloaded"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    cached = tw.cache_dir() / tw.standalone_asset_name()
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"not tailwind")
    cached.chmod(0o644)
    before = _snapshot(tmp_path / "cache")
    assert main(["build", "--check"]) == 1
    out = capsys.readouterr().out
    assert f"[FAIL] tailwind: cached {cached} failed sha256" in out
    assert _snapshot(tmp_path / "cache") == before
    cached.unlink()
    assert main(["build", "--check"]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] tailwind: no Tailwind CLI found, and --check does not download one" in out
    assert not cached.exists()


def test_fresh_app_without_secret_fails_with_the_package_message(built, capsys, monkeypatch):
    monkeypatch.delenv("UX_CHANNEL_SECRET")
    before = _snapshot(built)
    assert main(["build", "--check"]) == 1
    check = _rows(capsys.readouterr().out)["package"]
    assert _snapshot(built) == before
    assert check.startswith("[FAIL] package: doctor --prod: [FAIL] secret: Channel secret refused:")
    assert main(["build", "--skip-tailwind", "--skip-import", "--package"]) == 1
    assert _rows(capsys.readouterr().out)["package"] == check


def test_dev_mode_is_not_shippable(built, capsys, monkeypatch):
    monkeypatch.setenv("DEBUG", "1")
    assert main(["build", "--check"]) == 1
    assert "[FAIL] package: doctor --prod: [FAIL] DEBUG: DEBUG='1' is dev mode" in capsys.readouterr().out


def test_import_failure_is_the_package_message(built, capsys):
    (built / "lib.json").write_text("{}", encoding="utf-8")
    (built / "routes" / "data.py").write_text(
        "from pathlib import Path\nDATA = (Path(__file__).parents[1] / 'lib.json').read_text()\n",
        encoding="utf-8",
    )
    assert main(["build"]) == 0  # the source tree imports; the bundle file set does not
    capsys.readouterr()
    before = _snapshot(built)
    assert main(["build", "--check"]) == 1
    check = _rows(capsys.readouterr().out)["package"]
    assert _snapshot(built) == before
    assert check.startswith("[FAIL] package: import app:asgi from the bundle alone failed: ")
    assert "lib.json" in check
    assert main(["build", "--skip-tailwind", "--package"]) == 1
    assert _rows(capsys.readouterr().out)["package"] == check


@pytest.mark.parametrize("flag", ["--package", "--archive", "--skip-import", "--out=x", "--name=x"])
def test_check_refuses_flags_that_write_or_skip_its_checks(app, capsys, flag):
    with pytest.raises(SystemExit) as exc:
        main(["build", "--check", flag])
    assert exc.value.code == 2
    assert f"--check cannot be combined with {flag.split('=')[0]}" in capsys.readouterr().err


def test_check_fails_when_the_app_does_not_serve_the_library_js(built, capsys):
    # A root secrets.py shadows the stdlib module the static mount needs (#131): import OK, JS 404.
    (built / "secrets.py").write_text("X = 1\n", encoding="utf-8")
    assert main(["build", "--check"]) == 1
    check = _rows(capsys.readouterr().out)["package"]
    assert check.startswith(
        "[FAIL] package: GET /ux-dom/static/x_element.js from the bundle alone returned 404"
    )
    assert main(["build", "--skip-tailwind", "--package"]) == 1
    assert _rows(capsys.readouterr().out)["package"] == check
    assert not (built / "dist" / "demo").exists()


LIFESPAN = {
    "raises": "        await receive()\n        raise RuntimeError('db unreachable')\n",
    "fails": "        await receive()\n        await send({'type': 'lifespan.startup.failed', 'message': 'db\\nunreachable'})\n        return\n",
    "hangs": "        await receive()\n        await asyncio.Event().wait()\n",
    "none": "        raise RuntimeError('lifespan is not supported')\n",
}


def _wrap_lifespan(root: Path, body: str) -> None:
    (root / "app.py").write_text(
        (root / "app.py").read_text(encoding="utf-8")
        + "\nimport asyncio\n_served = asgi\n\n\nasync def asgi(scope, receive, send):\n"
        + "    if scope['type'] == 'lifespan':\n" + body
        + "    else:\n        await _served(scope, receive, send)\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "case, want",
    [
        ("raises", "[FAIL] package: ASGI startup failed: RuntimeError: db unreachable"),
        ("fails", "[FAIL] package: ASGI startup failed: db unreachable"),
        ("hangs", "[FAIL] package: ASGI startup did not finish within 1s"),
    ],
)
def test_check_and_package_boot_the_app(built, capsys, monkeypatch, case, want):
    import ux_compose.cli.package as package

    monkeypatch.setattr(package, "LIFESPAN_TIMEOUT", 1.0)
    _wrap_lifespan(built, LIFESPAN[case])
    assert main(["build", "--check"]) == 1
    assert _rows(capsys.readouterr().out)["package"] == want
    assert main(["build", "--skip-tailwind", "--package"]) == 1
    assert _rows(capsys.readouterr().out)["package"] == want
    assert not (built / "dist" / "demo").exists()


def test_an_app_without_lifespan_passes(built, capsys):
    _wrap_lifespan(built, LIFESPAN["none"])
    assert main(["build"]) == 0  # app.py changed: refresh output.css
    assert main(["build", "--check"]) == 0, capsys.readouterr().out
    assert main(["build", "--skip-tailwind", "--package"]) == 0, capsys.readouterr().out
    assert (built / "dist" / "demo" / "MANIFEST.json").is_file()


def test_a_request_error_is_not_an_import_error(built, capsys):
    (built / "app.py").write_text(
        (built / "app.py").read_text(encoding="utf-8")
        + "\n_served = asgi\n\n\nasync def asgi(scope, receive, send):\n"
        + "    if scope['type'] == 'http':\n        raise RuntimeError('state.db not initialised')\n"
        + "    await _served(scope, receive, send)\n",
        encoding="utf-8",
    )
    assert main(["build", "--skip-tailwind", "--package"]) == 1
    assert _rows(capsys.readouterr().out)["package"] == (
        "[FAIL] package: GET /ux-dom/static/x_element.js from the bundle alone raised "
        "RuntimeError: state.db not initialised"
    )


def test_the_scaffold_boots_and_packages(built, capsys):
    assert main(["build", "--skip-tailwind", "--package"]) == 0, capsys.readouterr().out


def test_default_build_steps_unchanged(app, capsys):
    assert main(["build"]) == 0
    assert list(_rows(capsys.readouterr().out)) == ["app.py", "tailwind", "import:app:asgi", "doctor"]
