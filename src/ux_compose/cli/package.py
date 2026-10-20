"""``uxcompose build --package`` / ``--archive`` — the runnable bundle.

``dist/<name>/`` holds the app source (root ``*.py``, ``routes/``,
``components/``, ``assets/``), the app's own ``requirements.txt``, the deploy
files that already exist, and three generated files: ``run.sh``,
``README.RUN.txt``, ``MANIFEST.json``. Library JS is not vendored; the
installed packages serve it. Nothing in the bundle names the build machine,
and the archive is byte-identical for the same inputs.
"""
from __future__ import annotations

import fnmatch
import gzip
import hashlib
import json
import os
import shutil
import tarfile
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path

from ux_compose.doctor import SKIP_DIRS

SOURCE_DIRS = ("routes", "components", "assets")
COPIED_FILES = (
    "requirements.txt",
    "README.md",
    "Dockerfile",
    ".dockerignore",
    "fly.toml",
    "render.yaml",
    "railway.json",
)
COPIED_DIRS = ("deploy",)
SECRETS = (".env", ".env.*", "*.pem", "*.key")
DISTS = ("ux-compose", "ux-dom", "ux-channel", "ux-behavior", "ux-motion")

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
python -c 'import sys; from ux_compose.doctor import secret_readiness; sys.exit(secret_readiness())'
exec uvicorn {entry} --app-dir . --host "$HOST" --port "$PORT"
"""

README_RUN = """\
ux-compose runnable bundle: {name}

  pip install -r requirements.txt
  export UX_CHANNEL_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
  ./run.sh                      # PORT (default 8080), HOST (default 0.0.0.0)

Library JavaScript (x_element.js, the Channel client) is NOT vendored into
this bundle. The installed packages serve it from site-packages.
MANIFEST.json lists every copied file with its sha256 and the commits of
ux-compose and its specialists this bundle was built and checked with.
"""


class PackageError(RuntimeError):
    """The bundle would not run, or would not be what this build checked."""


@dataclass
class Bundle:
    path: Path
    archive: Path | None = None
    excluded: list[str] = field(default_factory=list)


def _secret(name: str) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in SECRETS)


def collect(root: Path) -> tuple[list[Path], list[str]]:
    """(files to copy, secret files left out), both relative to ``root`` and sorted."""
    files: list[Path] = []
    excluded: list[str] = []

    def take(rel: Path) -> None:
        if _secret(rel.name):
            excluded.append(rel.as_posix())
        elif not rel.name.endswith(".pyc"):
            files.append(rel)

    for p in root.iterdir():
        if p.is_file() and (p.suffix == ".py" or p.name in COPIED_FILES or _secret(p.name)):
            take(p.relative_to(root))
    for base in (*SOURCE_DIRS, *COPIED_DIRS):
        for dirpath, dirnames, filenames in os.walk(root / base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                take((Path(dirpath) / name).relative_to(root))
    return sorted(files), sorted(excluded)


def _installed(name: str) -> dict[str, str | None]:
    dist = metadata.distribution(name)
    info = json.loads(dist.read_text("direct_url.json") or "{}")
    return {"version": dist.version, "vcs_commit": (info.get("vcs_info") or {}).get("commit_id")}


def _resolved(root: Path) -> dict[str, dict[str, str | None]]:
    """The ux-compose line in requirements.txt must be the ux-compose this build runs.

    Specialists come with that line, so their commits are the ones this
    interpreter checked the app with.
    """
    from ux_compose.scaffold import (
        _COMMENT,
        ComposeRefError,
        _logical_lines,
        compose_requirement,
        scan_requirements,
    )

    names = scan_requirements(root / "requirements.txt").names
    file, _, number = names["ux-compose"].rpartition(":")
    lines = dict(_logical_lines((root / file).read_text(encoding="utf-8")))
    pinned = _COMMENT.sub("", lines[int(number)]).strip()
    try:
        running, _note = compose_requirement()
    except ComposeRefError as exc:
        raise PackageError(str(exc)) from None
    if pinned != running:
        raise PackageError(
            f"requirements.txt pins {pinned!r}; this build runs {running!r}. "
            "The bundle would install code this build did not check: "
            "pin the running ux-compose, or build with the pinned one"
        )
    resolved = {name: _installed(name) for name in DISTS}
    resolved["ux-compose"]["vcs_commit"] = running.rpartition("@")[2].partition("#")[0]
    return resolved


def _write_archive(src: Path, tar_path: Path, name: str) -> None:
    """Sorted members, one ``<name>/`` root, mtime ``SOURCE_DATE_EPOCH`` or 0, owner 0."""
    mtime = int(os.environ.get("SOURCE_DATE_EPOCH") or 0)
    paths = sorted(src.rglob("*"), key=lambda p: p.relative_to(src).as_posix())
    with open(tar_path, "wb") as raw, gzip.GzipFile(
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


def write_bundle(
    root: Path,
    *,
    out_dir: Path,
    name: str,
    entry: str = "app:asgi",
    archive: bool = False,
) -> Bundle:
    """Write ``out_dir/name/`` (and ``out_dir/name.tar.gz``), or raise ``PackageError``.

    The bundle is assembled beside its final path, checked with
    ``doctor --prod`` rows, and only then moved into place: a refused
    bundle leaves nothing behind.
    """
    from ux_compose.doctor import scan_product_readiness

    root = Path(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / name
    tmp = out_dir / f".{name}.partial"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    try:
        files, excluded = collect(root)
        manifest_files = []
        for rel in files:
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / rel, tmp / rel)
            data = (root / rel).read_bytes()
            manifest_files.append(
                {"path": rel.as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            )
        fails = [row for row in scan_product_readiness(tmp) if row.startswith("[FAIL]")]
        if fails:
            raise PackageError("doctor --prod: " + "; ".join(fails))
        manifest = {
            "name": name,
            "entrypoint": entry,
            "static_model": "single_copy_from_site_packages",
            "files": manifest_files,
            "resolved": _resolved(tmp),
        }
        (tmp / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (tmp / "README.RUN.txt").write_text(README_RUN.format(name=name), encoding="utf-8")
        (tmp / "run.sh").write_text(RUN_SH.format(entry=entry), encoding="utf-8")
        (tmp / "run.sh").chmod(0o755)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    shutil.rmtree(dest, ignore_errors=True)
    tmp.rename(dest)
    bundle = Bundle(path=dest, excluded=excluded)
    if archive:
        bundle.archive = out_dir / f"{name}.tar.gz"
        _write_archive(dest, bundle.archive, name)
    return bundle


__all__ = ["Bundle", "PackageError", "collect", "write_bundle"]
