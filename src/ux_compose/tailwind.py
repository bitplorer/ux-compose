"""Tailwind CLI resolution — product build DX (this package).

Render (className, ``<link>``) stays on ux-dom.
App folders + compiler I/O live here (``ux_compose.assets.WebAssets``).
Finding, downloading, and invoking the compiler is ``uxcompose build``.
Same split as React vs ``next build``.
Sibling ``--watch`` spawn for ``serve dev`` lives here
(``start_tailwind_watch``).

Order (first hit wins):

1. ``UXCOMPOSE_TAILWIND`` or ``TAILWINDCSS``
2. ``tailwindcss`` on PATH
3. ``pytailwindcss``'s binary for the pinned version, SHA256 checked
4. local ``node_modules/.bin`` / ``@tailwindcss/cli`` (no implicit npx)
5. cached official standalone under ``$XDG_CACHE_HOME/ux-compose/``
   (SHA256 checked on every use; a mismatch is deleted)
6. (only if ``ensure=True``) download the official standalone CLI, SHA256
   checked before it is made executable
7. (only if ``ensure=True`` and the download could not run) pinned
   ``npx @tailwindcss/cli@<version>``. Never after an integrity failure.

The standalone binary runs only when its SHA256 matches
``TAILWIND_STANDALONE_SHA256`` (or ``UXCOMPOSE_TAILWIND_SHA256`` for another
``UXCOMPOSE_TAILWIND_VERSION``). A mismatch raises ``TailwindIntegrityError``.

Never copies library JS. CSS output stays in the app WebAssets tree.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import stat
import sys
import urllib.request
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
    "ensure_tailwind",
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
}


class TailwindIntegrityError(RuntimeError):
    """The standalone CLI cannot be verified, so it is not run."""


@dataclass(frozen=True)
class TailwindResolution:
    """Resolved CLI argv plus where it came from (doctor / banners)."""

    argv: list[str]
    source: str  # env | path | pytailwindcss | node | cache | download | npx


# Removed in 0.2.0. Fail loudly instead of silently ignoring them: e.g.
# UXDOM_TAILWIND_DOWNLOAD=0 forbade network downloads, and dropping it would
# fail open (download + execute a binary).
LEGACY_ENV = {
    "UXDOM_TAILWIND": "UXCOMPOSE_TAILWIND",
    "UXDOM_TAILWIND_DOWNLOAD": "UXCOMPOSE_TAILWIND_DOWNLOAD",
    "UXDOM_TAILWIND_VERSION": "UXCOMPOSE_TAILWIND_VERSION",
    "UXDOM_CACHE": "UXCOMPOSE_CACHE",
}


class LegacyTailwindEnvError(RuntimeError):
    """A removed ``UXDOM_*`` Tailwind variable is set."""


def _reject_legacy_env() -> None:
    found = [name for name in LEGACY_ENV if name in os.environ]
    if found:
        hints = ", ".join(f"{name} -> {LEGACY_ENV[name]}" for name in found)
        raise LegacyTailwindEnvError(
            f"no longer read (removed in 0.2.0): {hints}. "
            "Rename the variable(s) (or unset them) and run again."
        )


def cache_dir() -> Path:
    _reject_legacy_env()
    root = (
        os.environ.get("XDG_CACHE_HOME")
        or os.environ.get("UXCOMPOSE_CACHE")
    )
    base = Path(root) if root else Path.home() / ".cache"
    return base / "ux-compose"


def standalone_asset_name() -> str:
    sysname = platform.system().lower()
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"aarch64", "arm64"} else "x64"
    if sysname == "linux":
        return f"tailwindcss-linux-{arch}"
    if sysname == "darwin":
        return f"tailwindcss-macos-{arch}"
    if sysname.startswith("win"):
        return "tailwindcss-windows-x64.exe"
    return f"tailwindcss-linux-{arch}"


def _split_cmd(value: str) -> list[str]:
    return [part for part in value.split() if part]


def _from_env() -> Optional[TailwindResolution]:
    raw = (
        os.environ.get("UXCOMPOSE_TAILWIND")
        or os.environ.get("TAILWINDCSS")
    )
    if not raw:
        return None
    parts = _split_cmd(raw)
    if not parts:
        return None
    if len(parts) == 1 and Path(parts[0]).is_file():
        return TailwindResolution(parts, "env")
    if shutil.which(parts[0]):
        return TailwindResolution(parts, "env")
    if Path(parts[0]).is_file():
        return TailwindResolution(parts, "env")
    return None


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
    version, expected = _pinned()
    path = Path(get_bin_path(version))
    if path.is_file() and _sha256(path) == expected:
        return TailwindResolution([str(path)], "pytailwindcss")
    return None


def _from_node_modules(start: Optional[Path] = None) -> Optional[TailwindResolution]:
    """Local install only — never implicit npx (that is an ensure last resort)."""
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


def _pinned() -> tuple[str, str]:
    """Return (version, expected SHA256) for the standalone CLI, or refuse."""
    version = (
        os.environ.get("UXCOMPOSE_TAILWIND_VERSION") or TAILWIND_STANDALONE_VERSION
    )
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


def _cached_binary() -> Optional[Path]:
    """The cached standalone CLI if its SHA256 matches. A mismatch is deleted."""
    dest = cache_dir() / standalone_asset_name()
    if not dest.is_file():
        return None
    _, expected = _pinned()
    actual = _sha256(dest)
    if actual != expected:
        dest.unlink(missing_ok=True)
        print(
            f"tailwind: cached {dest} failed sha256 (expected {expected}, "
            f"got {actual}); deleted",
            file=sys.stderr,
        )
        return None
    if not os.access(dest, os.X_OK):
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def _download_allowed() -> bool:
    raw = os.environ.get("UXCOMPOSE_TAILWIND_DOWNLOAD", "1")
    return raw not in {"0", "false", "False"}


def _download_standalone(*, timeout: float = 60.0) -> Optional[Path]:
    """Download, verify, then install into the cache.

    None when downloads are off or the network fails. A digest mismatch
    deletes the file and raises ``TailwindIntegrityError``.
    """
    if not _download_allowed():
        return None
    version, expected = _pinned()
    name = standalone_asset_name()
    dest = cache_dir() / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{TAILWIND_RELEASES_URL}/{version}/{name}"
    tmp = dest.with_suffix(dest.suffix + ".part")
    digest = hashlib.sha256()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ux-compose/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp, tmp.open("wb") as fh:
            for block in iter(lambda: resp.read(1 << 20), b""):
                digest.update(block)
                fh.write(block)
    except Exception:
        tmp.unlink(missing_ok=True)
        return None
    actual = digest.hexdigest()
    if actual != expected:
        tmp.unlink(missing_ok=True)
        raise TailwindIntegrityError(
            f"Tailwind download failed sha256: expected {expected}, got {actual} "
            f"from {url}. The file was deleted and nothing was run."
        )
    tmp.chmod(tmp.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    tmp.replace(dest)
    print(f"tailwind: downloaded {name} {version} sha256 {actual} ok", file=sys.stderr)
    return dest


def _from_npx() -> Optional[TailwindResolution]:
    npx = shutil.which("npx")
    if not npx:
        return None
    pin = TAILWIND_STANDALONE_VERSION.lstrip("v")
    return TailwindResolution(
        [npx, "--yes", "-p", f"@tailwindcss/cli@{pin}", "-p", f"tailwindcss@{pin}", "tailwindcss"],
        "npx",
    )


def resolve_tailwind(
    *,
    cwd: Optional[Path] = None,
    ensure: bool = False,
) -> Optional[TailwindResolution]:
    """Return the first available Tailwind CLI, or None if unavailable.

    Raises ``LegacyTailwindEnvError`` if a removed ``UXDOM_*`` variable is set,
    and ``TailwindIntegrityError`` if the standalone CLI cannot be verified.
    """
    _reject_legacy_env()
    cwd = Path(cwd).resolve() if cwd is not None else None
    for finder in (_from_env, _from_path, _from_pytailwindcss):
        hit = finder()
        if hit:
            return hit
    hit = _from_node_modules(cwd)
    if hit:
        return hit
    cached = _cached_binary()
    if cached:
        return TailwindResolution([str(cached)], "cache")
    if ensure:
        downloaded = _download_standalone()
        if downloaded:
            return TailwindResolution([str(downloaded)], "download")
        npx = _from_npx()
        if npx:
            return npx
    return None


def resolve_tailwind_argv(
    *,
    cwd: Optional[Path] = None,
    ensure: bool = False,
) -> Optional[list[str]]:
    """Return argv prefix for the Tailwind CLI, or None if unavailable."""
    hit = resolve_tailwind(cwd=cwd, ensure=ensure)
    return list(hit.argv) if hit else None


def ensure_tailwind(*, cwd: Optional[Path] = None) -> list[str]:
    """Like ``resolve_tailwind_argv(ensure=True)`` but raises if missing."""
    argv = resolve_tailwind_argv(cwd=cwd, ensure=True)
    if not argv:
        raise FileNotFoundError(
            "Tailwind CLI not found. Install one of: "
            "npm i -D @tailwindcss/cli  ·  "
            "or put `tailwindcss` on PATH. "
            "`uxcompose build` can also download the official standalone CLI, "
            "SHA256-verified (set UXCOMPOSE_TAILWIND_DOWNLOAD=0 to disable)."
        )
    return argv


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
    except TailwindIntegrityError as exc:
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
            cmd, cwd=str(root), env=env, stdin=subprocess.DEVNULL
        )
    except OSError as exc:
        print(f"CSS: sibling --watch spawn failed: {exc}", file=sys.stderr)
        return None
    print(f"CSS: tailwind --watch ({hit.source}) → {output_css}")
    return proc
