"""Lock concern → file. Next bot: do not fold, do not invent a sibling."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
sys.path.insert(0, str(ROOT / "src"))

OWNERS = (
    "cli.py",
    "cli_build.py",
    "build.py",
    "serve/dev.py",
    "serve/restart.py",
    "serve/state.py",
    "tailwind.py",
    "hmr.py",
    "tunnel.py",
    "scaffold.py",
    "doctor.py",
    "deploy.py",
    "algebra.py",
    "author.py",
    "brand.py",
    "kit_construct.py",
    "surfaces.py",
    "surfaces_host.py",
    "live_client.py",
    "dom.py",
    "progressive.py",
    "attach_notes.py",
    "app.py",
    "component.py",
    "assets.py",
    "kit/overlay.py",
    "kit/copy.py",
    "routing/core.py",
    "routing/host.py",
    "routing/asgi.py",
    "routing/fastapi.py",
    "serve/__init__.py",
    "wire/__init__.py",
    "wire/boot.py",
    "wire/caps.py",
    "wire/cek.py",
    "dx/probe.py",
)


def test_owner_files_exist():
    missing = [name for name in OWNERS if not (SRC / name).is_file()]
    assert not missing, missing


def test_do_not_invent_fold_paths():
    """Dead paths stay dead. serve/ is the owner package; cli.py stays argv at root."""
    assert not (SRC / "kit" / "construct.py").exists()
    assert not (SRC / "cli" / "__init__.py").exists()
    assert not (SRC / "helpers.py").exists()
    assert not (SRC / "chrome.py").exists()
    assert not (SRC / "serve_dev.py").exists()
    assert not (SRC / "serve_restart.py").exists()
    assert not (SRC / "serve_state.py").exists()
    assert not (SRC / "routing" / "adapters").exists()
    assert (SRC / "serve" / "__init__.py").is_file()
    assert (SRC / "algebra.py").is_file()
    assert (SRC / "brand.py").is_file()


def test_architecture_module_map_names_the_pairs():
    text = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "## Module map (concern → file)" in text
    assert "`algebra.py`" in text and "`author.py`" in text
    assert "`brand.py`" in text and "`kit/overlay.py`" in text
    assert "`cli_build.py`" in text and "`build.py`" in text
    assert "`kit_construct.py`" in text
    assert "boot.py` is not the sole importer" in text
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "docs/ARCHITECTURE.md" in agents
    assert "Folding `author.py` into `algebra.py`" in agents


def test_helpers_is_algebra_not_junk_drawer():
    src = (SRC / "algebra.py").read_text(encoding="utf-8")
    assert "Composition algebra" in src
    assert "author.py" in src
    assert "_fragment_for_target" in src
    assert "def bind" in src
    assert "def update_with" in src


def test_author_is_convenience_not_algebra():
    src = (SRC / "author.py").read_text(encoding="utf-8")
    assert "algebra.py" in src
    assert "optional_*" in src or "rise_enter" in src
    assert "def bind" not in src
    assert "def update_with" not in src


def test_chrome_is_get_brand_not_overlay():
    chrome = (SRC / "brand.py").read_text(encoding="utf-8")
    overlay = (SRC / "kit" / "overlay.py").read_text(encoding="utf-8")
    assert "Not OverlayChrome" in chrome
    assert "def brand_wrap" in chrome
    assert "class OverlayChrome" in overlay or "OverlayChrome" in overlay


def test_kit_construct_stays_at_package_root():
    src = (SRC / "kit_construct.py").read_text(encoding="utf-8")
    assert "package **root**" in src or "package root" in src.lower()
    assert "kit/construct.py" in src


def test_isolation_door_is_wire_package():
    boot = (SRC / "wire" / "boot.py").read_text(encoding="utf-8")
    init = (SRC / "wire" / "__init__.py").read_text(encoding="utf-8")
    assert "ONLY place that may import" not in boot
    assert "wire/" in boot
    assert "only modules here may import" in init.lower() or "only modules here may import" in init


def test_tunnel_doc_names_serve_dev():
    src = (SRC / "tunnel.py").read_text(encoding="utf-8")
    assert "serve dev --tunnel" in src
    assert "uxcompose serve --tunnel" not in src


def test_surfaces_scan_not_host_bind():
    scan = (SRC / "surfaces.py").read_text(encoding="utf-8")
    host = (SRC / "surfaces_host.py").read_text(encoding="utf-8")
    assert "surfaces_host" in scan
    assert "Not the surface catalog" in host
    assert "def attach_page_router" in host
    assert "def scan_surfaces" in scan
