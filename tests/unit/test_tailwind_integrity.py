"""Unit: the standalone Tailwind CLI runs only after its SHA256 matches.

Offline. ``urlopen`` is replaced by a fake that serves bytes; nothing leaves
the process.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path

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
    with pytest.raises(tw.TailwindIntegrityError) as exc:
        tw.resolve_tailwind(ensure=True)
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


def test_no_npx_ever(only_download, monkeypatch, tmp_path):
    """npx is not a resolver step: downloads off + npx on PATH -> clear error."""
    import subprocess

    monkeypatch.setenv("UXCOMPOSE_TAILWIND_DOWNLOAD", "0")
    monkeypatch.setattr(tw.shutil, "which", lambda name: f"/bin/{name}")
    spawned = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: spawned.append(a))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: spawned.append(a))
    with pytest.raises(FileNotFoundError) as exc:
        tw.resolve_tailwind(ensure=True)
    msg = str(exc.value)
    assert "UXCOMPOSE_TAILWIND_DOWNLOAD=0" in msg and "UXCOMPOSE_TAILWIND" in msg
    assert spawned == []
    src = (Path(tw.__file__).parent / "tailwind.py").read_text(encoding="utf-8")
    build = (Path(tw.__file__).parent / "cli" / "product_build.py").read_text(encoding="utf-8")
    assert "npx" not in src and "npx" not in build


@pytest.mark.parametrize(
    "system, machine",
    [("FreeBSD", "amd64"), ("Linux", "riscv64"), ("Windows", "ARM64"), ("Linux", "i686")],
)
def test_unsupported_platform_fails_closed(only_download, monkeypatch, system, machine):
    monkeypatch.setattr(tw.platform, "system", lambda: system)
    monkeypatch.setattr(tw.platform, "machine", lambda: machine)
    fetch = FakeFetch(GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", fetch)
    with pytest.raises(tw.TailwindIntegrityError) as exc:
        tw.resolve_tailwind(ensure=True)
    assert f"{system}/{machine}" in str(exc.value)
    assert "UXCOMPOSE_TAILWIND" in str(exc.value)
    assert fetch.urls == []


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


class SlowBody:
    """A response body that trickles out, so parallel downloads overlap."""

    def __init__(self, payload: bytes):
        self.chunks = [payload[i : i + 4] for i in range(0, len(payload), 4)]

    def read(self, size=-1):
        import time

        time.sleep(0.002)
        return self.chunks.pop(0) if self.chunks else b""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_parallel_cold_cache_downloads_all_succeed(only_download, monkeypatch):
    """CI matrices / make -j share one cache: every build gets a verified CLI."""
    from concurrent.futures import ThreadPoolExecutor

    _trust(monkeypatch, GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", lambda req, timeout=None: SlowBody(GOOD))
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: tw.resolve_tailwind(ensure=True), range(6)))
    assert all(hit is not None and hit.argv == [str(only_download)] for hit in results)
    assert only_download.read_bytes() == GOOD
    assert os.access(only_download, os.X_OK)
    assert [p.name for p in only_download.parent.iterdir()] == [only_download.name]


def test_download_error_keeps_cause_and_requested_version(only_download, monkeypatch):
    import urllib.error

    monkeypatch.setenv("UXCOMPOSE_TAILWIND_VERSION", "v9.9.9")
    monkeypatch.setenv("UXCOMPOSE_TAILWIND_SHA256", _sha(GOOD))
    cause = urllib.error.URLError("connection refused")

    def fail(req, timeout=None):
        raise cause

    monkeypatch.setattr(tw.urllib.request, "urlopen", fail)
    with pytest.raises(FileNotFoundError) as exc:
        tw.resolve_tailwind(ensure=True)
    msg = str(exc.value)
    assert "v9.9.9" in msg and tw.TAILWIND_STANDALONE_VERSION not in msg
    assert "connection refused" in msg
    assert f"{tw.TAILWIND_RELEASES_URL}/v9.9.9/{tw.standalone_asset_name()}" in msg
    assert exc.value.__cause__ is cause
    assert list(only_download.parent.iterdir()) == []


def test_tailwindcss_alias_is_not_read(tmp_path, monkeypatch):
    """One knob: UXCOMPOSE_TAILWIND. TAILWINDCSS is not an alias for it."""
    fake = tmp_path / "tw"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.delenv("UXCOMPOSE_TAILWIND", raising=False)
    monkeypatch.setenv("TAILWINDCSS", str(fake))
    assert tw._from_env() is None
    src = Path(tw.__file__).read_text(encoding="utf-8")
    assert "TAILWINDCSS" not in src.replace("TAILWINDCSS_", "")


def test_unusable_uxcompose_tailwind_is_an_error(monkeypatch):
    """A set knob that points nowhere must not silently fall through to a download."""
    monkeypatch.setenv("UXCOMPOSE_TAILWIND", "/nonexistent/tailwindcss")
    with pytest.raises(FileNotFoundError, match="/nonexistent/tailwindcss"):
        tw.resolve_tailwind(ensure=True)


@pytest.mark.parametrize("machine, arch", [("x86_64", "x64"), ("aarch64", "arm64")])
def test_musl_linux_gets_the_musl_asset(monkeypatch, machine, arch):
    monkeypatch.setattr(tw.platform, "system", lambda: "Linux")
    monkeypatch.setattr(tw.platform, "machine", lambda: machine)
    monkeypatch.setattr(tw, "_is_musl", lambda: True)
    name = tw.standalone_asset_name()
    assert name == f"tailwindcss-linux-{arch}-musl"
    assert len(tw.TAILWIND_STANDALONE_SHA256[name]) == 64
    monkeypatch.setattr(tw, "_is_musl", lambda: False)
    assert tw.standalone_asset_name() == f"tailwindcss-linux-{arch}"


def test_is_musl_detects_the_loader(tmp_path, monkeypatch):
    monkeypatch.setattr(tw.platform, "libc_ver", lambda: ("", ""))
    assert tw._is_musl(lib=tmp_path) is False
    (tmp_path / "ld-musl-x86_64.so.1").write_bytes(b"")
    assert tw._is_musl(lib=tmp_path) is True
    monkeypatch.setattr(tw.platform, "libc_ver", lambda: ("glibc", "2.39"))
    assert tw._is_musl(lib=tmp_path) is False


def test_pytailwindcss_does_not_preempt_node_modules(tmp_path, monkeypatch):
    """pytailwindcss without its binary must not raise before node_modules is tried."""
    import sys
    import types

    monkeypatch.setenv("UXCOMPOSE_TAILWIND_VERSION", "latest")
    fake = types.ModuleType("pytailwindcss")
    fake.get_bin_path = lambda version="latest": tmp_path / "none" / version / "tailwindcss"
    monkeypatch.setitem(sys.modules, "pytailwindcss", fake)
    assert tw._from_pytailwindcss() is None


def test_product_build_reports_a_binary_that_cannot_run(tmp_path, monkeypatch):
    from ux_compose.cli.product_build import run_product_build
    from ux_compose.scaffold import create_app

    root = create_app(tmp_path / "app", name="app")
    monkeypatch.setattr(
        tw, "resolve_tailwind",
        lambda **k: tw.TailwindResolution([str(tmp_path / "missing-tw")], "cache"),
    )
    report = run_product_build(cwd=root, skip_import=True)
    step = next(s for s in report.steps if s.name == "tailwind")
    assert not step.ok and "missing-tw" in step.detail


class InterruptedBody(SlowBody):
    """Serves one block, then the user presses Ctrl-C (or the process is told to exit)."""

    def __init__(self, payload: bytes, raised: type[BaseException]):
        super().__init__(payload)
        self.raised = raised

    def read(self, size=-1):
        if len(self.chunks) < 2:
            raise self.raised
        return self.chunks.pop(0)


@pytest.mark.parametrize("raised", [KeyboardInterrupt, SystemExit])
def test_interrupted_download_leaves_no_temp_file(only_download, monkeypatch, raised):
    """#120: try/finally, not except OSError — Ctrl-C must not strand a .part file."""
    _trust(monkeypatch, GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", lambda req, timeout=None: InterruptedBody(GOOD, raised))
    with pytest.raises(raised):
        tw.resolve_tailwind(ensure=True)
    assert list(only_download.parent.iterdir()) == []


def test_interrupt_just_after_the_temp_file_is_created_leaves_none(only_download, monkeypatch):
    """#149 review: a signal landing as the temp file is created must not strand it.

    The SIGINT and SIGTERM handlers raise at the next bytecode, which can be
    before the download has bound the new file's name.
    """
    import signal

    _trust(monkeypatch, GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", lambda req, timeout=None: io.BytesIO(GOOD))
    real_open = os.open

    def open_then_interrupt(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if str(path).endswith(".part"):
            os.close(fd)
            raise KeyboardInterrupt
        return fd

    before = signal.getsignal(signal.SIGTERM)
    monkeypatch.setattr(tw.os, "open", open_then_interrupt)
    with pytest.raises(KeyboardInterrupt):
        tw.resolve_tailwind(ensure=True)
    assert list(only_download.parent.iterdir()) == []
    assert signal.getsignal(signal.SIGTERM) is before


_STALLED_DOWNLOAD = """
import sys, time
import ux_compose.tailwind as tw

class Stalled:
    def __init__(self):
        self.sent = False
    def read(self, size=-1):
        if not self.sent:
            self.sent = True
            return b"#!/bin/sh\\n"
        print("stalled", flush=True)
        # Short sleeps, not one sleep(60): CPython runs the handler between
        # bytecodes, so a signal landing just before one long sleep began
        # waited out the whole minute (the test's 30 s timeout).
        for _ in range(1200):
            time.sleep(0.05)
        return b""
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False

tw.urllib.request.urlopen = lambda req, timeout=None: Stalled()
tw.TAILWIND_STANDALONE_SHA256[tw.standalone_asset_name()] = "0" * 64
tw.resolve_tailwind(ensure=True)
"""


@pytest.mark.skipif(os.name != "posix", reason="SIGTERM is POSIX")
@pytest.mark.parametrize("signame", ["SIGTERM", "SIGHUP"])
def test_terminated_download_leaves_no_temp_file(only_download, signame):
    """#140: SIGTERM (docker stop, systemd, ``timeout``) cleans up like Ctrl-C, then still ends by that signal."""
    import signal
    import subprocess
    import sys

    env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
    proc = subprocess.Popen(
        [sys.executable, "-c", _STALLED_DOWNLOAD], env=env, stdout=subprocess.PIPE, text=True
    )
    try:
        assert proc.stdout.readline().strip() == "stalled"
        assert [p.suffix for p in only_download.parent.iterdir()] == [".part"]
        proc.send_signal(getattr(signal, signame))
        assert proc.wait(timeout=30) == -getattr(signal, signame)
    finally:
        proc.kill()
    assert list(only_download.parent.iterdir()) == []


def test_replace_refused_by_a_running_verified_binary_is_success(only_download, monkeypatch):
    """#120: Windows refuses os.replace onto an exe another build is running; it is already verified."""
    _trust(monkeypatch, GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", lambda req, timeout=None: io.BytesIO(GOOD))

    def busy(src, dst):
        Path(dst).write_bytes(GOOD)  # the parallel build that won
        raise PermissionError(13, "The process cannot access the file", str(dst))

    monkeypatch.setattr(tw.os, "replace", busy)
    hit = tw.resolve_tailwind(ensure=True)
    assert hit is not None and hit.argv == [str(only_download)]
    assert [p.name for p in only_download.parent.iterdir()] == [only_download.name]


def test_replace_refused_without_a_verified_destination_fails(only_download, monkeypatch):
    _trust(monkeypatch, GOOD)
    monkeypatch.setattr(tw.urllib.request, "urlopen", lambda req, timeout=None: io.BytesIO(GOOD))

    def busy(src, dst):
        Path(dst).write_bytes(BAD)
        raise PermissionError(13, "denied", str(dst))

    monkeypatch.setattr(tw.os, "replace", busy)
    with pytest.raises(PermissionError):
        tw.resolve_tailwind(ensure=True)
    assert [p.name for p in only_download.parent.iterdir()] == [only_download.name]  # no .part left


@pytest.mark.parametrize(
    "libc, machine, loaders, musl",
    [
        (("glibc", "2.39"), "x86_64", ["ld-musl-x86_64.so.1"], False),  # glibc host with musl installed
        (("", ""), "x86_64", [], False),  # static / unreadable interpreter, no musl loader
        (("", ""), "x86_64", ["ld-musl-x86_64.so.1"], True),  # Alpine
        (("", ""), "aarch64", ["ld-musl-aarch64.so.1"], True),
        (("", ""), "x86_64", ["ld-musl-aarch64.so.1"], False),  # hybrid image: another arch's loader
        (("", ""), "aarch64", ["ld-musl-x86_64.so.1"], False),
    ],
)
def test_musl_detection_inputs(tmp_path, monkeypatch, libc, machine, loaders, musl):
    """#120: the inputs are libc_ver() and the loader for *this* machine; UXCOMPOSE_TAILWIND overrides."""
    monkeypatch.setattr(tw.platform, "libc_ver", lambda: libc)
    monkeypatch.setattr(tw.platform, "machine", lambda: machine)
    for name in loaders:
        (tmp_path / name).write_bytes(b"")
    assert tw._is_musl(lib=tmp_path) is musl


def test_musl_override_is_documented():
    doc = (Path(__file__).resolve().parents[2] / "docs" / "guides" / "TAILWIND.md").read_text(encoding="utf-8")
    assert "picks the wrong asset" in doc and "UXCOMPOSE_TAILWIND=" in doc
