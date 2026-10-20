"""A ``*.py`` save reaches the open page through origin, by morph.

Real ``uxcompose serve dev`` in a fresh scaffold, real Chrome (major 155
or newer, same check as the Login test) on the origin URL. Rewriting
``routes/hello.py`` restarts the ui worker. Its HMR socket closes with
1012, origin must pass that close to the browser, and the client then
morphs the new HTML in. No navigation: ``Page.frameNavigated`` stays at
0 and a window marker survives, so this is not ``location.reload()``.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

from tests.security.test_login_typed_password import _Chrome, _free_port
from ux_compose.scaffold import create_app


class _Browser(_Chrome):
    """``_Chrome`` that counts main-frame navigations while it waits."""

    navigations = 0

    def _note(self, raw: dict) -> None:
        if raw.get("method") == "Page.frameNavigated":
            frame = raw.get("params", {}).get("frame", {})
            if not frame.get("parentId"):
                self.navigations += 1

    def call(self, method: str, params: dict | None = None, session: str | None = None):
        self._n += 1
        message = {"id": self._n, "method": method, "params": params or {}}
        if session:
            message["sessionId"] = session
        self.ws.send(json.dumps(message))
        while True:
            raw = json.loads(self.ws.recv())
            if raw.get("id") == self._n:
                if "error" in raw:
                    raise RuntimeError(raw["error"])
                return raw
            self._note(raw)


def _app_processes(root: Path) -> list[int]:
    out = []
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            try:
                if Path(os.readlink(f"/proc/{entry}/cwd")) == root:
                    out.append(int(entry))
            except OSError:
                pass
    return out


@pytest.fixture
def serve_dev(tmp_path):
    root = create_app(tmp_path / "demo", name="demo", level="auto", host="auto").resolve()
    port = _free_port()
    log = tmp_path / "serve.log"
    env = {**os.environ, "UX_CHANNEL_SECRET": "s" * 32}
    env.pop("DEBUG", None)
    with log.open("wb") as out:
        proc = subprocess.Popen(
            [sys.executable, "-m", "ux_compose.cli", "serve", "dev", "--port", str(port)],
            cwd=root,
            env=env,
            stdout=out,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
    try:
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/hello", timeout=3) as r:
                    if r.status == 200:
                        break
            except OSError:
                time.sleep(0.3)
        else:
            pytest.fail("serve dev did not answer /hello:\n" + log.read_text())
        yield root, port, log
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        for pid in _app_processes(root):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.fixture
def browser():
    b = _Browser()
    try:
        yield b
    finally:
        b.close()


def test_py_save_morphs_open_page_through_origin(serve_dev, browser):
    root, port, log = serve_dev
    browser.goto(f"http://127.0.0.1:{port}/hello")
    deadline = time.time() + 10
    while not browser.evaluate("window.__UXCOMPOSE_HMR__ === true"):
        assert time.time() < deadline, "HMR client did not start"
        time.sleep(0.1)
    time.sleep(0.5)  # let the HMR socket open
    browser.evaluate("window.__hmrMark = 'kept'")
    assert "+1 HMR" not in browser.evaluate("document.body.innerText")
    browser.navigations = 0

    hello = root / "routes" / "hello.py"
    hello.write_text(
        hello.read_text(encoding="utf-8").replace('button("+1"', 'button("+1 HMR"', 1),
        encoding="utf-8",
    )

    deadline = time.time() + 15
    text = ""
    while time.time() < deadline:
        text = browser.evaluate("document.body.innerText")
        if "+1 HMR" in text:
            break
        time.sleep(0.2)
    assert "+1 HMR" in text, "page did not change within 15 s:\n" + log.read_text()
    assert browser.navigations == 0
    assert browser.evaluate("window.__hmrMark") == "kept"
