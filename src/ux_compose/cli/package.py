"""``uxcompose build --package`` / ``--archive`` — the runnable bundle.

``OUT/<name>/`` holds an allowlist of the app: root ``*.py``, the
requirements file and deploy configs, and the source/asset file types under
``routes/``, ``components/``, ``assets/`` and ``deploy/``. Three files are
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

from ux_compose.doctor import BUNDLE_GENERATOR, is_bundle, is_skipped_dir

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

run.sh activates ./.venv when it exists, then uses the python3 and uvicorn
on PATH: install requirements.txt into that environment.

Library JavaScript (x_element.js, the Channel client) is NOT vendored into
this bundle. The installed packages serve it from site-packages.
MANIFEST.json lists every copied file with its sha256 and the commits of
ux-compose and its specialists this bundle was built and checked with.
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


def collect(root: Path) -> Collected:
    """Allowlisted files to copy; everything else excluded (listed) or refused.

    Refused: a symlink out of the app tree that the allowlist would copy, a
    key-shaped file (by name or content) inside an allowed directory, and a
    private key in a root file the allowlist would copy. A symlinked
    directory is left out and listed. Nothing outside the tree is read.
    """
    root = root.resolve()
    out = Collected()

    def visit(path: Path, allowed: set[str] | None) -> None:
        rel = path.relative_to(root).as_posix()
        if allowed is None and not (
            (path.name in ALLOWED and path.is_dir()) or path.suffix == ".py" or path.name in ROOT_FILES
        ):
            out.excluded.append(f"{rel}/" if path.is_dir() and not path.is_symlink() else rel)
            return
        if path.is_symlink():
            target = path.resolve()
            if not target.is_relative_to(root):
                out.refused.append(f"{rel} (symlink out of the app tree)")
                return
            if target.is_dir():
                out.excluded.append(f"{rel}/ (symlinked dir)")
                return
        if path.is_dir():
            sub = ALLOWED[path.name] if allowed is None else allowed
            if is_skipped_dir(path):
                out.excluded.append(f"{rel}/")
                return
            for child in sorted(path.iterdir()):
                visit(child, sub)
            return
        if allowed is None:
            if _key_content(path):
                out.refused.append(f"{rel} (holds a private key)")
            else:
                out.files.append(Path(rel))
        elif _key_name(path.name) or _key_content(path):
            out.refused.append(f"{rel} (key-shaped)")
        elif path.suffix.lower() in allowed:
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
        foreign = [
            p.name
            for p in sorted(out.iterdir())
            if not (
                (p.is_dir() and not p.is_symlink() and is_bundle(p))
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


def _source_date_epoch() -> int:
    raw = os.environ.get("SOURCE_DATE_EPOCH") or "0"
    if not raw.isdigit():
        raise PackageError(f"SOURCE_DATE_EPOCH must be a non-negative integer, got {raw!r}")
    return int(raw)


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
    from ux_compose.doctor import scan_product_readiness

    root = Path(root).resolve()
    out = check_out(root, Path(out_dir), name)
    mtime = _source_date_epoch()
    _requirement_lines(root)
    found = collect(root)
    if found.refused:
        raise PackageError("refusing to bundle: " + ", ".join(found.refused))

    created = not out.exists()
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=_TMP, dir=out))
    warnings: list[str] = []
    try:
        manifest_files = []
        for rel in found.files:
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            data = (root / rel).read_bytes()
            (tmp / rel).write_bytes(data)
            shutil.copymode(root / rel, tmp / rel)
            manifest_files.append(
                {"path": rel.as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            )
        fails = [row for row in scan_product_readiness(tmp) if row.startswith("[FAIL]")]
        if fails:
            raise PackageError("doctor --prod: " + "; ".join(fails))
        manifest = {
            "generator": BUNDLE_GENERATOR,
            "name": name,
            "entrypoint": entry,
            "static_model": "single_copy_from_site_packages",
            "files": manifest_files,
            "resolved": _resolved(tmp, warnings),
        }
        (tmp / "README.RUN.txt").write_text(README_RUN.format(name=name), encoding="utf-8")
        (tmp / "run.sh").write_text(RUN_SH.format(entry=entry), encoding="utf-8")
        (tmp / "run.sh").chmod(0o755)
        (tmp / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        tmp.chmod(0o755)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        if created:
            shutil.rmtree(out, ignore_errors=True)
        raise

    dest = out / name
    tar_path = out / f"{name}.tar.gz"
    if dest.exists():  # check_out proved it is a bundle this tool wrote
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


__all__ = ["Bundle", "Collected", "PackageError", "check_out", "collect", "write_bundle"]
