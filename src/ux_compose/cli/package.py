"""``uxcompose build --package`` / ``--archive`` — the runnable bundle.

``OUT/<name>/`` holds an allowlist of the app's regular files: every
``*.py``, the requirements file and deploy configs, and the source/asset
file types under ``routes/``, ``components/``, ``assets/`` and ``deploy/``.
Before it is moved into place, the entry must import from the bundle alone. Three files are
generated: ``run.sh``, ``README.RUN.txt``, ``MANIFEST.json``. Library JS is
not vendored; the installed packages serve it. Nothing in the bundle names
the build machine, and the archive is byte-identical for the same inputs.

Safety: ``--out`` must be a new, empty, or dedicated bundle directory (only
bundles this tool marked), never the app or one of its parents. The bundle
is assembled in a temp dir inside ``--out`` and renamed into place; only a
directory carrying this tool's MANIFEST marker is ever replaced.
"""
from __future__ import annotations

import fnmatch
import gzip
import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path

from ux_compose.doctor import BUNDLE_GENERATOR, SOURCE_DIRS, bundle_changes, is_bundle, is_skipped_dir

ROOT_FILES = (
    "requirements.txt",
    "README.md",
    "Dockerfile",
    ".dockerignore",
    "fly.toml",
    "render.yaml",
    "railway.json",
)
_SOURCE = {".py", ".html", ".css", ".js", ".json", ".md", ".txt"}
_ASSET = {
    ".css", ".js", ".mjs", ".map", ".html", ".json", ".txt", ".xml", ".webmanifest",
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".webm", ".mp3", ".pdf",
}  # fmt: skip
_DEPLOY = {".service", ".socket", ".timer", ".conf", ".toml", ".yaml", ".yml", ".json", ".sh", ".txt", ".md"}
# Directory → file suffixes a bundle may carry from it. Everything else is left out and listed.
ALLOWED = {"routes": _SOURCE, "components": _SOURCE, "assets": _ASSET, "deploy": _DEPLOY}
assert set(ALLOWED) == SOURCE_DIRS
# Key-shaped names; inside an allowed directory they refuse the build.
KEY_NAMES = (
    ".env", ".env.*", "*.env", "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*",
    "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore", "*.kdbx", "*.gpg",
    ".netrc", ".npmrc", ".pypirc", ".htpasswd",
)  # fmt: skip
_KEY_CONTENT = (b"PRIVATE KEY-----", b'"private_key":')
DISTS = ("ux-compose", "ux-dom", "ux-channel", "ux-behavior", "ux-motion")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_TMP = ".uxcompose-"

RUN_SH = """\
#!/bin/sh
set -eu
cd "$(dirname "$0")"
PORT="${{PORT:-8080}}"
HOST="${{HOST:-0.0.0.0}}"
if [ -d .venv ]; then
  . .venv/bin/activate
fi
# Channel refuses to boot without UX_CHANNEL_SECRET: say why in one line.
python3 -c 'import sys; from ux_compose.doctor import secret_readiness; sys.exit(secret_readiness())'
exec uvicorn {entry} --app-dir . --host "$HOST" --port "$PORT"
"""

README_RUN = """\
ux-compose runnable bundle: {name}

  pip install -r requirements.txt
  export UX_CHANNEL_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  ./run.sh                      # PORT (default 8080), HOST (default 0.0.0.0)

run.sh uses the python3 and uvicorn on PATH (activating ./.venv when it
exists): install requirements.txt into that environment. Keep a .venv in a
copy of this directory or an unpacked archive, not here; see the end.

Library JavaScript (x_element.js, the Channel client) is NOT vendored into
this bundle. The installed packages serve it from site-packages.
MANIFEST.json lists every copied file with its sha256 and the commits of
ux-compose and its specialists this bundle was built and checked with.

uxcompose build regenerates this directory, and refuses to replace it once
it holds anything else (a .venv, an .env, an edit): keep those elsewhere.
"""


class PackageError(RuntimeError):
    """The bundle would not run, would not be what this build checked, or is unsafe to write."""


@dataclass
class Collected:
    files: list[Path] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)


@dataclass
class Bundle:
    path: Path
    archive: Path | None = None
    excluded: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _key_name(name: str) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in KEY_NAMES)


def _key_content(path: Path) -> bool:
    with open(path, "rb") as fh:
        head = fh.read(1 << 16)
    return any(marker in head for marker in _KEY_CONTENT)


def collect(root: Path, *, skip: Path | None = None) -> Collected:
    """Allowlisted regular files to copy; everything else excluded (listed) or refused.

    Copied: every ``*.py`` under the root (outside excluded dirs), root
    ``ROOT_FILES``, and ``ALLOWED`` suffixes under ``routes/``,
    ``components/``, ``assets/``, ``deploy/``. Excluded: tool caches, real
    venvs, validated bundles, ``skip`` (the ``--out`` dir), and every other
    file. Refused: any symlink, a key-shaped file (name or content) inside an
    allowed dir, a copied file holding a private key or with more than one
    hardlink (the same file under another name, which may be anything). A
    top-level allowed dir is never skipped as a venv or bundle: two planted
    files must not hide ``routes/`` from the bundle and from ``doctor``.
    """
    root = root.resolve()
    out = Collected()

    def visit(path: Path, allowed: set[str] | None) -> None:
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            out.refused.append(f"{rel} (symlink)")
        elif path.is_dir():
            source = path.parent == root and path.name in SOURCE_DIRS
            if path == skip or is_skipped_dir(path, source=source):
                out.excluded.append(f"{rel}/")
                return
            if allowed is None and path.parent == root:
                allowed = ALLOWED.get(path.name)
            for child in sorted(path.iterdir()):
                visit(child, allowed)
        elif allowed is not None and (_key_name(path.name) or _key_content(path)):
            out.refused.append(f"{rel} (key-shaped)")
        elif (
            path.suffix == ".py"
            or (allowed is not None and path.suffix.lower() in allowed)
            or (path.parent == root and path.name in ROOT_FILES)
        ):
            if _key_content(path):
                out.refused.append(f"{rel} (holds a private key)")
            elif (links := path.stat().st_nlink) > 1:
                out.refused.append(f"{rel} (hardlinked, {links} links)")
            else:
                out.files.append(Path(rel))
        else:
            out.excluded.append(rel)

    for child in sorted(root.iterdir()):
        visit(child, None)
    return out


def _is_bundle_archive(path: Path) -> bool:
    if path.is_symlink() or not path.is_file() or not path.name.endswith(".tar.gz"):
        return False
    try:
        with tarfile.open(path, "r:gz") as tf:
            fh = tf.extractfile(f"{path.name[: -len('.tar.gz')]}/MANIFEST.json")
            manifest = json.loads(fh.read()) if fh else None
    except (OSError, tarfile.TarError, KeyError, ValueError):
        return False
    return isinstance(manifest, dict) and manifest.get("generator") == BUNDLE_GENERATOR


def check_out(root: Path, out_dir: Path, name: str) -> Path:
    """The resolved ``--out``, or ``PackageError`` before anything is written or deleted."""
    if not _NAME.fullmatch(name):
        raise PackageError(f"--name {name!r} must be one plain path segment (letters, digits, . _ -)")
    root, out = root.resolve(), out_dir.resolve()
    if root == out or root.is_relative_to(out):
        raise PackageError(
            f"--out {out_dir} is the app directory or one of its parents; "
            "pick a dedicated bundle directory such as dist"
        )
    if out.is_relative_to(root) and out.relative_to(root).parts[0] in ALLOWED:
        raise PackageError(f"--out {out_dir} is inside the app source ({out.relative_to(root).parts[0]}/)")
    if out.exists():
        if not out.is_dir():
            raise PackageError(f"--out {out_dir} is not a directory")
        dest = out / name
        if dest.is_dir() and not dest.is_symlink() and (changes := bundle_changes(dest, allow_venv=False)):
            shown = ", ".join(changes[:5]) + (", …" if len(changes) > 5 else "")
            where = dest.relative_to(root) if dest.is_relative_to(root) else dest
            raise PackageError(
                f"{where.as_posix()} holds {shown}: not written by uxcompose, "
                "so it is not replaced; move them out or pick another --out"
            )
        foreign = [
            p.name
            for p in sorted(out.iterdir())
            if not (
                (p.is_dir() and not p.is_symlink() and is_bundle(p, allow_venv=False))
                or _is_bundle_archive(p)
                or (p.name.startswith(_TMP) and p.is_dir() and not p.is_symlink())
            )
        ]
        if foreign:
            shown = ", ".join(foreign[:5]) + (", …" if len(foreign) > 5 else "")
            raise PackageError(
                f"--out {out_dir} is not a dedicated bundle directory (it holds {shown}); "
                "uxcompose only replaces bundles it wrote. Pick a new or empty directory"
            )
    return out


def _installed(name: str) -> dict:
    dist = metadata.distribution(name)
    info = json.loads(dist.read_text("direct_url.json") or "{}")
    return {"version": dist.version, "vcs_commit": (info.get("vcs_info") or {}).get("commit_id")}


def _dirty_checkout() -> str | None:
    """The editable ux-compose checkout path when it has uncommitted tracked changes."""
    from urllib.parse import urlparse
    from urllib.request import url2pathname

    from ux_compose.scaffold import _git

    for dist in metadata.distributions(name="ux-compose"):
        info = json.loads(dist.read_text("direct_url.json") or "{}")
        if "dir_info" in info and info.get("url", "").startswith("file:"):
            checkout = url2pathname(urlparse(info["url"]).path)
            if _git(Path(checkout), "status", "--porcelain", "--untracked-files=no"):
                return checkout
    return None


def _requirement_lines(root: Path) -> dict[int, str]:
    """Logical lines of ``root/requirements.txt``; refuses ``-r`` / ``-c`` includes."""
    from ux_compose.scaffold import _COMMENT, _logical_lines

    req = root / "requirements.txt"
    if not req.is_file():
        return {}
    lines = {n: _COMMENT.sub("", raw).strip() for n, raw in _logical_lines(req.read_text(encoding="utf-8"))}
    if any(line.startswith(("-r", "--requirement", "-c", "--constraint")) for line in lines.values()):
        raise PackageError(
            "requirements.txt includes other files (-r / -c); a bundle ships "
            "requirements.txt alone, so write those lines into it"
        )
    return lines


def _resolved(root: Path, warnings: list[str]) -> dict:
    """The ux-compose line in requirements.txt must be the ux-compose this build runs.

    Specialists come with that line, so their commits are the ones this
    interpreter checked the app with.
    """
    from ux_compose.scaffold import (
        ComposeRefError,
        compose_requirement,
        scan_requirements,
    )

    lines = _requirement_lines(root)
    pinned = lines[int(scan_requirements(root / "requirements.txt").names["ux-compose"].rpartition(":")[2])]
    try:
        running, note = compose_requirement()
    except ComposeRefError as exc:
        raise PackageError(str(exc)) from None
    if pinned != running:
        raise PackageError(
            f"requirements.txt pins {pinned!r}; this build runs {running!r}. "
            "The bundle would install code this build did not check: "
            "pin the running ux-compose (push that commit first), or build with the pinned one"
        )
    commit = running.rpartition("@")[2].partition("#")[0]
    if checkout := _dirty_checkout():
        warnings.append(
            f"WARNING: the ux-compose checkout {checkout} has uncommitted changes. "
            f"This build ran them, but the bundle installs {commit}, so it matches no commit "
            "this build checked. Commit and push, then package again"
        )
    elif note:
        warnings.append(note)
    resolved = {name: _installed(name) for name in DISTS}
    resolved["ux-compose"]["vcs_commit"] = commit
    return resolved


def _write_archive(src: Path, tar_path: Path, name: str, mtime: int) -> None:
    """Sorted members, one ``<name>/`` root, fixed mtime, owner 0; temp file, then rename."""
    paths = sorted(src.rglob("*"), key=lambda p: p.relative_to(src).as_posix())
    fd, tmp = tempfile.mkstemp(prefix=_TMP, dir=tar_path.parent)
    try:
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, mtime=mtime
        ) as gz, tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tf:
            for p in [src, *paths]:
                info = tf.gettarinfo(str(p), arcname="/".join([name, *p.relative_to(src).parts]))
                info.mtime, info.uid, info.gid, info.uname, info.gname = mtime, 0, 0, "", ""
                info.mode = 0o755 if p.is_dir() or os.access(p, os.X_OK) else 0o644
                if info.isfile():
                    with open(p, "rb") as fh:
                        tf.addfile(info, fh)
                else:
                    tf.addfile(info)
        os.chmod(tmp, 0o644)
        os.replace(tmp, tar_path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# Boot the app as uvicorn would (ASGI lifespan startup; an app that rejects
# the lifespan scope has none), GET each (path, content-type word) from its
# own ASGI callable, then shut it down. A failure is one stderr line
# starting with _STATIC. Each phase is bounded by LIFESPAN_TIMEOUT seconds.
_STATIC = "uxcompose-static:"
LIFESPAN_TIMEOUT = 30.0
# The whole probe process: asyncio cannot time out a blocking call (at import, or in a sync startup handler).
IMPORT_TIMEOUT = 120.0
_PROBE = """
import asyncio

def fail(message):
    sys.exit(STATIC + " " + " ".join(str(message).split()))

def why(exc):
    return f"{type(exc).__name__}: {exc}"

async def within(awaitable, what):
    try:
        return await asyncio.wait_for(awaitable, TIMEOUT)
    except TimeoutError:
        fail(f"{what} did not finish within {TIMEOUT:g}s")

class Lifespan:
    def __init__(self, app, state):
        self.to_app, self.from_app, self.received = asyncio.Queue(), asyncio.Queue(), False
        scope = {"type": "lifespan", "asgi": {"version": "3.0", "spec_version": "2.0"}, "state": state}
        self.task = asyncio.create_task(self.run(app, scope))

    async def receive(self):
        self.received = True
        return await self.to_app.get()

    async def run(self, app, scope):
        try:
            await app(scope, self.receive, self.from_app.put)
        except Exception as exc:
            await self.from_app.put({"type": "raised", "message": why(exc)})
        else:
            await self.from_app.put({"type": "returned", "message": "the app returned"})

    async def step(self, phase):
        await self.to_app.put({"type": f"lifespan.{phase}"})
        msg = await within(self.from_app.get(), f"ASGI {phase}")
        if msg["type"] == f"lifespan.{phase}.complete":
            return True
        if not self.received:
            return False  # rejected the lifespan scope: no lifespan, as uvicorn --lifespan auto
        fail(f"ASGI {phase} failed: {msg.get('message') or msg['type']}")

async def get(app, path, state):
    sent, done, requested = [], asyncio.Event(), []
    async def receive():
        if not requested:
            requested.append(True)
            return {"type": "http.request", "body": b"", "more_body": False}
        await done.wait()
        return {"type": "http.disconnect"}
    async def send(message):
        sent.append(message)
        if message["type"] == "http.response.body" and not message.get("more_body"):
            done.set()
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
             "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
             "root_path": "", "headers": [(b"host", b"localhost")], "client": ("127.0.0.1", 0),
             "server": ("localhost", 80), "state": dict(state)}
    try:
        await within(app(scope, receive, send), f"GET {path}")
    except Exception as exc:
        fail(f"GET {path} from the bundle alone raised {why(exc)}")
    start = next((m for m in sent if m["type"] == "http.response.start"), None)
    if start is None:
        fail(f"GET {path} from the bundle alone sent no response")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    kind = dict(start.get("headers", [])).get(b"content-type", b"").decode()
    return start["status"], kind, len(body)

async def main():
    state = {}
    lifespan = Lifespan(APP, state)
    booted = await lifespan.step("startup")
    for path, want in PATHS:
        status, kind, size = await get(APP, path, state)
        if status != 200 or want not in kind or not size:
            fail(f"GET {path} from the bundle alone returned {status} {kind or 'no content-type'} "
                 f"({size} bytes); the app must serve it with 200 {want}")
    if booted:
        await lifespan.step("shutdown")

asyncio.run(main())
"""


def _served(bundle: Path) -> list[tuple[str, str]]:
    """Library JS always (the package URL is the SSoT); the app's CSS when the bundle ships it."""
    from ux_compose.assets import WebAssets

    paths = [("/ux-dom/static/x_element.js", "javascript")]
    css = WebAssets.from_app_root(bundle, dry_run=True).output_css
    if css.is_file():
        paths.append((f"/css/{css.name}", "text/css"))
    return paths


def _smoke_import(bundle: Path, entry: str) -> None:
    """Import ``entry`` from a copy of the bundle alone (``python -I -B``, cwd = bundle), then GET its static.

    ``-I`` keeps the source root, ``PYTHONPATH`` and the user site off
    ``sys.path``; only the bundle dir is added. The copy keeps the app's
    import-time writes (``WebAssets`` folders) out of the bundle. In the same
    process the app's ASGI lifespan starts, the GETs (``_served``) run, and
    it shuts down (``_PROBE``).
    """
    import subprocess
    import sys

    mod, _, attr = entry.partition(":")
    code = (
        "import importlib, sys\n"
        "sys.path.insert(0, '.')\n"
        f"m = importlib.import_module({mod!r})\n"
        f"APP = getattr(m, {attr!r}, None)\n"
        f"assert APP is not None, 'no attribute {attr}'\n"
        f"PATHS = {_served(bundle)!r}\n"
        f"STATIC, TIMEOUT = {_STATIC!r}, {LIFESPAN_TIMEOUT!r}\n"
        + _PROBE
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    probe = Path(tempfile.mkdtemp(prefix="uxcompose-probe-"))
    try:
        shutil.copytree(bundle, probe / "bundle")
        proc = subprocess.run(
            [sys.executable, "-I", "-B", "-c", code],
            check=False,
            cwd=probe / "bundle",
            env=env,
            capture_output=True,
            text=True,
            timeout=IMPORT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise PackageError(
            f"import {entry} and its ASGI startup from the bundle alone did not finish within "
            f"{IMPORT_TIMEOUT:g}s; a blocking call at import time or in a sync startup handler?"
        ) from None
    finally:
        shutil.rmtree(probe, ignore_errors=True)
    if proc.returncode != 0:
        lines = [ln for ln in (proc.stderr or proc.stdout or "").splitlines() if ln.strip()]
        reason = lines[-1].replace(str(probe / "bundle") + "/", "") if lines else f"exit {proc.returncode}"
        if reason.startswith(_STATIC):
            raise PackageError(reason.removeprefix(_STATIC).strip())
        raise PackageError(f"import {entry} from the bundle alone failed: {reason}")


def _source_date_epoch() -> int:
    raw = os.environ.get("SOURCE_DATE_EPOCH") or "0"
    if not raw.isdigit():
        raise PackageError(f"SOURCE_DATE_EPOCH must be a non-negative integer, got {raw!r}")
    return int(raw)


def _collect_checked(root: Path, *, skip: Path | None = None) -> Collected:
    _requirement_lines(root)
    found = collect(root, skip=skip)
    if found.refused:
        raise PackageError("refusing to bundle: " + ", ".join(found.refused))
    return found


def _stage(root: Path, found: Collected, dest: Path) -> list[dict]:
    """Copy the collected files into ``dest``; return their MANIFEST entries."""
    manifest_files = []
    for rel in found.files:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        data = (root / rel).read_bytes()
        (dest / rel).write_bytes(data)
        shutil.copymode(root / rel, dest / rel)
        manifest_files.append(
            {"path": rel.as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        )
    return manifest_files


def _check_staged(staged: Path, entry: str, warnings: list[str]) -> dict:
    """``doctor --prod``, the import from the bundle alone, the ux-compose pin; returns ``resolved``."""
    from ux_compose.doctor import scan_product_readiness

    fails = [row for row in scan_product_readiness(staged) if row.startswith("[FAIL]")]
    if fails:
        raise PackageError("doctor --prod: " + "; ".join(fails))
    _smoke_import(staged, entry)
    return _resolved(staged, warnings)


def check_bundle(root: Path, *, entry: str = "app:asgi") -> tuple[list[str], list[str]]:
    """Every ``write_bundle`` check on a throwaway copy in the system temp dir.

    Returns the URLs the smoke import GOT and the warnings.

    Raises the ``PackageError`` ``write_bundle`` would raise. Writes nothing under ``root``.
    """
    root = Path(root).resolve()
    found = _collect_checked(root)
    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="uxcompose-check-") as tmp:
        _stage(root, found, Path(tmp))
        _check_staged(Path(tmp), entry, warnings)
        served = [path for path, _ in _served(Path(tmp))]
    return served, warnings


def write_bundle(
    root: Path,
    *,
    out_dir: Path,
    name: str,
    entry: str = "app:asgi",
    archive: bool = False,
) -> Bundle:
    """Write ``OUT/name/`` (and ``OUT/name.tar.gz``), or raise ``PackageError`` having written nothing.

    Checked before any write: ``--out`` (``check_out``), the file set
    (``collect``) and ``SOURCE_DATE_EPOCH``. The assembled bundle must pass
    ``doctor --prod`` and the ux-compose pin check before it replaces the
    previous bundle.
    """
    root = Path(root).resolve()
    out = check_out(root, Path(out_dir), name)
    mtime = _source_date_epoch()
    found = _collect_checked(root, skip=out)

    created = not out.exists()
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=_TMP, dir=out))
    warnings: list[str] = []
    try:
        manifest_files = _stage(root, found, tmp)
        manifest = {
            "generator": BUNDLE_GENERATOR,
            "name": name,
            "entrypoint": entry,
            "static_model": "single_copy_from_site_packages",
            "files": manifest_files,
            "resolved": _check_staged(tmp, entry, warnings),
        }
        (tmp / "README.RUN.txt").write_text(README_RUN.format(name=name), encoding="utf-8")
        (tmp / "run.sh").write_text(RUN_SH.format(entry=entry), encoding="utf-8")
        (tmp / "run.sh").chmod(0o755)
        (tmp / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        tmp.chmod(0o755)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        if created:
            try:
                out.rmdir()  # only if still empty: never another writer's files
            except OSError:
                pass
        raise

    dest = out / name
    tar_path = out / f"{name}.tar.gz"
    if dest.exists():
        if dest.is_symlink() or not is_bundle(dest, allow_venv=False):  # changed since check_out
            shutil.rmtree(tmp, ignore_errors=True)
            raise PackageError(f"{dest} changed during the build and is no longer a bundle this tool wrote")
        trash = Path(tempfile.mkdtemp(prefix=_TMP, dir=out))
        os.rename(dest, trash / name)
        os.rename(tmp, dest)
        shutil.rmtree(trash)
    else:
        os.rename(tmp, dest)
    bundle = Bundle(path=dest, excluded=found.excluded, warnings=warnings)
    if archive:
        _write_archive(dest, tar_path, name, mtime)
        bundle.archive = tar_path
    else:
        tar_path.unlink(missing_ok=True)  # an older bundle's archive (check_out proved it ours)
    return bundle


__all__ = ["Bundle", "Collected", "PackageError", "check_bundle", "check_out", "collect", "write_bundle"]
