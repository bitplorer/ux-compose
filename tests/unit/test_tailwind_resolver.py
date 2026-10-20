"""Unit: product Tailwind compiler resolution lives on ux-compose."""
from __future__ import annotations

import pytest

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
from ux_compose.cli.product_build import run_product_build


def test_env_wins(tmp_path, monkeypatch):
    fake = tmp_path / "tw"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setenv("UXCOMPOSE_TAILWIND", str(fake))
    hit = resolve_tailwind(ensure=False)
    assert hit is not None
    assert hit.source == "env"
    assert hit.argv == [str(fake)]


LEGACY_ENV = {
    "UXDOM_TAILWIND": "UXCOMPOSE_TAILWIND",
    "UXDOM_TAILWIND_DOWNLOAD": "UXCOMPOSE_TAILWIND_DOWNLOAD",
    "UXDOM_TAILWIND_VERSION": "UXCOMPOSE_TAILWIND_VERSION",
    "UXDOM_CACHE": "UXCOMPOSE_CACHE",
}


@pytest.mark.parametrize("legacy, replacement", sorted(LEGACY_ENV.items()))
def test_legacy_uxdom_env_fails_loudly(legacy, replacement, monkeypatch):
    """0.2.0: a removed UXDOM_* knob must not be silently ignored (fail-open).

    E.g. UXDOM_TAILWIND_DOWNLOAD=0 forbade network downloads; ignoring it would
    download and execute a binary. Resolution refuses and names the new knob.
    """
    import ux_compose.tailwind as tw

    for name in LEGACY_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(legacy, "0")
    with pytest.raises(tw.LegacyTailwindEnvError) as exc:
        resolve_tailwind(ensure=True)
    assert legacy in str(exc.value) and replacement in str(exc.value)
    with pytest.raises(tw.LegacyTailwindEnvError):
        tw.cache_dir()


def test_uxdom_tailwind_owned_is_not_a_knob(monkeypatch):
    """The old UXDOM_TAILWIND_OWNED marker was an output, not a setting."""
    import ux_compose.tailwind as tw

    for name in LEGACY_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("UXDOM_TAILWIND_OWNED", "1")
    tw.cache_dir()


def test_no_uxdom_reads_or_legacy_cache_in_tailwind_source():
    from pathlib import Path

    src = Path(__file__).resolve().parents[2] / "src" / "ux_compose"
    tw = (src / "tailwind.py").read_text(encoding="utf-8")
    assert 'environ.get("UXDOM_' not in tw
    assert "_legacy_cache_dir" not in tw
    assert "UXDOM_" not in (src / "cli/product_build.py").read_text(encoding="utf-8")


def test_download_disabled(monkeypatch):
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_DOWNLOAD", "0")
    with patch("ux_compose.tailwind._from_env", return_value=None), patch(
        "ux_compose.tailwind._from_path", return_value=None
    ), patch("ux_compose.tailwind._from_pytailwindcss", return_value=None), patch(
        "ux_compose.tailwind._from_node_modules", return_value=None
    ), patch(
        "ux_compose.tailwind._cached_binary", return_value=None
    ), patch(
        "ux_compose.tailwind.urllib.request.urlopen"
    ) as urlopen:
        assert resolve_tailwind_argv(ensure=False) is None
        with pytest.raises(FileNotFoundError, match="UXCOMPOSE_TAILWIND_DOWNLOAD=0"):
            resolve_tailwind_argv(ensure=True)
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
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_DOWNLOAD", "0")
    monkeypatch.chdir(root)
    report = run_product_build(cwd=root, skip_import=True)
    assert report.ok, report.steps
    assert report.output_css is not None
    assert report.output_css.is_file()
    assert "fake compiled css" in report.output_css.read_text(encoding="utf-8")
