"""One timeout meaning for build(), App.mount, and DirectoryRoutes.discover.

UX_COMPOSE_BUILD_LOCK_TIMEOUT, and build(lock_timeout=...) where that
argument applies:

- unset or blank: 60 seconds
- 0: one try, then BuildLockTimeout, with no wait
- inf and none, any case: no limit
- abc, -1, nan: ValueError naming UX_COMPOSE_BUILD_LOCK_TIMEOUT
"""
from __future__ import annotations

import importlib
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

from tests.asgi_http import asgi_get

pytestmark = pytest.mark.import_isolation

_ENV = "UX_COMPOSE_BUILD_LOCK_TIMEOUT"


def _cases() -> list[tuple[str, str, str]]:
    values = [
        "unset",
        "",
        "0",
        "inf",
        "INF",
        " none",
        " INF",
        "none",
        "None",
        "NONE",
        "infinite",
        "Infinity",
        "abc",
        "-1",
        "nan",
    ]
    cases = [("env", entry, value) for entry in ("build", "mount", "discover") for value in values]
    cases.extend(("argument", "build", value) for value in values if value != "unset")
    return cases


def _kind(value: str) -> str:
    if value == "unset":
        return "default"
    token = value.strip().lower()
    if token == "":
        return "default"
    if token == "0":
        return "zero"
    if token in {"inf", "none", "infinite", "infinity"}:
        return "open"
    return "bad"


def _label(value: str) -> str:
    parts: list[str] = []
    for char in value:
        if char == " ":
            parts.append("sp")
        elif char.isalnum():
            parts.append(char)
        else:
            parts.append("x")
    return "".join(parts) or "blank"


def _purge(name: str) -> None:
    for key in list(sys.modules):
        if key == name or key.startswith(name + "."):
            sys.modules.pop(key, None)


def _folder(root: Path, name: str) -> Path:
    pkg = root / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "home.py").write_text(
        textwrap.dedent(
            """\
            class Home:
                id = 'home'
                routes = ('get',)
                def render(self):
                    return 'OURS'
            """
        ),
        encoding="utf-8",
    )
    return pkg


def _call(entry: str, folder: Path, argument: object):
    if entry == "build":
        from ux_compose.build import build

        kwargs: dict[str, object] = dict(name="X", host="asgi", live="null", level=1)
        if argument is not _OMIT:
            kwargs["lock_timeout"] = argument
        built = build(folder, **kwargs)
        return asgi_get(built[1], "/home").text
    if entry == "mount":
        from ux_compose.app import App

        bundle = App().mount(folder)
        return bundle.unit_registry["home"].render()
    from ux_compose.routing.core import DirectoryRoutes

    records = DirectoryRoutes(folder).discover()
    return records[0].page_cls().render()


_OMIT = object()


@pytest.mark.parametrize(("source", "entry", "value"), _cases())
def test_lock_timeout_value_on_every_entry(tmp_path, monkeypatch, source: str, entry: str, value: str):
    kind = _kind(value)
    name = f"tv{source[:1]}{entry[:1]}{_label(value)}"
    if source == "env":
        if value == "unset":
            monkeypatch.delenv(_ENV, raising=False)
        else:
            monkeypatch.setenv(_ENV, value)
        argument: object = _OMIT
    else:
        monkeypatch.delenv(_ENV, raising=False)
        argument = value

    if kind == "bad":
        folder = _folder(tmp_path, name)
        out: dict[str, object] = {}

        def run_bad() -> None:
            started = time.perf_counter()
            try:
                _call(entry, folder, argument)
                out["text"] = "served"
            except BaseException as exc:
                out["err"] = exc
            out["elapsed"] = time.perf_counter() - started

        worker = threading.Thread(target=run_bad, daemon=True)
        try:
            worker.start()
            worker.join(1)
            assert not worker.is_alive()
            err = out.get("err")
            assert isinstance(err, ValueError), out.get("text")
            assert _ENV in str(err)
            assert float(out["elapsed"]) < 1
        finally:
            _purge(name)
        return

    gate_name = f"g{name}"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nRELEASE = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    other = tmp_path / "b" / name
    other.mkdir(parents=True)
    (other / "__init__.py").write_text("", encoding="utf-8")
    (other / "main.py").write_text(
        textwrap.dedent(
            f"""\
            import {gate_name}
            {gate_name}.IN.set()
            {gate_name}.RELEASE.wait(5)
            VALUE = 'OTHER'
            """
        ),
        encoding="utf-8",
    )
    folder = _folder(tmp_path / "a", name)
    monkeypatch.syspath_prepend(str(other.parent))
    importlib.invalidate_caches()
    gate = importlib.import_module(gate_name)
    out = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    def caller() -> None:
        started = time.perf_counter()
        try:
            out["text"] = _call(entry, folder, argument)
        except BaseException as exc:
            out["err"] = exc
        out["elapsed"] = time.perf_counter() - started

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=caller, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        right.start()
        if kind == "zero":
            right.join(0.9)
            assert not right.is_alive()
            from ux_compose.build import BuildLockTimeout

            err = out.get("err")
            assert isinstance(err, BuildLockTimeout), out.get("text")
            assert err.timeout == 0
            assert "after 0s" in str(err)
            assert float(out["elapsed"]) < 1
            assert "text" not in out
            gate.RELEASE.set()
        elif kind == "default":
            time.sleep(1.15)
            assert right.is_alive(), out.get("err")
            gate.RELEASE.set()
            right.join(3)
            assert not right.is_alive()
            assert out.get("err") is None, out.get("err")
            assert out.get("text") == "OURS"
            assert float(out["elapsed"]) >= 1
        else:
            time.sleep(0.3)
            assert right.is_alive(), out.get("err")
            gate.RELEASE.set()
            right.join(2)
            assert not right.is_alive()
            assert out.get("err") is None, out.get("err")
            assert out.get("text") == "OURS"
        left.join(2)
        assert not left.is_alive()
        assert out.get("loader") is None, out.get("loader")
    finally:
        gate.RELEASE.set()
        left.join(1)
        right.join(1)
        _purge(name)
        sys.modules.pop(gate_name, None)
