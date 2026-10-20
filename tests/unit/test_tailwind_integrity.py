"""Unit: the standalone Tailwind CLI runs only after its SHA256 matches.

Offline. ``urlopen`` is replaced by a fake that serves bytes; nothing leaves
the process.
"""
from __future__ import annotations

import hashlib
import io
import os
from unittest.mock import patch

import pytest

import ux_compose.tailwind as tw

GOOD = b"#!/bin/sh\necho good tailwind\n"
BAD = b"#!/bin/sh\necho evil\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FakeFetch:
    """Stands in for ``urllib.request.urlopen``; records the URLs asked for."""

    def __init__(self, payload: bytes):
        self.payload = payload
        self.urls: list[str] = []

    def __call__(self, req, timeout=None):
        self.urls.append(req.full_url)
        return io.BytesIO(self.payload)


@pytest.fixture
def only_download(tmp_path, monkeypatch):
    """Resolver with steps 1-4 empty, a fresh cache, downloads allowed."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    for name in (
        "UXCOMPOSE_TAILWIND_DOWNLOAD",
        "UXCOMPOSE_TAILWIND_VERSION",
        "UXCOMPOSE_TAILWIND_SHA256",
    ):
        monkeypatch.delenv(name, raising=False)
    for finder in ("_from_env", "_from_path", "_from_pytailwindcss", "_from_node_modules"):
        monkeypatch.setattr(tw, finder, lambda *a, **k: None)
    return tw.cache_dir() / tw.standalone_asset_name()


def _trust(monkeypatch, data: bytes) -> None:
    monkeypatch.setitem(tw.TAILWIND_STANDALONE_SHA256, tw.standalone_asset_name(), _sha(data))


def test_wrong_hash_fails_closed(only_download, monkeypatch):
    fetch = FakeFetch(BAD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", fetch)
    with patch.object(tw, "_from_npx") as npx:
        with pytest.raises(tw.TailwindIntegrityError) as exc:
            tw.resolve_tailwind(ensure=True)
        npx.assert_not_called()
    msg = str(exc.value)
    assert tw.TAILWIND_STANDALONE_SHA256[tw.standalone_asset_name()] in msg
    assert _sha(BAD) in msg
    assert fetch.urls[0] in msg
    assert not only_download.exists()
    assert list(only_download.parent.iterdir()) == []


def test_right_hash_is_cached_and_executable(only_download, monkeypatch, capsys):
    _trust(monkeypatch, GOOD)
    fetch = FakeFetch(GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", fetch)
    hit = tw.resolve_tailwind(ensure=True)
    assert hit is not None and hit.source == "download"
    assert hit.argv == [str(only_download)]
    assert only_download.read_bytes() == GOOD
    assert os.access(only_download, os.X_OK)
    assert fetch.urls == [
        f"{tw.TAILWIND_RELEASES_URL}/{tw.TAILWIND_STANDALONE_VERSION}/{tw.standalone_asset_name()}"
    ]
    assert f"sha256 {_sha(GOOD)} ok" in capsys.readouterr().err
    # Second resolve: verified cache, no new download.
    again = tw.resolve_tailwind(ensure=True)
    assert again is not None and again.source == "cache"
    assert len(fetch.urls) == 1


def test_tampered_cache_is_downloaded_again(only_download, monkeypatch):
    _trust(monkeypatch, GOOD)
    only_download.parent.mkdir(parents=True)
    only_download.write_bytes(GOOD + b"x")
    only_download.chmod(0o755)
    fetch = FakeFetch(GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", fetch)
    hit = tw.resolve_tailwind(ensure=True)
    assert hit is not None and hit.source == "download"
    assert len(fetch.urls) == 1
    assert only_download.read_bytes() == GOOD


def test_tampered_cache_is_not_used_without_ensure(only_download, monkeypatch):
    """serve dev (ensure=False) drops a poisoned cache instead of running it."""
    _trust(monkeypatch, GOOD)
    only_download.parent.mkdir(parents=True)
    only_download.write_bytes(BAD)
    only_download.chmod(0o755)
    assert tw.resolve_tailwind(ensure=False) is None
    assert not only_download.exists()


@pytest.mark.parametrize("version", ["latest", "v9.9.9"])
def test_version_without_known_digest_is_refused(only_download, monkeypatch, version):
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_VERSION", version)
    fetch = FakeFetch(GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", fetch)
    with pytest.raises(tw.TailwindIntegrityError, match="UXCOMPOSE_TAILWIND_SHA256"):
        tw.resolve_tailwind(ensure=True)
    assert fetch.urls == []


def test_latest_is_refused_even_with_a_digest(only_download, monkeypatch):
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_VERSION", "latest")
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_SHA256", _sha(GOOD))
    with pytest.raises(tw.TailwindIntegrityError, match="latest"):
        tw.resolve_tailwind(ensure=True)


def test_other_version_with_digest_is_verified(only_download, monkeypatch):
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_VERSION", "v9.9.9")
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_SHA256", _sha(GOOD))
    fetch = FakeFetch(GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", fetch)
    hit = tw.resolve_tailwind(ensure=True)
    assert hit is not None and hit.source == "download"
    assert fetch.urls[0].endswith(f"/v9.9.9/{tw.standalone_asset_name()}")


def test_npx_argv_is_pinned(monkeypatch):
    monkeypatch.delenv("UXCOMPOSE_TAILWIND_VERSION", raising=False)
    monkeypatch.setattr(tw.shutil, "which", lambda name: f"/bin/{name}")
    hit = tw._from_npx()
    assert hit is not None and hit.source == "npx"
    pin = tw.TAILWIND_STANDALONE_VERSION.lstrip("v")
    assert pin == "4.1.12"
    assert hit.argv == [
        "/bin/npx", "--yes",
        "-p", f"@tailwindcss/cli@{pin}",
        "-p", f"tailwindcss@{pin}",
        "tailwindcss",
    ]


@pytest.mark.parametrize(
    "system, machine",
    [
        ("Linux", "x86_64"),
        ("Linux", "aarch64"),
        ("Darwin", "x86_64"),
        ("Darwin", "arm64"),
        ("Windows", "AMD64"),
    ],
)
def test_every_asset_name_has_a_pinned_digest(monkeypatch, system, machine):
    monkeypatch.setattr(tw.platform, "system", lambda: system)
    monkeypatch.setattr(tw.platform, "machine", lambda: machine)
    digest = tw.TAILWIND_STANDALONE_SHA256[tw.standalone_asset_name()]
    assert len(digest) == 64 and int(digest, 16) >= 0


def test_pytailwindcss_binary_runs_only_when_verified(tmp_path, monkeypatch):
    """Never ``python -m pytailwindcss`` (downloads ``latest`` unverified)."""
    import sys
    import types

    monkeypatch.delenv("UXCOMPOSE_TAILWIND_VERSION", raising=False)
    monkeypatch.delenv("UXCOMPOSE_TAILWIND_SHA256", raising=False)
    binary = tmp_path / "bin" / tw.TAILWIND_STANDALONE_VERSION / "tailwindcss"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(BAD)
    fake = types.ModuleType("pytailwindcss")
    fake.get_bin_path = lambda version="latest": tmp_path / "bin" / version / "tailwindcss"
    monkeypatch.setitem(sys.modules, "pytailwindcss", fake)
    _trust(monkeypatch, GOOD)
    assert tw._from_pytailwindcss() is None
    assert binary.exists()  # not ours to delete
    binary.write_bytes(GOOD)
    hit = tw._from_pytailwindcss()
    assert hit is not None and hit.argv == [str(binary)]


def test_product_build_reports_integrity_failure(tmp_path, only_download, monkeypatch):
    """`uxcompose build` fails the tailwind step with the reason, no traceback."""
    from ux_compose.cli.product_build import run_product_build
    from ux_compose.scaffold import create_app

    root = create_app(tmp_path / "app", name="app")
    monkeypatch.setattr(tw.urllib.request, "urlopen", FakeFetch(BAD))
    report = run_product_build(cwd=root, skip_import=True)
    step = next(s for s in report.steps if s.name == "tailwind")
    assert not report.ok and not step.ok
    assert "sha256" in step.detail and _sha(BAD) in step.detail
    assert not only_download.exists()
    assert not (root / "assets" / "static" / "file" / "css" / "output.css").exists()
