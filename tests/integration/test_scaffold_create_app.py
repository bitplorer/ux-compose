"""Integration: create-app emits the complete product path."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app
from ux_compose.doctor import scan_isolation, scan_dual_document


def test_create_app_layout(tmp_path):
    dest = tmp_path / "demo"
    root = create_app(dest, name="demo", level="auto", host="auto")
    assert (root / "app.py").is_file()
    assert (root / "settings.py").is_file()
    assert (root / "document.py").is_file()
    assert (root / "routes" / "hello.py").is_file()
    assert (root / "README.md").is_file()
    assert (root / "requirements.txt").is_file()
    assert (root / "assets" / "css" / "input.css").is_file()
    text = (root / "app.py").read_text(encoding="utf-8")
    assert "build(" in text
    assert "asgi" in text
    assert "document=document" in text
    assert "from document import document" in text


def test_create_app_teaches_document_and_settings(tmp_path):
    root = create_app(tmp_path / "shop", name="shop", level=1, host="fastapi")
    settings = (root / "settings.py").read_text(encoding="utf-8")
    document = (root / "document.py").read_text(encoding="utf-8")
    hello = (root / "routes" / "hello.py").read_text(encoding="utf-8")
    css = (root / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    req = (root / "requirements.txt").read_text(encoding="utf-8")

    assert "BASE_DIR" in settings
    assert "WebAssets" in settings
    assert "DEBUG" in settings
    assert "import ux_channel" not in settings
    assert "from ux_channel" not in settings

    assert "Document(" in document
    assert ".use(" in document
    assert "def page(" in document
    assert "XElement" in document
    assert "Csp" in document
    assert "import ux_channel" not in document
    assert "from ux_channel" not in document

    assert "class Hello" in hello
    assert "def get(" in hello
    assert "from document import page" in hello
    assert "className" in hello

    assert '@import "tailwindcss"' in css
    assert "@source" in css

    assert "ux-compose" in req
    assert "ux-dom" in req


def test_create_app_isolation_and_single_document(tmp_path):
    root = create_app(tmp_path / "iso", name="iso")
    files = list(root.rglob("*.py"))
    assert scan_isolation(files) == []
    # One Document() in document.py; page() reuses it
    assert scan_dual_document(files) == []
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
