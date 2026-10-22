"""Tailwind CLI resolution — product build DX (this package).

Render (className, ``<link>``) stays on ux-dom.
App folders + compiler I/O live here (``ux_compose.assets.WebAssets``).
Finding, downloading, and invoking the compiler is ``uxcompose build``.
Same split as React vs ``next build``.
Sibling ``--watch`` spawn for ``serve dev`` lives here
(``start_tailwind_watch``).

Order (first hit wins):

1. ``UXCOMPOSE_TAILWIND`` (set but unusable is an error)
2. ``tailwindcss`` on PATH
3. ``pytailwindcss``'s binary for the pinned version, SHA256 checked
4. local ``node_modules/.bin`` / ``@tailwindcss/cli``
5. cached official standalone under ``$XDG_CACHE_HOME/ux-compose/``
   (SHA256 checked on every use; a mismatch is deleted)
6. (only if ``ensure=True``) download the official standalone CLI, SHA256
   checked before it is made executable. If that cannot happen,
   ``FileNotFoundError`` names the platform and ``UXCOMPOSE_TAILWIND``.

The standalone binary runs only when its SHA256 matches
``TAILWIND_STANDALONE_SHA256`` (or ``UXCOMPOSE_TAILWIND_SHA256`` for another
``UXCOMPOSE_TAILWIND_VERSION``). A mismatch raises ``TailwindIntegrityError``.

Never copies library JS. CSS output stays in the app WebAssets tree.
"""
from __future__ import annotations

import hashlib
import http.client
import os
import platform
import shutil
import signal
import stat
import sys
import threading
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

__all__ = [
    "TAILWIND_STANDALONE_SHA256",
    "TAILWIND_STANDALONE_VERSION",
    "TailwindIntegrityError",
    "TailwindResolution",
    "argv_with_io",
    "cache_dir",
    "discover_css_io",
    "resolve_tailwind",
    "resolve_tailwind_argv",
    "standalone_asset_name",
    "start_tailwind_watch",
]

# Pinned so serve/dev are reproducible. Another UXCOMPOSE_TAILWIND_VERSION
# also needs UXCOMPOSE_TAILWIND_SHA256; ``latest`` is refused.
TAILWIND_STANDALONE_VERSION = "v4.1.12"
TAILWIND_RELEASES_URL = "https://github.com/tailwindlabs/tailwindcss/releases/download"

# SHA256 of each standalone asset of TAILWIND_STANDALONE_VERSION, from the
# release's published checksum file, retrieved 2026-10-20:
# https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.12/sha256sums.txt
# Each asset was also downloaded and hashed on 2026-10-20: same digests.
# Keys are every name standalone_asset_name() returns.
TAILWIND_STANDALONE_SHA256: dict[str, str] = {
    "tailwindcss-linux-x64": "5eeee66ea237eae9a160fa3314fd0cf76ab993551a99fafb16fa1db6c6b90289",
    "tailwindcss-linux-arm64": "181332974fff1b3423ad75d6a2f1d09adf1ca63eb1324db0afbc4c30ff1ad086",
    "tailwindcss-macos-x64": "fc935d51813442472c2e1b28582fec3df204379e53d5724937d516dd425af37c",
    "tailwindcss-macos-arm64": "7d69be1776bbe8a49e15714d9873d08959c320aff0f0714d8d8e6d9d00d9b543",
    "tailwindcss-windows-x64.exe": "27e14fd9c0872281464da9c0991709e0f7cadedc60e4acfac371299246d54669",
    "tailwindcss-linux-x64-musl": "a8a1926a2951a5da0684c568d612bc0a590600334d3a85d0e63ea90ac7ced2e5",
    "tailwindcss-linux-arm64-musl": "eaedd516e9885a02ca752833b8acbf378c463b89abc1bf00f307fe4f523e1e7f",
}


class TailwindIntegrityError(RuntimeError):
    """The standalone CLI cannot be verified, so it is not run."""


@dataclass(frozen=True)
class TailwindResolution:
    """Resolved CLI argv plus where it came from (doctor / banners)."""

    argv: list[str]
    source: str  # env | path | pytailwindcss | node | cache | download


def cache_dir() -> Path:
    root = (
        os.environ.get("XDG_CACHE_HOME")
        or os.environ.get("UXCOMPOSE_CACHE")
    )
    base = Path(root) if root else Path.home() / ".cache"
    return base / "ux-compose"


def _platform() -> str:
    return f"{platform.system()}/{platform.machine()}"


def _is_musl(lib: Path = Path("/lib")) -> bool:
    """musl Linux: not glibc, and this machine's musl loader (the one the musl
    assets ask for) exists. Another arch's loader (a hybrid image) is not musl.
    A wrong guess is overridden by ``UXCOMPOSE_TAILWIND``.
    """
    if platform.libc_ver()[0] == "glibc":
        return False
    arch = {"amd64": "x86_64", "arm64": "aarch64"}.get(platform.machine().lower(), platform.machine().lower())
    return (lib / f"ld-musl-{arch}.so.1").exists()


def standalone_asset_name() -> str:
    """Official standalone asset for this platform; refuse one with no digest."""
    sysname = platform.system().lower()
    machine = platform.machine().lower()
    arch = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(machine)
    os_name = {"linux": "linux", "darwin": "macos", "windows": "windows"}.get(sysname)
    name = f"tailwindcss-{os_name}-{arch}"
    if os_name == "windows":
        name += ".exe"
    elif os_name == "linux" and _is_musl():
        name += "-musl"
    if name not in TAILWIND_STANDALONE_SHA256:
        raise TailwindIntegrityError(
            f"no verified Tailwind standalone CLI for {_platform()} "
            f"(pinned {TAILWIND_STANDALONE_VERSION} covers "
            f"{', '.join(TAILWIND_STANDALONE_SHA256)}). Set UXCOMPOSE_TAILWIND "
            "to a tailwindcss binary you trust, or put tailwindcss on PATH."
        )
    return name


def _split_cmd(value: str) -> list[str]:
    return [part for part in value.split() if part]


def _from_env() -> Optional[TailwindResolution]:
    raw = os.environ.get("UXCOMPOSE_TAILWIND")
    if not raw:
        return None
    parts = _split_cmd(raw)
    if not parts:
        return None
    if shutil.which(parts[0]) or Path(parts[0]).is_file():
        return TailwindResolution(parts, "env")
    raise FileNotFoundError(
        f"UXCOMPOSE_TAILWIND={raw!r} is not a file or a command on PATH. "
        "Fix it or unset it."
    )


def _from_path() -> Optional[TailwindResolution]:
    found = shutil.which("tailwindcss")
    return TailwindResolution([found], "path") if found else None


def _from_pytailwindcss() -> Optional[TailwindResolution]:
    """pytailwindcss's binary for the pinned version, if its SHA256 matches.

    Never ``python -m pytailwindcss``: it downloads ``latest`` unverified.
    """
    try:
        from pytailwindcss import get_bin_path  # type: ignore[import-not-found]
    except Exception:
        return None
    path = Path(get_bin_path(_version()))
    if path.is_file() and _sha256(path) == _pinned()[1]:
        return TailwindResolution([str(path)], "pytailwindcss")
    return None


def _from_node_modules(start: Optional[Path] = None) -> Optional[TailwindResolution]:
    """Local install only."""
    cur = Path(start or Path.cwd()).resolve()
    for base in [cur, *cur.parents]:
        bin_ = base / "node_modules" / ".bin" / "tailwindcss"
        if bin_.is_file():
            return TailwindResolution([str(bin_)], "node")
        cli = base / "node_modules" / "@tailwindcss" / "cli"
        index = cli / "dist" / "index.mjs"
        if index.is_file() and shutil.which("node"):
            return TailwindResolution(
                [shutil.which("node") or "node", str(index)], "node"
            )
        if base == base.parent:
            break
    return None


def _version() -> str:
    return os.environ.get("UXCOMPOSE_TAILWIND_VERSION") or TAILWIND_STANDALONE_VERSION


def _pinned() -> tuple[str, str]:
    """Return (version, expected SHA256) for the standalone CLI, or refuse."""
    version = _version()
    if version == "latest":
        raise TailwindIntegrityError(
            "UXCOMPOSE_TAILWIND_VERSION=latest is refused: pin a release tag "
            "and set UXCOMPOSE_TAILWIND_SHA256 to its digest."
        )
    expected = os.environ.get("UXCOMPOSE_TAILWIND_SHA256", "").strip().lower()
    if not expected and version == TAILWIND_STANDALONE_VERSION:
        expected = TAILWIND_STANDALONE_SHA256.get(standalone_asset_name(), "")
    if not expected:
        raise TailwindIntegrityError(
            f"no known SHA256 for Tailwind {version} {standalone_asset_name()}: "
            "set UXCOMPOSE_TAILWIND_SHA256 to the digest from that release's "
            "sha256sums.txt."
        )
    return version, expected


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _cached_binary(*, read_only: bool = False) -> Optional[Path]:
    """The cached standalone CLI if its SHA256 matches. A mismatch is deleted.

    ``read_only`` changes nothing in the cache: a mismatch raises
    ``TailwindIntegrityError``, a non-executable file ``FileNotFoundError``.
    """
    dest = cache_dir() / standalone_asset_name()
    if not dest.is_file():
        return None
    _, expected = _pinned()
    actual = _sha256(dest)
    if actual != expected:
        if read_only:
            raise TailwindIntegrityError(
                f"cached {dest} failed sha256 (expected {expected}, got {actual})"
            )
        dest.unlink(missing_ok=True)
        print(
            f"tailwind: cached {dest} failed sha256 (expected {expected}, "
            f"got {actual}); deleted",
            file=sys.stderr,
        )
        return None
    if not os.access(dest, os.X_OK):
        if read_only:
            raise FileNotFoundError(f"cached {dest} is not executable (--check does not chmod)")
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def _download_allowed() -> bool:
    raw = os.environ.get("UXCOMPOSE_TAILWIND_DOWNLOAD", "1")
    return raw not in {"0", "false", "False"}


def _missing(reason: str) -> FileNotFoundError:
    return FileNotFoundError(
        f"Tailwind CLI not found on {_platform()}: {reason}. Set "
        "UXCOMPOSE_TAILWIND to a tailwindcss binary you trust, or put "
        "tailwindcss on PATH."
    )


class _Terminated(BaseException):
    """SIGTERM or SIGHUP arrived while a download was being written."""

    def __init__(self, signum: int):
        super().__init__(signum)
        self.signum = signum


def _on_terminate(signum, frame) -> None:
    raise _Terminated(signum)


@contextmanager
def _terminate_unwinds():
    """SIGTERM and SIGHUP unwind through ``finally`` like Ctrl-C, then end the process by that signal.

    Their default action kills the process with no cleanup (docker stop,
    systemd, ``timeout``). Only a default handler is replaced, on the main
    thread: an app's own handler, or ``nohup``'s ignore, stays as it is.
    """
    saved = {}
    if threading.current_thread() is threading.main_thread():
        for name in ("SIGTERM", "SIGHUP"):
            sig = getattr(signal, name, None)
            if sig is not None and signal.getsignal(sig) is signal.SIG_DFL:
                saved[sig] = signal.signal(sig, _on_terminate)
    try:
        yield
    except _Terminated as stop:
        for sig, handler in saved.items():
            signal.signal(sig, handler)
        saved = {}
        signal.raise_signal(stop.signum)
        raise SystemExit(128 + stop.signum) from None
    finally:
        for sig, handler in saved.items():
            signal.signal(sig, handler)


def _download_standalone(*, timeout: float = 60.0) -> Optional[Path]:
    """Download, verify, then install into the cache.

    None when downloads are off. A failed download raises
    ``FileNotFoundError`` from its cause. A digest mismatch deletes the file
    and raises ``TailwindIntegrityError``.

    Each process writes its own temp file next to the cache entry, verifies
    it, then ``os.replace`` s it in, so parallel builds never share a
    half-written file. The temp file is removed on any exit, Ctrl-C and
    SIGTERM too (``_terminate_unwinds``).
    Windows refuses the replace while another build runs the binary; a
    verified file already there is then the result. The returned path is
    hashed again after the replace.
    """
    if not _download_allowed():
        return None
    version, expected = _pinned()
    name = standalone_asset_name()
    dest = cache_dir() / name
    url = f"{TAILWIND_RELEASES_URL}/{version}/{name}"
    digest = hashlib.sha256()
    # Named before it exists, so ``finally`` sees it even when a signal lands
    # as the file is created.
    tmp: Optional[Path] = dest.parent / f"{name}.{os.urandom(8).hex()}.part"
    with _terminate_unwinds():
        try:
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
                req = urllib.request.Request(url, headers={"User-Agent": "ux-compose/0.1"})
                with urllib.request.urlopen(req, timeout=timeout) as resp, os.fdopen(fd, "wb") as fh:
                    for block in iter(lambda: resp.read(1 << 20), b""):
                        digest.update(block)
                        fh.write(block)
                    fh.flush()
                    os.fsync(fh.fileno())
            except (OSError, http.client.HTTPException) as exc:
                raise _missing(f"downloading Tailwind {version} from {url} failed: {exc}") from exc
            actual = digest.hexdigest()
            if actual != expected:
                raise TailwindIntegrityError(
                    f"Tailwind download failed sha256: expected {expected}, got {actual} "
                    f"from {url}. The file was deleted and nothing was run."
                )
            tmp.chmod(0o755)
            try:
                os.replace(tmp, dest)
            except PermissionError:
                if not (dest.is_file() and _sha256(dest) == expected):
                    raise
            else:
                tmp = None
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
    actual = _sha256(dest)
    if actual != expected:
        raise TailwindIntegrityError(
            f"{dest} changed after it was installed (sha256 {actual}, expected "
            f"{expected}). Nothing was run."
        )
    print(f"tailwind: downloaded {name} {version} sha256 {actual} ok", file=sys.stderr)
    return dest


def resolve_tailwind(
    *,
    cwd: Optional[Path] = None,
    ensure: bool = False,
    read_only: bool = False,
) -> Optional[TailwindResolution]:
    """Return the first available Tailwind CLI.

    Without ``ensure``, None if none is available. With ``ensure``, raises
    ``FileNotFoundError`` when the verified download cannot run.
    ``read_only`` (``build --check``, without ``ensure``) leaves the cache
    as it is: no delete, no chmod.
    Raises ``TailwindIntegrityError`` if the standalone CLI cannot be verified.
    """
    cwd = Path(cwd).resolve() if cwd is not None else None
    for finder in (_from_env, _from_path, _from_pytailwindcss):
        hit = finder()
        if hit:
            return hit
    hit = _from_node_modules(cwd)
    if hit:
        return hit
    cached = _cached_binary(read_only=read_only)
    if cached:
        return TailwindResolution([str(cached)], "cache")
    if ensure:
        downloaded = _download_standalone()
        if downloaded:
            return TailwindResolution([str(downloaded)], "download")
        raise _missing("downloads are off (UXCOMPOSE_TAILWIND_DOWNLOAD=0)")
    return None


def resolve_tailwind_argv(
    *,
    cwd: Optional[Path] = None,
    ensure: bool = False,
) -> Optional[list[str]]:
    """Return argv prefix for the Tailwind CLI (see ``resolve_tailwind``)."""
    hit = resolve_tailwind(cwd=cwd, ensure=ensure)
    return list(hit.argv) if hit else None


def argv_with_io(
    argv: Sequence[str],
    *,
    input_css: Path,
    output_css: Path,
    minify: bool = False,
    watch: bool = False,
) -> list[str]:
    out = list(argv)
    out.extend(["-i", str(input_css), "-o", str(output_css)])
    if minify:
        out.append("--minify")
    elif watch:
        out.append("--watch")
    return out


def discover_css_io(root: Path) -> Optional[tuple[Path, Path]]:
    """Resolve input/output CSS for a product tree.

    Product convention SSoT: ``WebAssets`` on this package.
    Input is ``assets/css/input.css``. Output is ``WebAssets.output_css``
    (``assets/static/file/css/output.css``), the folder ``/css`` mounts.
    """
    root = Path(root)
    from ux_compose.assets import WebAssets

    wa = WebAssets.from_app_root(root, dry_run=True)
    input_css = wa.input_css
    if not input_css.is_file():
        alt = wa.dir / "input.css"
        if alt.is_file():
            input_css = alt
        else:
            return None
    return input_css, wa.output_css


def start_tailwind_watch(*, cwd: str | None = None):
    """Sibling Tailwind --watch. Lives here, not in cli.py or hmr.py.

    Returns a Popen or None. None is quiet when the tree has no input.css.
    The Popen leads its own process group; serve dev stops that group.
    Missing CLI is a warning, not a failed serve.
    """
    import subprocess

    root = Path(cwd or ".").resolve()
    io = discover_css_io(root)
    if io is None:
        return None
    input_css, output_css = io
    try:
        hit = resolve_tailwind(cwd=root, ensure=False)
    except (TailwindIntegrityError, FileNotFoundError) as exc:
        print(f"CSS: {exc} — skip sibling --watch", file=sys.stderr)
        return None
    if hit is None:
        print(
            "CSS: Tailwind CLI not found — skip sibling --watch "
            "(run uxcompose build to download the verified standalone CLI)",
            file=sys.stderr,
        )
        return None
    output_css.parent.mkdir(parents=True, exist_ok=True)
    cmd = argv_with_io(
        hit.argv,
        input_css=input_css,
        output_css=output_css,
        minify=False,
        watch=True,
    )
    cmd = [("--watch=always" if part == "--watch" else part) for part in cmd]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(root), env.get("PYTHONPATH", "")])
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(root),
            env=env,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        print(f"CSS: sibling --watch spawn failed: {exc}", file=sys.stderr)
        return None
    print(f"CSS: tailwind --watch ({hit.source}) → {output_css}")
    return proc
