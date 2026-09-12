"""Integration: create-app emits the complete product path."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app
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
    assert "from ux_dom.runtime import" in document
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

    assert "ux-compose" in req
    assert "ux-behavior" in req
    assert "fastapi" in req
    assert "uvicorn" in req
    active = [
        ln.strip()
        for ln in req.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    assert any(
        "ux-compose" in ln and "git+https://github.com/bitplorer/ux-compose.git@" in ln
        and "24a182f" in ln
        for ln in active
    )
    assert any("ux-behavior" in ln for ln in active)
    assert any("fastapi" in ln for ln in active)
    assert any(ln.startswith("uvicorn") for ln in active)
    assert any(ln.startswith("cek-host") and ">=0.1.3" in ln for ln in active)
    assert any(ln.startswith("cek-surface") and ">=0.1.3" in ln for ln in active)
    assert any("ux-channel" in ln for ln in active)
    assert any("d0412c6" in ln for ln in active), "Channel VCS pin must be ≥ d0412c6 (Soft 3+4)"
    assert any("ux-dom" in ln and "2e894cd" in ln for ln in active)
    assert any("ux-motion" in ln and "67ff3f0" in ln for ln in active)
    assert any("ux-behavior" in ln and "793f120" in ln for ln in active)
    assert "subdirectory=python" in req
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
    """pip install -r requirements.txt must name the full pinned stack."""
    root = create_app(tmp_path / "caps", name="caps")
    req = (root / "requirements.txt").read_text(encoding="utf-8")
    app_py = (root / "app.py").read_text(encoding="utf-8")
    active = _active_requirement_lines(req)

    assert 'cek="require"' in app_py
    assert "wrap=document" in app_py
    assert any(ln.startswith("cek-host") and ">=0.1.3" in ln for ln in active)
    assert any(ln.startswith("cek-surface") and ">=0.1.3" in ln for ln in active)
    assert any("ux-channel" in ln and "d0412c6" in ln for ln in active)
    assert any("ux-dom" in ln and "2e894cd" in ln for ln in active)
    assert any("ux-behavior" in ln and "793f120" in ln for ln in active)
    assert any("ux-motion" in ln and "67ff3f0" in ln for ln in active)
    assert "subdirectory=python" in req
    assert any(ln.startswith("fastapi") for ln in active)
    assert any(ln.startswith("uvicorn") for ln in active)
    assert any(
        "ux-compose" in ln and "git+https://github.com/bitplorer/ux-compose.git@" in ln
        and "24a182f" in ln
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
