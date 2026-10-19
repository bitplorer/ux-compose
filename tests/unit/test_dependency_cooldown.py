"""CI dependency cooldown: a PyPI distribution must be at least 14 days old.

The checker is CI-only (``ci/check_dependency_cooldown.py``). These tests mock
the PyPI JSON API. Local, editable, and git-SHA installs are not registry
releases and are skipped. A network or payload failure fails closed.
"""
from __future__ import annotations

import importlib.util
import json
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ci" / "check_dependency_cooldown.py"

RUN = datetime(2026, 10, 19, 12, 41, 3, 900747, tzinfo=timezone.utc)
FASTAPI_0148_UPLOADED = "2026-10-19T12:26:03.900747Z"
FASTAPI_0142_2_UPLOADED = "2026-09-30T09:51:09.800102Z"


def _load():
    spec = importlib.util.spec_from_file_location("check_dependency_cooldown", SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"missing dependency cooldown script: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cooldown = _load()


def _payload(*upload_times: str) -> dict:
    return {
        "urls": [
            {"filename": f"file-{index}", "upload_time_iso_8601": upload_time}
            for index, upload_time in enumerate(upload_times)
        ]
    }


def _fetch_returning(payload: dict):
    def fetch(name: str, version: str) -> dict:
        return payload

    return fetch


def test_fifteen_minute_old_fastapi_0_148_0_fails():
    uploaded = datetime.fromisoformat(FASTAPI_0148_UPLOADED.replace("Z", "+00:00"))
    assert RUN - uploaded == timedelta(minutes=15)

    with pytest.raises(cooldown.CooldownCheckError) as caught:
        cooldown.check_installed(
            [cooldown.Installed("fastapi", "0.148.0")],
            now=RUN,
            fetch=_fetch_returning(_payload(FASTAPI_0148_UPLOADED)),
        )

    message = str(caught.value)
    assert message == (
        "fastapi 0.148.0 was uploaded 2026-10-19T12:26:03.900747+00:00 "
        "(less than 14 days before this run)"
    )


def test_version_older_than_14_days_passes():
    uploaded = datetime.fromisoformat(FASTAPI_0142_2_UPLOADED.replace("Z", "+00:00"))
    assert RUN - uploaded >= timedelta(days=14)

    checked = cooldown.check_installed(
        [cooldown.Installed("fastapi", "0.142.2")],
        now=RUN,
        fetch=_fetch_returning(_payload(FASTAPI_0142_2_UPLOADED)),
    )
    assert checked == 1


def test_exactly_14_days_old_passes():
    now = datetime(2026, 10, 19, 12, 26, 3, tzinfo=timezone.utc)
    checked = cooldown.check_installed(
        [cooldown.Installed("fastapi", "0.142.2")],
        now=now,
        fetch=_fetch_returning(_payload("2026-10-05T12:26:03Z")),
    )
    assert checked == 1


def test_one_second_under_14_days_fails():
    now = datetime(2026, 10, 19, 12, 26, 3, tzinfo=timezone.utc)
    with pytest.raises(cooldown.CooldownCheckError, match="fastapi 0.142.2 was uploaded"):
        cooldown.check_installed(
            [cooldown.Installed("fastapi", "0.142.2")],
            now=now,
            fetch=_fetch_returning(_payload("2026-10-05T12:26:04Z")),
        )


def test_version_age_is_the_earliest_file_upload():
    """A later wheel does not reset the clock. The version dates from its first file."""
    checked = cooldown.check_installed(
        [cooldown.Installed("fastapi", "0.142.2")],
        now=RUN,
        fetch=_fetch_returning(_payload(FASTAPI_0142_2_UPLOADED, FASTAPI_0148_UPLOADED)),
    )
    assert checked == 1


@pytest.mark.parametrize(
    "direct_url",
    [
        {"url": "file:///tmp/localpkg-1.0-py3-none-any.whl", "archive_info": {}},
        {"url": "file:///workspace/ux-compose", "dir_info": {"editable": True}},
        {
            "url": "https://github.com/bitplorer/ux-dom.git",
            "vcs_info": {
                "vcs": "git",
                "commit_id": "0440ccbf9b9a53a0ba11ae43b3d04b6079b330f4",
                "requested_revision": "0440ccbf9b9a53a0ba11ae43b3d04b6079b330f4",
            },
        },
        {
            "url": "git+https://github.com/bitplorer/cek-python.git@985e58a",
            "vcs_info": {"vcs": "git", "commit_id": "985e58a"},
        },
    ],
)
def test_local_editable_and_git_sha_installs_are_skipped(direct_url):
    seen: list[tuple[str, str]] = []

    def fetch(name: str, version: str) -> dict:
        seen.append((name, version))
        return _payload(FASTAPI_0142_2_UPLOADED)

    checked = cooldown.check_installed(
        [
            cooldown.Installed("skipped", "9.9.9", direct_url),
            cooldown.Installed("fastapi", "0.142.2"),
        ],
        now=RUN,
        fetch=fetch,
    )
    assert checked == 1
    assert seen == [("fastapi", "0.142.2")]


def test_network_error_fails_closed():
    def fetch(name: str, version: str) -> dict:
        raise urllib.error.URLError("timed out")

    with pytest.raises(cooldown.CooldownCheckError) as caught:
        cooldown.check_installed(
            [cooldown.Installed("fastapi", "0.148.0")],
            now=RUN,
            fetch=fetch,
        )

    message = str(caught.value)
    assert message.startswith("dependency cooldown check failed closed:")
    assert "https://pypi.org/pypi/fastapi/0.148.0/json" in message
    assert "timed out" in message


def test_fetch_pypi_json_reads_the_json_api(monkeypatch):
    captured: dict = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(_payload(FASTAPI_0142_2_UPLOADED)).encode()

    def urlopen(request, timeout=0):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(cooldown.urllib.request, "urlopen", urlopen)
    payload = cooldown.fetch_pypi_json("fastapi", "0.142.2")
    assert captured["url"] == "https://pypi.org/pypi/fastapi/0.142.2/json"
    assert captured["timeout"] > 0
    assert payload["urls"][0]["upload_time_iso_8601"] == FASTAPI_0142_2_UPLOADED


def test_fetch_pypi_json_network_error_fails_closed(monkeypatch):
    def urlopen(request, timeout=0):
        raise urllib.error.URLError("nodename nor servname provided")

    monkeypatch.setattr(cooldown.urllib.request, "urlopen", urlopen)
    with pytest.raises(cooldown.CooldownCheckError) as caught:
        cooldown.fetch_pypi_json("fastapi", "0.148.0")
    message = str(caught.value)
    assert message.startswith("dependency cooldown check failed closed:")
    assert "network error" in message
    assert "https://pypi.org/pypi/fastapi/0.148.0/json" in message
    assert "nodename nor servname provided" in message


def test_missing_upload_time_fails_closed():
    with pytest.raises(cooldown.CooldownCheckError, match="failed closed"):
        cooldown.check_installed(
            [cooldown.Installed("fastapi", "0.142.2")],
            now=RUN,
            fetch=_fetch_returning({"urls": [{"filename": "x"}]}),
        )


def test_from_distribution_skips_editable_and_keeps_registry_names():
    class Editable:
        name = "ux-compose"
        version = "0.2.0"

        def read_text(self, filename):
            assert filename == "direct_url.json"
            return json.dumps(
                {"url": "file:///workspace", "dir_info": {"editable": True}}
            )

    class Registry:
        name = "fastapi"
        version = "0.142.2"

        def read_text(self, filename):
            return None

    editable = cooldown.from_distribution(Editable())
    registry = cooldown.from_distribution(Registry())
    assert cooldown.is_pypi_distribution(editable) is False
    assert cooldown.is_pypi_distribution(registry) is True
    assert (registry.name, registry.version) == ("fastapi", "0.142.2")


def test_main_pass_line(monkeypatch, capsys):
    monkeypatch.setattr(cooldown, "utc_now", lambda: RUN)
    monkeypatch.setattr(
        cooldown,
        "iter_installed",
        lambda: [cooldown.Installed("fastapi", "0.142.2")],
    )
    monkeypatch.setattr(
        cooldown,
        "fetch_pypi_json",
        lambda name, version: _payload(FASTAPI_0142_2_UPLOADED),
    )

    assert cooldown.main([]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.strip() == (
        "dependency cooldown ok: all 1 checked PyPI distributions are at least 14 days old"
    )


def test_main_names_young_fastapi_on_stderr(monkeypatch, capsys):
    monkeypatch.setattr(cooldown, "utc_now", lambda: RUN)
    monkeypatch.setattr(
        cooldown,
        "iter_installed",
        lambda: [cooldown.Installed("fastapi", "0.148.0")],
    )
    monkeypatch.setattr(
        cooldown,
        "fetch_pypi_json",
        lambda name, version: _payload(FASTAPI_0148_UPLOADED),
    )

    assert cooldown.main([]) == 1
    captured = capsys.readouterr()
    assert "fastapi 0.148.0 was uploaded 2026-10-19T12:26:03.900747+00:00" in captured.err
    assert captured.out == ""


def test_main_fails_closed_when_no_pypi_distribution_was_checked(monkeypatch, capsys):
    monkeypatch.setattr(cooldown, "utc_now", lambda: RUN)
    monkeypatch.setattr(
        cooldown,
        "iter_installed",
        lambda: [
            cooldown.Installed(
                "ux-compose",
                "0.2.0",
                {"url": "file:///workspace", "dir_info": {"editable": True}},
            )
        ],
    )

    assert cooldown.main([]) == 1
    captured = capsys.readouterr()
    assert (
        captured.err.strip()
        == "dependency cooldown check failed closed: no PyPI distributions were checked"
    )
