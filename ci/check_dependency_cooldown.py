"""Fail the CI job when a PyPI distribution is younger than 14 days.

Local, editable, and git-SHA installs are not registry releases and are
skipped. Their PyPI dependencies are ordinary distributions and are checked.
The version's upload time is the earliest ``upload_time_iso_8601`` among its
files on https://pypi.org/pypi/<name>/<version>/json. A network, HTTP, or
payload failure fails closed.
"""
from __future__ import annotations

import importlib.metadata
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

COOLDOWN = timedelta(days=14)
PYPI_JSON = "https://pypi.org/pypi/{name}/{version}/json"


class CooldownCheckError(Exception):
    """The cooldown check cannot prove every PyPI distribution is old enough."""


class Installed:
    __slots__ = ("name", "version", "direct_url")

    def __init__(self, name: str, version: str, direct_url: dict | None = None) -> None:
        self.name = name
        self.version = version
        self.direct_url = direct_url


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_pypi_distribution(installed: Installed) -> bool:
    info = installed.direct_url
    if not info:
        return True
    url = str(info.get("url") or "")
    dir_info = info.get("dir_info") or {}
    if dir_info.get("editable"):
        return False
    if url.startswith("file:"):
        return False
    vcs = info.get("vcs_info") or {}
    if vcs.get("vcs") == "git" or vcs.get("commit_id"):
        return False
    lowered = url.lower()
    if lowered.startswith("git+") or lowered.startswith("git:"):
        return False
    return True


def from_distribution(dist) -> Installed:
    raw = dist.read_text("direct_url.json")
    if not raw:
        return Installed(name=dist.name, version=dist.version)
    try:
        direct = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"invalid direct_url.json for {dist.name} {dist.version}: {exc}"
        ) from exc
    if not isinstance(direct, dict):
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"direct_url.json for {dist.name} {dist.version} is not an object"
        )
    return Installed(name=dist.name, version=dist.version, direct_url=direct)


def iter_installed() -> list[Installed]:
    return [from_distribution(dist) for dist in importlib.metadata.distributions()]


def fetch_pypi_json(name: str, version: str) -> dict:
    url = PYPI_JSON.format(name=name, version=version)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ux-compose-ci-dependency-cooldown",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except Exception as exc:
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"network error fetching {url}: {exc}"
        ) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"invalid JSON from {url}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"unexpected payload from {url}"
        )
    return payload


def _parse_upload_time(raw: object, *, name: str, version: str) -> datetime:
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"{name} {version} has an unreadable upload_time_iso_8601 {raw!r}: {exc}"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _earliest_upload(payload: dict, *, name: str, version: str) -> datetime:
    urls = payload.get("urls") if isinstance(payload, dict) else None
    if not isinstance(urls, list) or not urls:
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"{name} {version} has no files on PyPI"
        )
    times = [
        _parse_upload_time(item["upload_time_iso_8601"], name=name, version=version)
        for item in urls
        if isinstance(item, dict) and item.get("upload_time_iso_8601")
    ]
    if not times:
        raise CooldownCheckError(
            "dependency cooldown check failed closed: "
            f"{name} {version} has no upload_time_iso_8601"
        )
    return min(times)


def check_installed(installed, *, now: datetime, fetch, cooldown: timedelta = COOLDOWN) -> int:
    violations: list[str] = []
    checked = 0
    for dist in installed:
        if not is_pypi_distribution(dist):
            continue
        checked += 1
        url = PYPI_JSON.format(name=dist.name, version=dist.version)
        try:
            payload = fetch(dist.name, dist.version)
        except CooldownCheckError:
            raise
        except Exception as exc:
            raise CooldownCheckError(
                "dependency cooldown check failed closed: "
                f"network error fetching {url}: {exc}"
            ) from exc
        uploaded = _earliest_upload(payload, name=dist.name, version=dist.version)
        if now - uploaded < cooldown:
            violations.append(
                f"{dist.name} {dist.version} was uploaded {uploaded.isoformat()} "
                f"(less than {cooldown.days} days before this run)"
            )
    if violations:
        raise CooldownCheckError("\n".join(violations))
    return checked


def main(argv: list[str] | None = None) -> int:
    del argv
    try:
        checked = check_installed(iter_installed(), now=utc_now(), fetch=fetch_pypi_json)
    except CooldownCheckError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if checked == 0:
        print(
            "dependency cooldown check failed closed: no PyPI distributions were checked",
            file=sys.stderr,
        )
        return 1
    print(
        "dependency cooldown ok: "
        f"all {checked} checked PyPI distributions are at least 14 days old"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
