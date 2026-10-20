"""Integration: create-app emits the complete product path."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app, scan_requirements
from ux_compose.doctor import scan_isolation, scan_dual_document, scan_render_chrome


def test_create_app_layout(tmp_path):
    dest = tmp_path / "demo"
    root = create_app(dest, name="demo", level="auto", host="auto")
    assert (root / "app.py").is_file()
    assert (root / "settings.py").is_file()
    assert (root / "document.py").is_file()
    assert not (root / "shell.py").exists()
    assert (root / "routes" / "hello.py").is_file()
    assert (root / "README.md").is_file()
    assert (root / "requirements.txt").is_file()
    assert (root / "assets" / "css" / "input.css").is_file()
    text = (root / "app.py").read_text(encoding="utf-8")
    assert "build(" in text
    assert "asgi" in text
    assert "document=document" in text
    assert "from document import document" in text
    assert "from shell import wrap" not in text
    assert "wrap=document" in text
    assert "wrap_get_chrome" not in text
    assert 'cek="require"' in text
    assert "import ux_channel" not in text
    assert "from ux_channel" not in text
    assert (root / "routes" / "index.py").is_file()
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "uxcompose serve dev" in readme
    assert "uxcompose serve prod" in readme
    assert "serve app:asgi" not in readme
    assert "3.13" not in readme


def test_create_app_teaches_document_and_settings(tmp_path):
    root = create_app(tmp_path / "shop", name="shop", level=1, host="fastapi")
    settings = (root / "settings.py").read_text(encoding="utf-8")
    document = (root / "document.py").read_text(encoding="utf-8")
    hello = (root / "routes" / "hello.py").read_text(encoding="utf-8")
    css = (root / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    req = (root / "requirements.txt").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert "BASE_DIR" in settings
    assert "from ux_compose import WebAssets" in settings
    assert "from ux_dom import WebAssets" not in settings
    assert "DEBUG" in settings
    assert "import ux_channel" not in settings
    assert "from ux_channel" not in settings

    assert "Document(" in document
    assert ".use(" in document
    assert "def page(" not in document
    assert "XElement" in document
    assert "Csp" in document
    assert "Channel.optional()" in document
    assert "from ux_dom import Channel, Csp, Document, XElement" in document
    assert "ux_dom.runtime" not in document
    assert "Channel" in document
    assert "import ux_channel" not in document
    assert "from ux_channel" not in document
    assert "document = None" not in document
    assert "except Exception" not in document

    assert "class Hello" in hello
    assert "def get(" not in hello
    assert "def render(" in hello
    assert "className" in hello
    assert "HAS_DOM" not in hello

    assert '@import "tailwindcss"' in css
    assert "@source" in css

    assert "fastapi" in req
    assert "uvicorn" in req
    active = [
        ln.strip()
        for ln in req.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    assert any(
        ln.startswith("ux-compose @ git+https://github.com/bitplorer/ux-compose.git@")
        for ln in active
    )
    assert any("fastapi" in ln for ln in active)
    assert any(ln.startswith("uvicorn") for ln in active)
    assert any(ln.startswith("cek-host") and ">=0.2.0" in ln for ln in active)
    assert any(ln.startswith("cek-surface") and ">=0.2.0" in ln for ln in active)
    assert not any(
        ln in {"ux-dom", "ux-behavior", "ux-channel", "ux-motion", "ux-compose"}
        for ln in active
    )
    assert "3.13" not in req

    assert 'cek="require"' in readme
    assert "3.13" not in readme
    assert "3.14" in readme


def test_create_app_isolation_and_single_document(tmp_path):
    root = create_app(tmp_path / "iso", name="iso")
    files = list(root.rglob("*.py"))
    assert scan_isolation(files) == []
    # One Document() in document.py; host wraps GET (no leftover page())
    assert scan_dual_document(files) == []
    assert scan_render_chrome(files) == []
    src = (root / "document.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and (
            (isinstance(n.func, ast.Name) and n.func.id == "Document")
            or (isinstance(n.func, ast.Attribute) and n.func.attr == "Document")
        )
    ]
    assert len(calls) == 1


def test_create_app_python_compiles(tmp_path):
    """Emitted .py must parse — leftover {{format}} braces are a defect."""
    root = create_app(tmp_path / "c", name="c")
    for p in root.rglob("*.py"):
        src = p.read_text(encoding="utf-8")
        ast.parse(src, filename=str(p))
        assert "{{" not in src, f"leftover format escape in {p.name}"
        assert "}}" not in src, f"leftover format escape in {p.name}"


def test_create_app_discovers_root_and_hello(tmp_path):
    """index.py aliases GET /; hello.py stays at /hello."""
    from ux_compose.routing import DirectoryRoutes

    root = create_app(tmp_path / "routes_demo", name="routes_demo")
    core = DirectoryRoutes(root, base_directory="routes")
    paths = {r.path for r in core.discover()}
    assert "/" in paths
    assert "/hello" in paths


def _active_requirement_lines(text: str) -> list[str]:
    return [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def test_create_app_requirements_boot_cap_require(tmp_path):
    """pip install -r requirements.txt names ux-compose; it brings the pinned stack."""
    root = create_app(tmp_path / "caps", name="caps")
    req = (root / "requirements.txt").read_text(encoding="utf-8")
    app_py = (root / "app.py").read_text(encoding="utf-8")
    active = _active_requirement_lines(req)

    assert 'cek="require"' in app_py
    assert "wrap=document" in app_py
    assert any(ln.startswith("cek-host") and ">=0.2.0" in ln for ln in active)
    assert any(ln.startswith("cek-surface") and ">=0.2.0" in ln for ln in active)
    assert any(ln.startswith("fastapi") for ln in active)
    assert any(ln.startswith("uvicorn") for ln in active)
    assert any(
        ln.startswith("ux-compose @ git+https://github.com/bitplorer/ux-compose.git@")
        for ln in active
    )
    assert not any(
        ln in {"ux-dom", "ux-behavior", "ux-channel", "ux-motion", "ux-compose"}
        for ln in active
    )
    assert "3.13" not in req
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "3.13" not in readme
    assert "3.14" in readme
    assert 'cek="require"' in readme


def test_create_app_settings_debug_matches_ux_behavior(tmp_path):
    """settings.DEBUG reads env the way ux-behavior does: unset is prod."""
    import os

    root = create_app(tmp_path / "demo", name="demo")
    settings = (root / "settings.py").read_text(encoding="utf-8")
    assert "from ux_behavior.wire import debug_requests_dev" in settings
    assert "DEBUG = debug_requests_dev()" in settings
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "`uxcompose serve dev` sets dev mode" in readme
    assert "UX_CHANNEL_SECRET" in readme

    base = {k: v for k, v in os.environ.items() if k != "DEBUG"}
    base["PYTHONPATH"] = os.pathsep.join([str(root), str(ROOT / "src")])
    seen = {}
    for value in (None, "0", "false", "1", "on"):
        env = dict(base) if value is None else {**base, "DEBUG": value}
        out = subprocess.run(
            [sys.executable, "-c", "import settings; print(settings.DEBUG)"],
            cwd=root, env=env, capture_output=True, text=True, check=True,
        ).stdout.strip()
        seen[value] = out
    assert seen == {None: "False", "0": "False", "false": "False", "1": "True", "on": "True"}


def _requirements(root):
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    text = (root / "requirements.txt").read_text(encoding="utf-8")
    reqs = [Requirement(ln) for ln in _active_requirement_lines(text)]
    return [(canonicalize_name(r.name), r) for r in reqs]


def test_scaffold_requirements_have_one_line_per_distribution(tmp_path):
    """One line per distribution, and no specialist beside ux-compose (D2)."""
    root = create_app(tmp_path / "one")
    assert scan_requirements(root / "requirements.txt").problem is None


class _Dist:
    def __init__(self, direct_url, version="0.2.0"):
        self._direct_url = direct_url
        self.version = version

    def read_text(self, name):
        assert name == "direct_url.json"
        return None if self._direct_url is None else json.dumps(self._direct_url)


def _installed(monkeypatch, direct_url, version="0.2.0"):
    """The checkout's egg-info (PYTHONPATH=src) comes first, as it does in this repo."""
    from ux_compose import scaffold

    found = [_Dist(None, version), _Dist(direct_url, version)]
    monkeypatch.setattr(scaffold.metadata, "distributions", lambda name: found)


def _compose_line(root):
    return dict(_requirements(root))["ux-compose"]


def test_create_app_pins_running_commit(tmp_path, monkeypatch, capsys):
    sha = "0123456789abcdef0123456789abcdef01234567"
    _installed(monkeypatch, {
        "url": "https://github.com/bitplorer/ux-compose.git",
        "vcs_info": {"vcs": "git", "commit_id": sha, "requested_revision": sha},
    })
    req = _compose_line(create_app(tmp_path / "vcs"))
    assert req.url == f"git+https://github.com/bitplorer/ux-compose.git@{sha}"
    assert capsys.readouterr().err == ""


def test_create_app_pins_local_checkout_head(tmp_path, monkeypatch, capsys):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    git = ["git", "-C", str(checkout), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True)
    (checkout / "f").write_text("1", encoding="utf-8")
    subprocess.run([*git, "add", "f"], check=True)
    subprocess.run([*git, "commit", "-qm", "c"], check=True)
    head = subprocess.run(
        [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    _installed(monkeypatch, {"url": checkout.as_uri(), "dir_info": {"editable": True}})

    req = _compose_line(create_app(tmp_path / "unpushed"))
    assert req.url == f"git+https://github.com/bitplorer/ux-compose.git@{head}"
    err = capsys.readouterr().err
    assert f"WARNING: create-app: {head} is on no remote branch" in err
    assert f"pins its HEAD {head}" in err and "uncommitted" not in err

    subprocess.run([*git, "update-ref", "refs/remotes/origin/main", head], check=True)
    create_app(tmp_path / "clean")
    err = capsys.readouterr().err
    assert f"pins its HEAD {head}" in err and "WARNING" not in err

    (checkout / "f").write_text("2", encoding="utf-8")
    create_app(tmp_path / "dirty")
    assert "uncommitted changes are not in it" in capsys.readouterr().err


def test_create_app_refuses_stale_egg_info(tmp_path, monkeypatch, capsys):
    """Review repro: PYTHONPATH=src with an old egg-info and no installed record."""
    from importlib import metadata

    from ux_compose import scaffold
    from ux_compose.cli.create_app import main

    src = tmp_path / "src"
    egg = src / "ux_compose.egg-info"
    egg.mkdir(parents=True)
    (egg / "PKG-INFO").write_text(
        "Metadata-Version: 2.1\nName: ux-compose\nVersion: 0.2.0\n", encoding="utf-8"
    )
    real = metadata.distributions
    monkeypatch.setattr(
        scaffold.metadata, "distributions", lambda name: real(name=name, path=[str(src)])
    )
    assert [d.version for d in scaffold.metadata.distributions("ux-compose")] == ["0.2.0"]

    assert main([str(tmp_path / "bare")]) == 1
    err = capsys.readouterr().err
    assert "no install record (direct_url.json)" in err
    assert "git at a commit" in err and "editable git checkout" in err
    assert not (tmp_path / "bare").exists()


def test_create_app_refuses_unknown_ref(tmp_path, monkeypatch):
    from ux_compose.scaffold import ComposeRefError

    wheel = (tmp_path / "ux_compose-0.2.0-py3-none-any.whl").as_uri()
    _installed(monkeypatch, {"url": wheel, "archive_info": {}})
    with pytest.raises(ComposeRefError, match="has nothing to pin.*editable git checkout"):
        create_app(tmp_path / "wheel")
    assert not (tmp_path / "wheel").exists()
