"""Unit: product Tailwind compiler resolution lives on ux-compose."""
from __future__ import annotations

import stat
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.scaffold import create_app
from ux_compose.tailwind import (
    argv_with_io,
    discover_css_io,
    resolve_tailwind,
    resolve_tailwind_argv,
    standalone_asset_name,
)
from ux_compose.cli_build import run_product_build


def test_env_wins(tmp_path, monkeypatch):
    fake = tmp_path / "tw"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setenv("UXCOMPOSE_TAILWIND", str(fake))
    monkeypatch.delenv("UXDOM_TAILWIND", raising=False)
    monkeypatch.delenv("TAILWINDCSS", raising=False)
    hit = resolve_tailwind(ensure=False)
    assert hit is not None
    assert hit.source == "env"
    assert hit.argv == [str(fake)]


def test_legacy_uxdom_env_alias(tmp_path, monkeypatch):
    fake = tmp_path / "tw"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.delenv("UXCOMPOSE_TAILWIND", raising=False)
    monkeypatch.setenv("UXDOM_TAILWIND", str(fake))
    monkeypatch.delenv("TAILWINDCSS", raising=False)
    hit = resolve_tailwind(ensure=False)
    assert hit is not None
    assert hit.argv == [str(fake)]


def test_no_npx_without_ensure(monkeypatch):
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_DOWNLOAD", "0")
    with patch("ux_compose.tailwind._from_env", return_value=None), patch(
        "ux_compose.tailwind._from_path", return_value=None
    ), patch("ux_compose.tailwind._from_pytailwindcss", return_value=None), patch(
        "ux_compose.tailwind._from_node_modules", return_value=None
    ), patch(
        "ux_compose.tailwind._cached_binary", return_value=None
    ):
        assert resolve_tailwind(ensure=False) is None
        hit = resolve_tailwind(ensure=True)
        if hit is not None:
            assert hit.source == "npx"
            assert "npx" in hit.argv[0]


def test_download_disabled(monkeypatch):
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_DOWNLOAD", "0")
    with patch("ux_compose.tailwind._from_env", return_value=None), patch(
        "ux_compose.tailwind._from_path", return_value=None
    ), patch("ux_compose.tailwind._from_pytailwindcss", return_value=None), patch(
        "ux_compose.tailwind._from_node_modules", return_value=None
    ), patch(
        "ux_compose.tailwind._cached_binary", return_value=None
    ), patch(
        "ux_compose.tailwind._from_npx", return_value=None
    ), patch(
        "ux_compose.tailwind.urllib.request.urlopen"
    ) as urlopen:
        assert resolve_tailwind_argv(ensure=True) is None
        urlopen.assert_not_called()


def test_argv_with_io_watch_vs_minify():
    cmd = argv_with_io(
        ["tw"],
        input_css=Path("in.css"),
        output_css=Path("out.css"),
        watch=True,
    )
    assert cmd[-1] == "--watch"
    cmd = argv_with_io(
        ["tw"],
        input_css=Path("in.css"),
        output_css=Path("out.css"),
        minify=True,
    )
    assert cmd[-1] == "--minify"
    assert "--watch" not in cmd


def test_discover_css_io_matches_scaffold(tmp_path):
    root = create_app(tmp_path / "shop", name="shop")
    io = discover_css_io(root)
    assert io is not None
    inp, out = io
    assert inp == root / "assets" / "css" / "input.css"
    assert out == root / "assets" / "static" / "file" / "css" / "output.css"
    assert out.parent.is_dir()
    css = inp.read_text(encoding="utf-8")
    assert '@import "tailwindcss"' in css
    assert "@source" in css


def test_discover_css_io_matches_compose_webassets(tmp_path):
    from ux_compose.assets import WebAssets

    root = create_app(tmp_path / "wa", name="wa")
    io = discover_css_io(root)
    assert io is not None
    _, out = io
    wa = WebAssets.from_app_root(root, dry_run=True)
    assert wa.output_css == out


def test_standalone_asset_name():
    name = standalone_asset_name()
    assert name.startswith("tailwindcss-"), name


def test_scaffold_document_links_the_compiled_file(tmp_path):
    root = create_app(tmp_path / "d", name="d")
    settings = (root / "settings.py").read_text(encoding="utf-8")
    document = (root / "document.py").read_text(encoding="utf-8")
    assert 'OUTPUT_CSS = "output.css"' in settings
    assert "/css/{OUTPUT_CSS}" in document
    io = discover_css_io(root)
    assert io is not None
    assert io[1].name == "output.css"


def test_product_build_runs_fake_compiler(tmp_path, monkeypatch):
    """End-to-end: create-app layout + resolver + compile writes output.css."""
    root = create_app(tmp_path / "built", name="built")
    fake = tmp_path / "fake-tw"
    fake.write_text(
        "#!/bin/sh\n"
        "out=''\n"
        "while [ $# -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    -o) out=$2; shift 2 ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        "mkdir -p \"$(dirname \"$out\")\"\n"
        "echo '/* fake compiled css */' > \"$out\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("UXCOMPOSE_TAILWIND", str(fake))
    monkeypatch.delenv("UXDOM_TAILWIND", raising=False)
    monkeypatch.delenv("TAILWINDCSS", raising=False)
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_DOWNLOAD", "0")
    monkeypatch.chdir(root)
    report = run_product_build(cwd=root, skip_import=True)
    assert report.ok, report.steps
    assert report.output_css is not None
    assert report.output_css.is_file()
    assert "fake compiled css" in report.output_css.read_text(encoding="utf-8")
