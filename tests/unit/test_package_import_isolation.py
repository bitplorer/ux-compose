"""Package import identity across build().

Deterministic: marked ``import_isolation`` so pytest-randomly does not
reorder these cases. The seeded host step does not collect this module.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import textwrap
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tests.asgi_http import asgi_get

pytestmark = pytest.mark.import_isolation

ROOT = Path(__file__).resolve().parents[2]


def _write(pkg: Path, files: dict[str, str]) -> Path:
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "__init__.py").write_text("", encoding="utf-8")
    for rel, src in files.items():
        dest = pkg / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(textwrap.dedent(src), encoding="utf-8")
    return pkg


def _drop_tree(root: Path) -> None:
    root = root.resolve()
    for key in list(sys.modules):
        mod = sys.modules.get(key)
        origin = getattr(mod, "__file__", None)
        if not isinstance(origin, str) or not origin:
            continue
        try:
            if Path(origin).resolve().is_relative_to(root):
                sys.modules.pop(key, None)
        except OSError:
            continue


def _serve(pkg: Path) -> str:
    from ux_compose.build import build

    _app, asgi, _bundle = build(pkg, name="Demo", host="asgi", live="null", level=1)
    response = asgi_get(asgi, "/hello")
    assert response.status_code == 200, response.text
    return response.text


def _marked_hello(label: str) -> str:
    return (
        "from demo.models import MARKER\n"
        "class Hello:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        f"        return 'ROUTE-{label}:' + MARKER\n"
    )


def _same_name_trees(tmp_path: Path) -> tuple[Path, Path]:
    left = _write(
        tmp_path / "left" / "demo",
        {
            "models.py": 'MARKER = "ALPHA"\n',
            "routes/hello.py": _marked_hello("ALPHA"),
        },
    )
    right = _write(
        tmp_path / "right" / "demo",
        {
            "models.py": 'MARKER = "BETA"\n',
            "routes/hello.py": _marked_hello("BETA"),
        },
    )
    return left, right


def _use_tree(monkeypatch: pytest.MonkeyPatch, pkg: Path) -> None:
    parent = str(pkg.parent)
    monkeypatch.syspath_prepend(parent)
    importlib.invalidate_caches()


def test_same_folder_name_serves_its_own_routes_in_both_orders(tmp_path, monkeypatch):
    left, right = _same_name_trees(tmp_path)
    try:
        _use_tree(monkeypatch, left)
        assert _serve(left) == "ROUTE-ALPHA:ALPHA"
        _use_tree(monkeypatch, right)
        assert _serve(right) == "ROUTE-BETA:BETA"
        _use_tree(monkeypatch, left)
        assert _serve(left) == "ROUTE-ALPHA:ALPHA"
    finally:
        _drop_tree(tmp_path)


def test_scaffold_folder_named_app_starts_through_uvicorn(tmp_path):
    from ux_compose.scaffold import create_app

    root = create_app(tmp_path / "app", name="App", level=1, host="asgi")
    port = _free_port()
    env = dict(os.environ)
    inherited = env.get("PYTHONPATH")
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not inherited else src + os.pathsep + inherited
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:asgi",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    url = f"http://127.0.0.1:{port}/hello"
    try:
        body = _wait_http(proc, url)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    assert "hello" in body.lower()


def test_myapp_main_py_builds_at_import(tmp_path, monkeypatch):
    pkg = _write(
        tmp_path / "myapp",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'from-main'\n"
            ),
        },
    )
    (pkg / "main.py").write_text(
        "from pathlib import Path\n"
        "from ux_compose.build import build\n"
        "app, asgi, bundle = build(\n"
        "    Path(__file__).resolve().parent,\n"
        "    name='My',\n"
        "    host='asgi',\n"
        "    live='null',\n"
        "    level=1,\n"
        ")\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        sys.modules.pop("myapp", None)
        sys.modules.pop("myapp.main", None)
        importlib.invalidate_caches()
        main = importlib.import_module("myapp.main")
        response = asgi_get(main.asgi, "/hello")
        assert response.status_code == 200
        assert response.text == "from-main"
    finally:
        _drop_tree(tmp_path)
        for key in list(sys.modules):
            if key == "myapp" or key.startswith("myapp."):
                sys.modules.pop(key, None)


def test_models_imported_before_build_keep_identity_and_state(tmp_path, monkeypatch):
    import fastapi

    pkg = _write(
        tmp_path / "myapp",
        {
            "models.py": "class Item:\n    pass\nMARKER = {'n': 1}\n",
            "routes/hello.py": (
                "from myapp.models import Item, MARKER\n"
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return f'{id(Item)}:{MARKER[\"n\"]}'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    fastapi_type = fastapi.FastAPI
    json_mod = sys.modules["json"]
    try:
        for key in list(sys.modules):
            if key == "myapp" or key.startswith("myapp."):
                sys.modules.pop(key, None)
        importlib.invalidate_caches()
        models = importlib.import_module("myapp.models")
        item = models.Item
        models.MARKER["n"] = 7
        body = _serve(pkg)
        assert body == f"{id(item)}:7"
        assert sys.modules["myapp.models"] is models
        assert models.Item is item
        assert models.MARKER["n"] == 7
        assert sys.modules["json"] is json_mod
        assert sys.modules["fastapi"] is fastapi
        assert fastapi.FastAPI is fastapi_type
    finally:
        _drop_tree(tmp_path)
        for key in list(sys.modules):
            if key == "myapp" or key.startswith("myapp."):
                sys.modules.pop(key, None)


def test_route_edit_is_picked_up_on_rebuild(tmp_path):
    pkg = _write(
        tmp_path / "editpkg",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'version-1'\n"
            ),
        },
    )
    try:
        assert _serve(pkg) == "version-1"
        hello = pkg / "routes" / "hello.py"
        hello.write_text(
            "class Hello:\n"
            "    routes = ('get',)\n"
            "    def render(self):\n"
            "        return 'version-2'\n",
            encoding="utf-8",
        )
        # Bytecode is keyed by mtime. Move it forward so a real reload
        # cannot reuse the previous pyc.
        fresh = time.time() + 5
        os.utime(hello, (fresh, fresh))
        assert _serve(pkg) == "version-2"
    finally:
        _drop_tree(tmp_path)


def test_threaded_same_name_builds_serve_their_own_routes(tmp_path):
    left = _write(
        tmp_path / "left" / "demo",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'THREAD-ALPHA'\n"
            ),
        },
    )
    right = _write(
        tmp_path / "right" / "demo",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'THREAD-BETA'\n"
            ),
        },
    )
    barrier = threading.Barrier(8)
    errors: list[BaseException] = []
    guard = threading.Lock()

    def work(index: int) -> None:
        pkg = left if index % 2 == 0 else right
        expected = "THREAD-ALPHA" if index % 2 == 0 else "THREAD-BETA"
        other = "THREAD-BETA" if expected == "THREAD-ALPHA" else "THREAD-ALPHA"
        try:
            barrier.wait(timeout=10)
            body = _serve(pkg)
            if body != expected or other in body:
                raise AssertionError(body)
        except BaseException as exc:
            with guard:
                errors.append(exc)

    threads = [threading.Thread(target=work, args=(index,)) for index in range(8)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        assert not any(thread.is_alive() for thread in threads)
        assert errors == []
    finally:
        _drop_tree(tmp_path)


def _free_port() -> int:
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http(proc: subprocess.Popen[str], url: str) -> str:
    deadline = time.time() + 15
    last = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            err = proc.stderr.read() if proc.stderr is not None else ""
            raise AssertionError(err or f"uvicorn exited {proc.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                return response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = str(exc)
            time.sleep(0.05)
    raise AssertionError(last or "uvicorn did not serve /hello")
