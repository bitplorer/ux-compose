"""Package import identity across build().

Deterministic: marked ``import_isolation`` so pytest-randomly does not
reorder these cases. The seeded host step does not collect this module.
"""
from __future__ import annotations

import importlib
import logging
import os
import subprocess
import sys
import textwrap
import threading
import time
import types
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


def _run_daemon(fn, timeout: float) -> None:
    """Run ``fn`` on a daemon thread. A hung import fails at ``timeout``."""
    errors: list[BaseException] = []

    def target() -> None:
        try:
            fn()
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    assert not thread.is_alive(), "thread still running"
    if errors:
        raise errors[0]


def test_import_lock_and_package_lock_do_not_deadlock(tmp_path, monkeypatch):
    """Thread B holds shared_mod's import lock and then build().

    Thread A builds while its route imports shared_mod. Events order the
    two sides. A deadlock fails the join. The importer must raise nothing.
    """
    from starlette.testclient import TestClient

    from ux_compose.build import build

    root = tmp_path
    probe: dict[str, str] = {}
    errors: dict[str, BaseException] = {}

    def mk(folder: str, files: dict[str, str], name: str = "myapp") -> Path:
        pkg = root / folder / name
        payload = {"routes/__init__.py": "", "__init__.py": "", **files}
        for rel, src in payload.items():
            dest = pkg / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(textwrap.dedent(src), encoding="utf-8")
        return pkg

    def get(pkg: Path, path: str) -> str:
        _app, asgi, _bundle = build(pkg, name="X", host="asgi", live="null", level=1)
        response = TestClient(asgi, raise_server_exceptions=False).get(path)
        return f"{response.status_code}:{response.text.strip()[:60]!r}"

    def route(cls: str, expr: str, pre: str = "") -> str:
        return pre + (
            f"class {cls}:\n    def render(self):\n        return {expr}\n"
        )

    (root / "x1gate.py").write_text(
        "import threading\n"
        "IN_SHARED = threading.Event()\n"
        "RELEASE_SHARED = threading.Event()\n"
        "ROUTE_IMPORTING = threading.Event()\n",
        encoding="utf-8",
    )
    inner = mk("p2", {"routes/b.py": route("B", "'<p>b</p>'")}, name="other")
    (root / "shared_mod.py").write_text(
        "import x1gate\n"
        "x1gate.IN_SHARED.set()\n"
        "if not x1gate.RELEASE_SHARED.wait(10):\n"
        "    raise TimeoutError('shared_mod was not released')\n"
        "from pathlib import Path\n"
        "from ux_compose.build import build\n"
        f"build(Path({str(inner)!r}), name='S', host='asgi', live='null', level=1)\n"
        "X = 1\n",
        encoding="utf-8",
    )
    outer = mk(
        "p1",
        {
            "routes/a.py": (
                "import x1gate\n"
                "x1gate.ROUTE_IMPORTING.set()\n"
                "import shared_mod\n"
            )
            + route("A", "'<p>a</p>'"),
        },
    )
    monkeypatch.syspath_prepend(str(root))

    def import_shared() -> None:
        try:
            importlib.import_module("shared_mod")
        except BaseException as exc:
            errors["importer"] = exc

    def build_outer() -> None:
        try:
            probe["body"] = get(outer, "/a")
        except BaseException as exc:
            errors["builder"] = exc

    try:
        importer = threading.Thread(target=import_shared, daemon=True)
        builder = threading.Thread(target=build_outer, daemon=True)
        importer.start()
        assert importlib.import_module("x1gate").IN_SHARED.wait(5)
        builder.start()
        assert importlib.import_module("x1gate").ROUTE_IMPORTING.wait(5)
        importlib.import_module("x1gate").RELEASE_SHARED.set()
        builder.join(10)
        importer.join(10)
        assert not builder.is_alive() and not importer.is_alive()
        assert "importer" not in errors, errors.get("importer")
        assert "builder" not in errors, errors.get("builder")
        assert probe["body"].startswith("200:")
        assert "<p>a</p>" in probe["body"]
    finally:
        _drop_tree(root)
        for key in list(sys.modules):
            if key in {"shared_mod", "x1gate", "myapp", "other"} or key.startswith(
                ("myapp.", "other.", "ux_surface_")
            ):
                sys.modules.pop(key, None)


def test_reentrant_build_same_package_name_keeps_both_routes(tmp_path, monkeypatch):
    inner = _write(
        tmp_path / "right" / "demo",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'INNER'\n"
            ),
        },
    )
    outer = _write(
        tmp_path / "left" / "demo",
        {
            "routes/hello.py": (
                "from pathlib import Path\n"
                "from ux_compose.build import build\n"
                f"BUILT = build(Path({str(inner)!r}), name='I', host='asgi', live='null', level=1)\n"
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OUTER'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(outer.parent))
    holder: dict[str, object] = {}

    def load() -> None:
        holder["mod"] = importlib.import_module("demo.routes.hello")

    try:
        _run_daemon(load, 10)
        mod = holder["mod"]
        inner_asgi = mod.BUILT[1]
        assert asgi_get(inner_asgi, "/hello").text == "INNER"
        outer_body = _serve(outer)
        assert outer_body == "OUTER"
    finally:
        _drop_tree(tmp_path)
        for key in list(sys.modules):
            if key == "demo" or key.startswith("demo."):
                sys.modules.pop(key, None)


def test_reentrant_build_of_another_package_serves_both(tmp_path, monkeypatch):
    inner = _write(
        tmp_path / "right" / "other",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'INNER'\n"
            ),
        },
    )
    outer = _write(
        tmp_path / "left" / "demo",
        {
            "routes/hello.py": (
                "from pathlib import Path\n"
                "from ux_compose.build import build\n"
                f"BUILT = build(Path({str(inner)!r}), name='I', host='asgi', live='null', level=1)\n"
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OUTER'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(outer.parent))
    holder: dict[str, object] = {}

    def load() -> None:
        holder["mod"] = importlib.import_module("demo.routes.hello")

    try:
        _run_daemon(load, 10)
        mod = holder["mod"]
        assert asgi_get(mod.BUILT[1], "/hello").text == "INNER"
        assert _serve(outer) == "OUTER"
    finally:
        _drop_tree(tmp_path)
        for key in list(sys.modules):
            if key in {"demo", "other"} or key.startswith(("demo.", "other.")):
                sys.modules.pop(key, None)


def test_build_folder_named_json_keeps_stdlib(tmp_path):
    import json

    json_mod = sys.modules["json"]
    dumps = json.dumps
    pkg = _write(
        tmp_path / "json",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'from-json-app'\n"
            ),
        },
    )
    try:
        assert _serve(pkg) == "from-json-app"
        assert sys.modules["json"] is json_mod
        assert json.dumps is dumps
        assert json.dumps({"a": 1}) == '{"a": 1}'
    finally:
        _drop_tree(tmp_path)
        for key in list(sys.modules):
            if key == "json.routes" or key.startswith("json.routes.") or key.startswith("json.routes"):
                origin = getattr(sys.modules.get(key), "__file__", None)
                if isinstance(origin, str):
                    try:
                        if Path(origin).resolve().is_relative_to(tmp_path.resolve()):
                            sys.modules.pop(key, None)
                    except OSError:
                        continue


def test_path_keyerror_does_not_abort_build(tmp_path):
    pkg = _write(
        tmp_path / "widget",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'widget-ok'\n"
            ),
        },
    )

    class BoomPath:
        def __iter__(self):
            raise KeyError("widget")

    sentinel = types.ModuleType("widget")
    sentinel.__file__ = str(pkg / "__init__.py")
    sentinel.__path__ = BoomPath()
    sys.modules["widget"] = sentinel
    try:
        assert _serve(pkg) == "widget-ok"
        assert sys.modules["widget"] is sentinel
    finally:
        if sys.modules.get("widget") is sentinel:
            sys.modules.pop("widget", None)
        _drop_tree(tmp_path)


def test_repeated_builds_do_not_grow_sys_modules(tmp_path, monkeypatch):
    """Rebuilding one folder adds nothing.

    A different package name that is on ``sys.path`` adds exactly that
    package, its ``routes`` package, and the route module. Those three
    stay so the served module remains importable
    (``release_build_package_modules`` keeps the route and anchors its
    parents). A rebuild of the same name adds nothing else.
    """
    from ux_compose.build import build

    def hello(name: str) -> dict[str, str]:
        return {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                f"        return {name!r}\n"
            ),
        }

    warm = _write(tmp_path / "warm" / "warmpkg", hello("warm"))
    names = ["warmpkg"]
    monkeypatch.syspath_prepend(str(warm.parent))
    try:
        build(warm, name="W", host="asgi", live="null", level=1)
        base = len(sys.modules)
        for _ in range(30):
            built = build(warm, name="W", host="asgi", live="null", level=1)
            assert asgi_get(built[1], "/hello").text == "warm"
        assert len(sys.modules) == base
        for index in range(30):
            name = f"pkg{index}"
            names.append(name)
            pkg = _write(tmp_path / f"d{index}" / name, hello(f"n{index}"))
            monkeypatch.syspath_prepend(str(pkg.parent))
            before = set(sys.modules)
            built = build(pkg, name="N", host="asgi", live="null", level=1)
            assert asgi_get(built[1], "/hello").text == f"n{index}"
            added = set(sys.modules) - before
            assert added == {name, f"{name}.routes", f"{name}.routes.hello"}
            again = set(sys.modules)
            built = build(pkg, name="N", host="asgi", live="null", level=1)
            assert set(sys.modules) == again
            assert asgi_get(built[1], "/hello").text == f"n{index}"
    finally:
        for name in names:
            _purge_package(name)
        _drop_tree(tmp_path)


def test_sixteen_threads_three_builds_serve_their_own_routes(tmp_path):
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
    barrier = threading.Barrier(16)
    errors: list[BaseException] = []
    guard = threading.Lock()

    def work(index: int) -> None:
        try:
            barrier.wait(timeout=10)
            for round_index in range(3):
                pkg = left if (index + round_index) % 2 == 0 else right
                expected = "THREAD-ALPHA" if pkg is left else "THREAD-BETA"
                body = _serve(pkg)
                if body != expected:
                    raise AssertionError(body)
        except BaseException as exc:
            with guard:
                errors.append(exc)

    threads = [
        threading.Thread(target=work, args=(index,), daemon=True) for index in range(16)
    ]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)
        assert not any(thread.is_alive() for thread in threads)
        assert errors == []
    finally:
        _drop_tree(tmp_path)


def _marker(html: str) -> str:
    start = html.find("<div id=m>")
    if start < 0:
        return html[:80]
    start += len("<div id=m>")
    end = html.find("</div>", start)
    return html[start:end] if end >= 0 else html[start:start + 80]


def test_concurrent_same_name_builds_keep_their_helpers(tmp_path):
    """16 threads x 3 builds, 4 shared package names, each route imports a sibling."""
    from starlette.testclient import TestClient

    from ux_compose.build import build

    jobs: list[tuple[int, Path, str]] = []
    for thread_index in range(16):
        for build_index in range(3):
            pkg_name = f"thh{(thread_index + build_index) % 4}"
            marker = f"T{thread_index}_B{build_index}_{pkg_name}"
            root = tmp_path / f"t{thread_index}b{build_index}" / pkg_name
            (root / "routes").mkdir(parents=True)
            (root / "__init__.py").write_text("", encoding="utf-8")
            (root / "routes" / "__init__.py").write_text("", encoding="utf-8")
            (root / "routes" / "_helper.py").write_text(
                f"import time\ntime.sleep(0.01)\nTEXT = {marker!r}\n",
                encoding="utf-8",
            )
            (root / "routes" / "home.py").write_text(
                "import time\n"
                f"from {pkg_name}.routes._helper import TEXT\n"
                "time.sleep(0.01)\n"
                f"OWN = {marker!r}\n"
                "class Home:\n"
                "    def render(self):\n"
                "        return f'<div id=m>{OWN}|{TEXT}</div>'\n",
                encoding="utf-8",
            )
            jobs.append((thread_index, root, marker))

    results: dict[str, object] = {}
    errors: list[tuple[str, str]] = []
    barrier = threading.Barrier(16)
    guard = threading.Lock()

    def worker(thread_index: int) -> None:
        barrier.wait(timeout=10)
        for owner, root, marker in jobs:
            if owner != thread_index:
                continue
            try:
                sys.path.insert(0, str(root.parent))
                results[marker] = build(
                    root, name=f"T{thread_index}", host="fastapi", live="null", level=1
                )[1]
            except Exception as exc:
                with guard:
                    errors.append((marker, f"{type(exc).__name__}: {exc}"[:160]))

    threads = [
        threading.Thread(target=worker, args=(index,), daemon=True) for index in range(16)
    ]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)
        assert not any(thread.is_alive() for thread in threads)
        wrong: list[tuple[str, str]] = []
        for marker, asgi in results.items():
            with TestClient(asgi) as client:
                got = _marker(client.get("/home").text)
            if got != f"{marker}|{marker}":
                wrong.append((marker, got))
        assert errors == []
        assert wrong == []
    finally:
        _drop_tree(tmp_path)
        for key in list(sys.modules):
            if key.startswith("thh") and key[3:4].isdigit():
                sys.modules.pop(key, None)


def test_cross_thread_same_name_build_times_out_instead_of_hanging(tmp_path, monkeypatch):
    """A route import that joins build() of the same name on another thread."""
    import builtins

    from ux_compose.build import build

    inner = tmp_path / "B2" / "reent2"
    (inner / "routes").mkdir(parents=True)
    (inner / "__init__.py").write_text("", encoding="utf-8")
    (inner / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (inner / "routes" / "home.py").write_text(
        "class Home:\n    def render(self):\n        return '<div id=m>REENT2_B</div>'\n",
        encoding="utf-8",
    )
    outer = tmp_path / "A2" / "reent2"
    (outer / "routes").mkdir(parents=True)
    (outer / "__init__.py").write_text("", encoding="utf-8")
    (outer / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (outer / "routes" / "home.py").write_text(
        "import builtins, threading\n"
        "from pathlib import Path\n"
        "from ux_compose.build import build\n"
        "def _b():\n"
        "    try:\n"
        f"        build(Path({str(inner)!r}), name='B2', host='fastapi', live='null', level=1, lock_timeout=1)\n"
        "        builtins._REENT2_EXC = 'ok'\n"
        "    except Exception as exc:\n"
        "        builtins._REENT2_EXC = f'{type(exc).__name__}: {exc}'\n"
        "_t = threading.Thread(target=_b, daemon=True)\n"
        "_t.start()\n"
        "_t.join(20)\n"
        "builtins._REENT2_JOINED = not _t.is_alive()\n"
        "class Home:\n"
        "    def render(self):\n"
        "        return '<div id=m>REENT2_A</div>'\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(outer.parent))
    monkeypatch.delattr(builtins, "_REENT2_EXC", raising=False)
    monkeypatch.delattr(builtins, "_REENT2_JOINED", raising=False)

    def run() -> None:
        build(outer, name="A2", host="fastapi", live="null", level=1)

    started = time.time()
    thread = threading.Thread(target=run, daemon=True)
    try:
        thread.start()
        thread.join(12)
        assert not thread.is_alive()
        assert time.time() - started < 12
        recorded = getattr(builtins, "_REENT2_EXC", "")
        assert recorded.startswith("BuildLockTimeout")
        assert "reent2" in recorded
        assert "UX_COMPOSE_BUILD_LOCK_TIMEOUT" in recorded
        assert getattr(builtins, "_REENT2_JOINED", False) is True
    finally:
        _drop_tree(tmp_path)
        for key in list(sys.modules):
            if key == "reent2" or key.startswith("reent2."):
                sys.modules.pop(key, None)


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


def _purge_package(name: str) -> None:
    for key in list(sys.modules):
        if key == name or key.startswith(name + "."):
            sys.modules.pop(key, None)


def _hints_package(root: Path, name: str, counter: Path) -> Path:
    pkg = root / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "models.py").write_text("class M:\n    pass\n", encoding="utf-8")
    (pkg / "routes" / "h.py").write_text(
        "from __future__ import annotations\n"
        "import dataclasses\n"
        "import typing\n"
        f"from {name}.models import M\n"
        f"open({str(counter)!r}, 'a', encoding='utf-8').write('x')\n"
        "@dataclasses.dataclass\n"
        "class D:\n"
        "    m: M | None = None\n"
        "class H:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return '<p>' + str(typing.get_type_hints(D)) + '</p>'\n",
        encoding="utf-8",
    )
    return pkg


def test_type_hints_survive_build_on_path(tmp_path, monkeypatch):
    """Future annotations resolve after build when the folder is on sys.path."""
    from starlette.testclient import TestClient

    from ux_compose.build import build

    name = "hinton"
    counter = tmp_path / f"{name}-runs.txt"
    counter.write_text("", encoding="utf-8")
    pkg = _hints_package(tmp_path / "on", name, counter)
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        _app, asgi, _bundle = build(pkg, name="X", host="asgi", live="null", level=1)
        response = TestClient(asgi).get("/h")
        assert response.status_code == 200, response.text
        assert "M" in response.text
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_route_file_runs_once_over_three_builds(tmp_path, monkeypatch):
    from ux_compose.build import build

    name = "onceapp"
    counter = tmp_path / "once-runs.txt"
    counter.write_text("", encoding="utf-8")
    pkg = _hints_package(tmp_path, name, counter)
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        for _ in range(3):
            build(pkg, name="X", host="asgi", live="null", level=1)
        assert counter.read_text(encoding="utf-8") == "x"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_import_after_build_is_the_served_module(tmp_path, monkeypatch):
    from ux_compose.build import build

    name = "idapp"
    pkg = tmp_path / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "a.py").write_text(
        "import sys\n"
        "SERVED = id(sys.modules[__name__])\n"
        "class A:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return str(SERVED)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        _app, asgi, _bundle = build(pkg, name="X", host="asgi", live="null", level=1)
        mod = importlib.import_module(f"{name}.routes.a")
        assert asgi_get(asgi, "/a").text == str(id(mod))
        assert sys.modules[f"{name}.routes.a"] is mod
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_same_folder_thirty_builds_do_not_grow_sys_modules(tmp_path):
    from ux_compose.build import build

    name = "flatapp"
    pkg = _write(
        tmp_path / name,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'flat'\n"
            ),
        },
    )
    try:
        build(pkg, name="X", host="asgi", live="null", level=1)
        base = len(sys.modules)
        for _ in range(29):
            built = build(pkg, name="X", host="asgi", live="null", level=1)
            assert asgi_get(built[1], "/a").text == "flat"
        assert len(sys.modules) == base
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_distinct_folders_grow_sys_modules_at_most_once(tmp_path):
    from ux_compose.build import build

    names: list[str] = []
    try:
        for index in range(3):
            name = f"grow{index}"
            names.append(name)
            pkg = _write(
                tmp_path / f"d{index}" / name,
                {
                    "routes/a.py": (
                        "class A:\n"
                        "    routes = ('get',)\n"
                        "    def render(self):\n"
                        f"        return {name!r}\n"
                    ),
                },
            )
            before = len(sys.modules)
            built = build(pkg, name="X", host="asgi", live="null", level=1)
            assert asgi_get(built[1], "/a").text == name
            assert f"{name}.routes.a" in sys.modules
            after = len(sys.modules)
            assert after > before
            built = build(pkg, name="X", host="asgi", live="null", level=1)
            assert len(sys.modules) == after
            assert asgi_get(built[1], "/a").text == name
    finally:
        for name in names:
            _purge_package(name)
        _drop_tree(tmp_path)


def test_different_name_builds_while_same_name_is_held(tmp_path, monkeypatch):
    """A different package name must not wait on a name that is already importing."""
    from ux_compose.build import build

    (tmp_path / "holdgate.py").write_text(
        "import threading\n"
        "ENTERED = threading.Event()\n"
        "RELEASE = threading.Event()\n"
        "FINISHED = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    held = _write(
        tmp_path / "held" / "heldapp",
        {
            "routes/a.py": (
                "import holdgate\n"
                "holdgate.ENTERED.set()\n"
                "holdgate.RELEASE.wait(10)\n"
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'held'\n"
            ),
        },
    )
    other = _write(
        tmp_path / "other" / "otherapp",
        {
            "routes/a.py": (
                "import holdgate\n"
                "holdgate.FINISHED.set()\n"
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'other'\n"
            ),
        },
    )
    errors: list[BaseException] = []

    def run(pkg: Path) -> None:
        try:
            build(pkg, name="X", host="asgi", live="null", level=1)
        except BaseException as exc:
            errors.append(exc)

    gate = importlib.import_module("holdgate")
    threads = [
        threading.Thread(target=run, args=(held,), daemon=True),
        threading.Thread(target=run, args=(other,), daemon=True),
    ]
    try:
        threads[0].start()
        assert gate.ENTERED.wait(5)
        threads[1].start()
        assert gate.FINISHED.wait(2), "different name waited on the held name"
        gate.RELEASE.set()
        for thread in threads:
            thread.join(5)
        assert not any(thread.is_alive() for thread in threads)
        assert errors == []
    finally:
        _purge_package("heldapp")
        _purge_package("otherapp")
        sys.modules.pop("holdgate", None)
        _drop_tree(tmp_path)


def test_helper_imported_by_the_route_stays_after_build(tmp_path, monkeypatch):
    from ux_compose.build import build

    name = "helplock"
    pkg = _write(
        tmp_path / name,
        {
            "models.py": "MARKER = {'n': 1}\n",
            "routes/a.py": (
                f"from {name}.models import MARKER\n"
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return str(MARKER['n'])\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/a").text == "1"
        assert f"{name}.models" in sys.modules
        models = sys.modules[f"{name}.models"]
        models.MARKER["n"] = 9
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert sys.modules[f"{name}.models"] is models
        assert asgi_get(built[1], "/a").text == "9"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_route_package_parents_stay_importable(tmp_path, monkeypatch):
    from ux_compose.build import build

    name = "anchorapp"
    pkg = _write(
        tmp_path / name,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'anchored'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/a").text == "anchored"
        mod = importlib.import_module(f"{name}.routes.a")
        assert sys.modules[name] is not None
        assert sys.modules[f"{name}.routes"] is not None
        assert sys.modules[f"{name}.routes.a"] is mod
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_preimported_subpackage_survives_build(tmp_path, monkeypatch):
    from ux_compose.build import build

    name = "snapapp"
    pkg = _write(
        tmp_path / name,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'snap'\n"
            ),
        },
    )
    legacy = pkg / "routes" / "legacy"
    legacy.mkdir()
    (legacy / "__init__.py").write_text("TOKEN = 'mine'\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        _purge_package(name)
        imported = importlib.import_module(f"{name}.routes.legacy")
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/a").text == "snap"
        assert sys.modules[f"{name}.routes.legacy"] is imported
        assert imported.TOKEN == "mine"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_package_import_lock_blocks_another_thread():
    from ux_compose.routing.core import isolate_package_imports, package_import_lock

    release = threading.Event()
    held = threading.Event()
    done = threading.Event()

    def holder() -> None:
        package_import_lock.acquire()
        try:
            held.set()
            release.wait(5)
        finally:
            package_import_lock.release()

    def worker() -> None:
        isolate_package_imports(Path("/tmp/ux-compose-lock-probe"))
        done.set()

    owner = threading.Thread(target=holder, daemon=True)
    other = threading.Thread(target=worker, daemon=True)
    owner.start()
    assert held.wait(2)
    other.start()
    assert not done.wait(0.3)
    release.set()
    assert done.wait(2)
    owner.join(2)
    other.join(2)
    assert not owner.is_alive() and not other.is_alive()


def test_on_path_route_edit_is_picked_up(tmp_path, monkeypatch):
    name = "editon"
    pkg = _write(
        tmp_path / name,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'version-1'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
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
        fresh = time.time() + 5
        os.utime(hello, (fresh, fresh))
        assert _serve(pkg) == "version-2"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_detached_loads_do_not_share_a_module_key(tmp_path):
    """Two directories stay distinct when the dotted name is already taken."""
    left = _write(
        tmp_path / "left" / "demo",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'ALPHA'\n"
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
                "        return 'BETA'\n"
            ),
        },
    )
    for part in ("demo", "demo.routes", "demo.routes.hello"):
        sys.modules[part] = types.ModuleType(part)
    try:
        assert _serve(left) == "ALPHA"
        assert _serve(right) == "BETA"
    finally:
        _purge_package("demo")
        for key in list(sys.modules):
            if key.startswith("ux_surface_") or key.startswith("demo_"):
                sys.modules.pop(key, None)
        _drop_tree(tmp_path)


def _hold_package(root: Path, name: str) -> Path:
    return _write(
        root / name,
        {
            "routes/a.py": (
                "import holdgate\n"
                "holdgate.ENTERED.set()\n"
                "holdgate.RELEASE.wait(30)\n"
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                f"        return {name!r}\n"
            ),
        },
    )


def test_default_timeout_serves_a_nine_second_route(tmp_path, monkeypatch):
    """Both threads get 200 when one route takes 9s and the default wait is 60s."""
    from ux_compose.build import build

    monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
    name = "slowapp"
    pkg = _write(
        tmp_path / name,
        {
            "routes/a.py": (
                "import time\n"
                "time.sleep(9)\n"
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'slow-ok'\n"
            ),
        },
    )
    errors: list[str] = []
    bodies: list[str] = []

    def run() -> None:
        try:
            built = build(pkg, name="X", host="asgi", live="null", level=1)
            response = asgi_get(built[1], "/a")
            if response.status_code != 200:
                errors.append(f"{response.status_code}:{response.text[:80]}")
            else:
                bodies.append(response.text)
        except BaseException as exc:
            errors.append(f"{type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=run, daemon=True) for _ in range(2)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)
        assert not any(thread.is_alive() for thread in threads)
        assert errors == []
        assert bodies == ["slow-ok", "slow-ok"]
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_tiny_lock_timeout_names_package_and_setting(tmp_path, monkeypatch):
    from ux_compose.build import build

    (tmp_path / "holdgate.py").write_text(
        "import threading\n"
        "ENTERED = threading.Event()\n"
        "RELEASE = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
    name = "tinyapp"
    pkg = _hold_package(tmp_path, name)
    gate = importlib.import_module("holdgate")
    errors: list[BaseException] = []

    def hold() -> None:
        try:
            build(pkg, name="H", host="asgi", live="null", level=1)
        except BaseException as exc:
            errors.append(exc)

    def wait() -> None:
        try:
            build(pkg, name="W", host="asgi", live="null", level=1, lock_timeout=0.2)
        except BaseException as exc:
            errors.append(exc)

    holder = threading.Thread(target=hold, daemon=True)
    waiter = threading.Thread(target=wait, daemon=True)
    try:
        holder.start()
        assert gate.ENTERED.wait(5)
        waiter.start()
        waiter.join(3)
        assert not waiter.is_alive()
        assert len(errors) == 1
        exc = errors[0]
        assert type(exc).__name__ == "BuildLockTimeout"
        text = str(exc)
        assert name in text
        assert "UX_COMPOSE_BUILD_LOCK_TIMEOUT" in text
        gate.RELEASE.set()
        holder.join(5)
        assert not holder.is_alive()
    finally:
        gate.RELEASE.set()
        _purge_package(name)
        sys.modules.pop("holdgate", None)
        _drop_tree(tmp_path)


def test_env_lock_timeout_and_none_override(tmp_path, monkeypatch):
    from ux_compose.build import build

    (tmp_path / "holdgate.py").write_text(
        "import threading\n"
        "ENTERED = threading.Event()\n"
        "RELEASE = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = "envapp"
    pkg = _hold_package(tmp_path, name)
    gate = importlib.import_module("holdgate")
    monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "0.2")
    seen: list[BaseException] = []

    def hold() -> None:
        build(pkg, name="H", host="asgi", live="null", level=1, lock_timeout=None)

    def timed() -> None:
        try:
            build(pkg, name="W", host="asgi", live="null", level=1)
        except BaseException as exc:
            seen.append(exc)

    def unlimited() -> None:
        try:
            build(pkg, name="U", host="asgi", live="null", level=1, lock_timeout=None)
            seen.append(None)
        except BaseException as exc:
            seen.append(exc)

    holder = threading.Thread(target=hold, daemon=True)
    try:
        holder.start()
        assert gate.ENTERED.wait(5)
        waiter = threading.Thread(target=timed, daemon=True)
        waiter.start()
        waiter.join(2)
        assert not waiter.is_alive()
        assert len(seen) == 1 and type(seen[0]).__name__ == "BuildLockTimeout"
        assert name in str(seen[0])
        follower = threading.Thread(target=unlimited, daemon=True)
        follower.start()
        follower.join(0.3)
        assert follower.is_alive()
        gate.RELEASE.set()
        follower.join(5)
        holder.join(5)
        assert not follower.is_alive() and not holder.is_alive()
        assert None in seen
    finally:
        gate.RELEASE.set()
        _purge_package(name)
        sys.modules.pop("holdgate", None)
        _drop_tree(tmp_path)


def test_route_import_does_not_keep_another_threads_helper(tmp_path, monkeypatch):
    """T2 caches folder B's helper, then A's route imports that name.

    Pausing inside the route is too late: the package is already A's.
    The import is paused before the route module loads, which is the
    order where B's helper is what gets served.
    """
    import ux_compose.surfaces as surfaces

    for side, mark in (("A", "HELPER_A"), ("B", "HELPER_B")):
        pkg = tmp_path / side / "myapp"
        (pkg / "routes").mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "helpers.py").write_text(f"MARK = {mark!r}\n", encoding="utf-8")
    (tmp_path / "A" / "myapp" / "routes" / "home.py").write_text(
        "from myapp.helpers import MARK\n"
        "class Home:\n"
        "    def render(self):\n"
        "        return f'<div id=m>A|{MARK}</div>'\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path / "B"))
    armed = threading.Event()
    cached = threading.Event()
    builder: dict[str, threading.Thread] = {}
    real_import = importlib.import_module

    def paused_import(name: str, package: str | None = None):
        if (
            builder.get("thread") is threading.current_thread()
            and not paused_import.tripped
            and (name == "myapp" or name.startswith("myapp."))
        ):
            paused_import.tripped = True
            armed.set()
            assert cached.wait(5), "T2 did not cache the helper"
        return real_import(name, package)

    paused_import.tripped = False
    monkeypatch.setattr(surfaces.importlib, "import_module", paused_import)

    from ux_compose.build import build

    out: dict[str, object] = {}

    def t2() -> None:
        assert armed.wait(5)
        module = real_import("myapp.helpers")
        out["t2"] = module.MARK
        cached.set()

    def t1() -> None:
        builder["thread"] = threading.current_thread()
        try:
            out["built"] = build(
                tmp_path / "A" / "myapp", name="A", host="asgi", live="null", level=1
            )
        except BaseException as exc:
            out["err"] = exc

    other = threading.Thread(target=t2, daemon=True)
    owner = threading.Thread(target=t1, daemon=True)
    try:
        other.start()
        owner.start()
        owner.join(15)
        other.join(5)
        assert not owner.is_alive() and not other.is_alive()
        assert "err" not in out, out.get("err")
        built = out["built"]
        assert asgi_get(built[1], "/home").text == "<div id=m>A|HELPER_A</div>"
    finally:
        _purge_package("myapp")
        _drop_tree(tmp_path)


def test_off_path_package_import_raises_module_not_found(tmp_path):
    """A package that is not on sys.path is not imported for the build.

    Main raises ModuleNotFoundError for that name. The pin must not
    invent a successful import.
    """
    from ux_compose.build import build
    from ux_compose.surfaces import SurfaceError

    name = "myapp"
    pkg = tmp_path / "off" / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "models").mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "models" / "__init__.py").write_text("class M:\n    pass\n", encoding="utf-8")
    (pkg / "routes" / "h.py").write_text(
        "from myapp.models import M\n"
        "class H:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return M.__name__\n",
        encoding="utf-8",
    )
    try:
        with pytest.raises(SurfaceError) as caught:
            build(pkg, name="X", host="asgi", live="null", level=1)
        cause = caught.value.__cause__
        assert isinstance(cause, ModuleNotFoundError)
        assert cause.name == "myapp"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_in_use_helper_from_another_folder_is_rejected(tmp_path, monkeypatch):
    """Building P2 must not serve a helper that another thread is loading from P1.

    The helper module is already in sys.modules from P1 and that import
    has not finished. Main serves P1's value. build() has to fail closed.
    Twenty overlaps each raise PackageImportConflict, and the two
    directories are the exception's loaded_from and building fields.
    """
    from ux_compose.build import build
    from ux_compose.routing.core import PackageImportConflict

    gate_name = "gate_foreign_helper"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nOUT = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    p1 = tmp_path / "P1" / "myapp"
    p2 = tmp_path / "P2" / "myapp"
    hold = f"import {gate_name}\nMARK = 'FROM_P1'\n{gate_name}.IN.set()\n{gate_name}.OUT.wait(0.15)\n"
    for folder, body in (
        (p1, hold),
        (p2, "MARK = 'FROM_P2'\n"),
    ):
        (folder / "routes").mkdir(parents=True)
        (folder / "__init__.py").write_text("", encoding="utf-8")
        (folder / "routes" / "__init__.py").write_text("", encoding="utf-8")
        (folder / "helpers.py").write_text(body, encoding="utf-8")
        (folder / "routes" / "home.py").write_text(
            "from myapp.helpers import MARK\n"
            "class Home:\n"
            "    routes = ('get',)\n"
            "    def render(self):\n"
            "        return MARK\n",
            encoding="utf-8",
        )
    monkeypatch.syspath_prepend(str(p1.parent))
    gate = importlib.import_module(gate_name)
    raised = 0
    try:
        for _ in range(20):
            _purge_package("myapp")
            importlib.invalidate_caches()
            gate.IN.clear()
            gate.OUT.clear()
            out: dict[str, object] = {}

            def loader() -> None:
                try:
                    importlib.import_module("myapp.helpers")
                except BaseException as exc:
                    out["loader"] = exc

            def builder() -> None:
                assert gate.IN.wait(5)
                try:
                    built = build(p2, name="X", host="asgi", live="null", level=1)
                    out["served"] = asgi_get(built[1], "/home").text
                except BaseException as exc:
                    out["err"] = exc
                finally:
                    gate.OUT.set()

            left = threading.Thread(target=loader, daemon=True)
            right = threading.Thread(target=builder, daemon=True)
            left.start()
            right.start()
            left.join(8)
            right.join(8)
            assert not left.is_alive() and not right.is_alive()
            err = out.get("err")
            assert isinstance(err, PackageImportConflict), out.get("served")
            assert err.loaded_from == p1.resolve()
            assert err.building == p2.resolve()
            assert out.get("served") != "FROM_P1"
            raised += 1
        assert raised == 20
    finally:
        gate.OUT.set()
        _purge_package("myapp")
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def test_importing_another_trees_main_serves_this_folder(tmp_path, monkeypatch):
    """Thread A is importing x1's myapp.main. Thread B's build of x2 serves x2.

    x2 does not ship main.py. The overlap is not a PackageImportConflict.
    Three builds each return x2's three routes.
    """
    from ux_compose.build import build

    gate_name = "gate_x1_main"
    (tmp_path / f"{gate_name}.py").write_text(
        "import time\nIN = __import__('threading').Event()\nFINISHED = None\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    x1 = tmp_path / "x1" / "myapp"
    x2 = tmp_path / "x2" / "myapp"
    x1.mkdir(parents=True)
    (x1 / "__init__.py").write_text("", encoding="utf-8")
    (x1 / "main.py").write_text(
        f"import {gate_name}\n"
        "import time\n"
        f"{gate_name}.IN.set()\n"
        "time.sleep(0.3)\n"
        f"{gate_name}.FINISHED = time.monotonic()\n"
        "VALUE = 'X1'\n",
        encoding="utf-8",
    )
    _write(
        x2,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'X2-a'\n"
            ),
            "routes/b.py": (
                "class B:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'X2-b'\n"
            ),
            "routes/c.py": (
                "class C:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'X2-c'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(x1.parent))
    gate = importlib.import_module(gate_name)
    served_ok = 0
    try:
        for _ in range(3):
            _purge_package("myapp")
            importlib.invalidate_caches()
            gate.IN.clear()
            gate.FINISHED = None
            out: dict[str, object] = {}

            def loader() -> None:
                try:
                    importlib.import_module("myapp.main")
                except BaseException as exc:
                    out["loader"] = exc

            def builder() -> None:
                assert gate.IN.wait(5)
                out["started"] = time.monotonic()
                try:
                    built = build(x2, name="X", host="asgi", live="null", level=1)
                    out["pages"] = [
                        asgi_get(built[1], "/a").text,
                        asgi_get(built[1], "/b").text,
                        asgi_get(built[1], "/c").text,
                    ]
                except BaseException as exc:
                    out["err"] = exc

            left = threading.Thread(target=loader, daemon=True)
            right = threading.Thread(target=builder, daemon=True)
            left.start()
            right.start()
            left.join(8)
            right.join(8)
            assert not left.is_alive() and not right.is_alive()
            assert out.get("loader") is None, out.get("loader")
            assert "err" not in out, out.get("err")
            assert out.get("pages") == ["X2-a", "X2-b", "X2-c"]
            assert out["started"] < gate.FINISHED
            served_ok += 1
        assert served_ok == 3
    finally:
        _purge_package("myapp")
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def test_blocked_foreign_import_times_out_as_build_lock_timeout(tmp_path, monkeypatch):
    """Waiting out a foreign import raises BuildLockTimeout and serves nothing.

    The other folder's main stays blocked. lock_timeout bounds the wait.
    The page from that folder is not returned.
    """
    from ux_compose.build import BuildLockTimeout, build

    gate_name = "gate_import_timeout"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nOUT = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    x1 = tmp_path / "x1" / "myapp"
    x2 = tmp_path / "x2" / "myapp"
    x1.mkdir(parents=True)
    (x1 / "__init__.py").write_text("", encoding="utf-8")
    (x1 / "main.py").write_text(
        f"import {gate_name}\n"
        f"{gate_name}.IN.set()\n"
        f"{gate_name}.OUT.wait(5)\n"
        "VALUE = 'X1'\n",
        encoding="utf-8",
    )
    _write(
        x2,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'X2-a'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(x1.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module("myapp.main")
        except BaseException as exc:
            out["loader"] = exc

    def builder() -> None:
        assert gate.IN.wait(5)
        try:
            built = build(
                x2, name="X", host="asgi", live="null", level=1, lock_timeout=0.2
            )
            out["served"] = asgi_get(built[1], "/a").text
        except BaseException as exc:
            out["err"] = exc
        finally:
            gate.OUT.set()

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=builder, daemon=True)
    try:
        left.start()
        right.start()
        left.join(8)
        right.join(8)
        assert not left.is_alive() and not right.is_alive()
        err = out.get("err")
        assert isinstance(err, BuildLockTimeout), err
        assert err.package == "myapp"
        assert err.timeout == 0.2
        assert "timed out waiting to build 'myapp' after 0.2s" in str(err)
        assert "served" not in out
    finally:
        gate.OUT.set()
        _purge_package("myapp")
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def test_off_path_route_runs_twice_across_three_builds(tmp_path):
    """Main runs an off-path route file twice, then keeps the module.

    Three builds of a folder that is not on sys.path execute the file
    twice in total. The dotted route module is still in sys.modules.
    """
    from ux_compose.build import build

    name = "runapp"
    counter = tmp_path / "runs.txt"
    counter.write_text("", encoding="utf-8")
    pkg = _write(
        tmp_path / name,
        {
            "routes/a.py": (
                f"open({str(counter)!r}, 'a', encoding='utf-8').write('x')\n"
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'ran'\n"
            ),
        },
    )
    try:
        for _ in range(3):
            built = build(pkg, name="X", host="asgi", live="null", level=1)
            assert asgi_get(built[1], "/a").text == "ran"
        assert counter.read_text(encoding="utf-8") == "xx"
        assert f"{name}.routes.a" in sys.modules
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_off_path_type_hints_survive_build(tmp_path):
    """Type hints in an off-path route still resolve after build."""
    from ux_compose.build import build

    name = "hintoff"
    pkg = _write(
        tmp_path / name,
        {
            "routes/h.py": (
                "from __future__ import annotations\n"
                "import typing\n"
                "class M:\n"
                "    pass\n"
                "class D:\n"
                "    m: M | None = None\n"
                "class H:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return str(typing.get_type_hints(D))\n"
            ),
        },
    )
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        text = asgi_get(built[1], "/h").text
        assert "M" in text
        assert f"{name}.routes.h" in sys.modules
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_package_init_helper_survives_three_builds(tmp_path, monkeypatch):
    """A helper package's __init__ stays imported, so hints keep resolving."""
    from starlette.testclient import TestClient

    from ux_compose.build import build

    name = "myapp"
    counter = tmp_path / "runs.txt"
    counter.write_text("", encoding="utf-8")
    pkg = tmp_path / "pi" / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "models").mkdir()
    (pkg / "models" / "__init__.py").write_text(
        "from __future__ import annotations\n"
        "import dataclasses\n"
        f"open({str(counter)!r}, 'a', encoding='utf-8').write('x')\n"
        "class M:\n"
        "    pass\n"
        "@dataclasses.dataclass\n"
        "class D:\n"
        "    m: M | None = None\n"
        "STATE = {'n': 0}\n",
        encoding="utf-8",
    )
    (pkg / "routes" / "h.py").write_text(
        "import typing\n"
        "from myapp.models import D\n"
        "class H:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return '<p>' + str(typing.get_type_hints(D)) + '</p>'\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        statuses: list[int] = []
        for _ in range(3):
            _app, asgi, _bundle = build(pkg, name="X", host="asgi", live="null", level=1)
            response = TestClient(asgi).get("/h")
            statuses.append(response.status_code)
            assert response.status_code == 200, response.text
        assert statuses == [200, 200, 200]
        assert counter.read_text(encoding="utf-8") == "x"
        assert f"{name}.models" in sys.modules
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_package_init_helper_keeps_state_across_import(tmp_path, monkeypatch):
    """The served route and a later import are the same models package."""
    from ux_compose.build import build

    name = "myapp"
    counter = tmp_path / "runs.txt"
    counter.write_text("", encoding="utf-8")
    pkg = tmp_path / "ps" / name
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "models").mkdir()
    (pkg / "models" / "__init__.py").write_text(
        f"open({str(counter)!r}, 'a', encoding='utf-8').write('x')\n"
        "STATE = {'n': 0}\n",
        encoding="utf-8",
    )
    (pkg / "routes" / "c.py").write_text(
        "from myapp import models\n"
        "class C:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return str(models.STATE['n'])\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        _app, asgi, _bundle = build(pkg, name="X", host="asgi", live="null", level=1)
        models = importlib.import_module(f"{name}.models")
        models.STATE["n"] = 7
        assert asgi_get(asgi, "/c").text == "7"
        assert counter.read_text(encoding="utf-8") == "x"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def _lock_timeout_package(tmp_path: Path, name: str, body: str) -> Path:
    return _write(
        tmp_path / name,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                f"        return {body!r}\n"
            ),
        },
    )


def test_env_lock_timeout_abc_names_the_setting(monkeypatch):
    from ux_compose.build import _UNSET, _resolve_lock_timeout

    monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "abc")
    with pytest.raises(ValueError, match="UX_COMPOSE_BUILD_LOCK_TIMEOUT"):
        _resolve_lock_timeout(_UNSET)


def test_env_lock_timeout_nan_names_the_setting(monkeypatch):
    from ux_compose.build import _UNSET, _resolve_lock_timeout

    monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "nan")
    with pytest.raises(ValueError, match="UX_COMPOSE_BUILD_LOCK_TIMEOUT"):
        _resolve_lock_timeout(_UNSET)


def test_env_lock_timeout_negative_names_the_setting(monkeypatch):
    from ux_compose.build import _UNSET, _resolve_lock_timeout

    monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "-2")
    with pytest.raises(ValueError, match="UX_COMPOSE_BUILD_LOCK_TIMEOUT"):
        _resolve_lock_timeout(_UNSET)


def test_negative_lock_timeout_is_rejected(tmp_path):
    """-1 must not reach the lock. That value waits forever once the lock is held."""
    from ux_compose.build import build

    pkg = _lock_timeout_package(tmp_path, "negapp", "neg")
    try:
        with pytest.raises(ValueError, match="UX_COMPOSE_BUILD_LOCK_TIMEOUT"):
            build(pkg, name="X", host="asgi", live="null", level=1, lock_timeout=-1)
    finally:
        _purge_package("negapp")
        _drop_tree(tmp_path)


def test_inf_lock_timeout_kwarg_waits_without_overflow(tmp_path):
    from ux_compose.build import _resolve_lock_timeout, build

    pkg = _lock_timeout_package(tmp_path, "infkw", "inf-kw")
    try:
        built = build(
            pkg, name="X", host="asgi", live="null", level=1, lock_timeout=float("inf")
        )
        assert asgi_get(built[1], "/a").text == "inf-kw"
        assert _resolve_lock_timeout(float("inf")) is None
    finally:
        _purge_package("infkw")
        _drop_tree(tmp_path)


def test_inf_lock_timeout_env_waits_without_overflow(tmp_path, monkeypatch):
    from ux_compose.build import _UNSET, _resolve_lock_timeout, build

    monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "inf")
    pkg = _lock_timeout_package(tmp_path, "infenv", "inf-env")
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/a").text == "inf-env"
        assert _resolve_lock_timeout(_UNSET) is None
        monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "infinite")
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/a").text == "inf-env"
    finally:
        _purge_package("infenv")
        _drop_tree(tmp_path)


def test_popping_parent_during_child_import_does_not_raise_keyerror(tmp_path, monkeypatch):
    """Another thread must not pop the parent between importlib's two lookups."""
    from ux_compose.routing.core import _forget_module

    pkg = tmp_path / "myapp"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text("MARK = 'HELPER'\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    _purge_package("myapp")
    importlib.invalidate_caches()

    original = sys.modules
    at_lookup = threading.Event()
    other_done = threading.Event()
    state: dict[str, object] = {"fired": False, "importer": None}

    class _ParentLookup(dict):
        def __getitem__(self, key: str):
            if (
                key == "myapp"
                and not state["fired"]
                and threading.current_thread() is state["importer"]
            ):
                state["fired"] = True
                at_lookup.set()
                assert other_done.wait(5), "popper did not return"
            return dict.__getitem__(self, key)

    lookup = _ParentLookup(original)
    out: dict[str, object] = {}

    def importer() -> None:
        try:
            module = importlib.import_module("myapp.helpers")
            out["mark"] = module.MARK
        except BaseException as exc:
            out["err"] = exc

    def popper() -> None:
        assert at_lookup.wait(5), "import never looked up the parent"
        _forget_module("myapp")
        other_done.set()

    owner = threading.Thread(target=importer, daemon=True)
    state["importer"] = owner
    other = threading.Thread(target=popper, daemon=True)
    sys.modules = lookup
    try:
        other.start()
        owner.start()
        owner.join(5)
        other.join(5)
        assert not owner.is_alive() and not other.is_alive()
        assert state["fired"]
        assert "err" not in out, out.get("err")
        assert out.get("mark") == "HELPER"
    finally:
        snapshot = dict(lookup)
        sys.modules = original
        original.update(snapshot)
        other_done.set()
        _purge_package("myapp")
        _drop_tree(tmp_path)


def test_release_drops_a_module_that_is_not_this_folder(tmp_path):
    """Something outside this tree is removed. A no-op release would keep it."""
    from ux_compose.build import build

    name = "dropapp"
    outside = tmp_path / "outside.py"
    outside.write_text("GHOST = 1\n", encoding="utf-8")
    pkg = _write(
        tmp_path / name,
        {
            "routes/a.py": (
                "import sys\n"
                "import types\n"
                f"ghost = types.ModuleType({name + '.ghost'!r})\n"
                f"ghost.__file__ = {str(outside)!r}\n"
                f"sys.modules[{name + '.ghost'!r}] = ghost\n"
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'dropped'\n"
            ),
        },
    )
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/a").text == "dropped"
        assert f"{name}.ghost" not in sys.modules
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_routes_package_init_is_not_kept_as_a_route(tmp_path, monkeypatch):
    """A routes subpackage is not a route file just because its directory sits under routes."""
    from ux_compose.build import build

    name = "nestapp"
    pkg = tmp_path / name
    (pkg / "routes" / "nest").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "nest" / "__init__.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    (pkg / "routes" / "home.py").write_text(
        f"from {name}.routes.nest import VALUE\n"
        "class Home:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return str(VALUE)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/home").text == "1"
        assert f"{name}.routes.nest" not in sys.modules
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_module_without_origins_is_not_a_route(tmp_path):
    from ux_compose.routing.core import _is_this_folder_route

    mod = types.ModuleType("plain.mod")
    assert _is_this_folder_route(mod, tmp_path) is False


def test_none_lock_timeout_ignores_a_short_default(tmp_path, monkeypatch):
    """None waits the other build out even when the default wait is tiny."""
    from ux_compose.build import build

    build_mod = sys.modules["ux_compose.build"]

    (tmp_path / "holdgate.py").write_text(
        "import threading\n"
        "ENTERED = threading.Event()\n"
        "RELEASE = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
    monkeypatch.setattr(build_mod, "_DEFAULT_LOCK_TIMEOUT", 0.2)
    name = "noneapp"
    pkg = _hold_package(tmp_path, name)
    gate = importlib.import_module("holdgate")
    seen: list[object] = []

    def hold() -> None:
        build(pkg, name="H", host="asgi", live="null", level=1, lock_timeout=None)

    def waiter() -> None:
        try:
            build(pkg, name="W", host="asgi", live="null", level=1, lock_timeout=None)
            seen.append(None)
        except BaseException as exc:
            seen.append(exc)

    holder = threading.Thread(target=hold, daemon=True)
    follower = threading.Thread(target=waiter, daemon=True)
    try:
        holder.start()
        assert gate.ENTERED.wait(5)
        follower.start()
        follower.join(0.4)
        assert follower.is_alive()
        gate.RELEASE.set()
        follower.join(5)
        holder.join(5)
        assert not follower.is_alive() and not holder.is_alive()
        assert seen == [None]
    finally:
        gate.RELEASE.set()
        _purge_package(name)
        sys.modules.pop("holdgate", None)
        _drop_tree(tmp_path)


def test_blank_lock_timeout_env_uses_the_default(tmp_path, monkeypatch):
    from ux_compose.build import build

    monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "   ")
    name = "blankapp"
    pkg = _write(
        tmp_path / name,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'blank-ok'\n"
            ),
        },
    )
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/a").text == "blank-ok"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_detached_module_is_not_left_in_sys_modules(tmp_path):
    """A path-unique module registered for this build is gone when build returns."""
    from ux_compose.build import build

    pkg = _write(
        tmp_path / "left" / "demo",
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'ALPHA'\n"
            ),
        },
    )
    for part in ("demo", "demo.routes", "demo.routes.hello"):
        sys.modules[part] = types.ModuleType(part)
    try:
        before = {key for key in sys.modules if key.startswith("ux_surface_")}
        built = build(pkg, name="D", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/hello").text == "ALPHA"
        leaked = [
            key for key in sys.modules if key.startswith("ux_surface_") and key not in before
        ]
        assert leaked == []
    finally:
        _purge_package("demo")
        for key in list(sys.modules):
            if key.startswith("ux_surface_") or key.startswith("demo"):
                sys.modules.pop(key, None)
        _drop_tree(tmp_path)


def test_failed_build_does_not_leave_the_package(tmp_path, monkeypatch):
    """A route that fails to import must not leave the package loaded.

    Package shells are not helpers. Keeping them after the route raises
    would leave ``myapp`` in ``sys.modules``.
    """
    from ux_compose.build import build
    from ux_compose.surfaces import SurfaceError

    name = "myapp"
    pkg = _write(
        tmp_path / name,
        {"routes/home.py": "raise RuntimeError('boom')\n"},
    )
    monkeypatch.syspath_prepend(str(pkg.parent))
    try:
        with pytest.raises(SurfaceError):
            build(pkg, name="X", host="asgi", live="null", level=1)
        left = [key for key in sys.modules if key == name or key.startswith(name + ".")]
        assert left == []
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_single_file_module_on_sys_path_pins_the_package(tmp_path, monkeypatch):
    """``myapp.py`` on sys.path makes the name importable, so the pin applies.

    The folder being built is what ``import myapp`` returns. Deleting the
    ``{package}.py`` check treats the name as off-path and serves the file.
    """
    from ux_compose.build import build

    on_path = tmp_path / "onpath"
    on_path.mkdir()
    (on_path / "myapp.py").write_text("VALUE = 'file'\n", encoding="utf-8")
    pkg = tmp_path / "off" / "myapp"
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("VALUE = 'pkg'\n", encoding="utf-8")
    (pkg / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "home.py").write_text(
        "import myapp\n"
        "class Home:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return myapp.VALUE + '|' + str(myapp.__file__)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(on_path))
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        value, origin = asgi_get(built[1], "/home").text.split("|", 1)
        assert value == "pkg"
        assert Path(origin).resolve() == (pkg / "__init__.py").resolve()
    finally:
        _purge_package("myapp")
        _drop_tree(tmp_path)


def test_idle_py_helper_from_another_folder_is_replaced(tmp_path, monkeypatch):
    """An idle ``helpers.py`` from another folder is not what this build serves.

    ``build()`` drops that module and loads this folder's file. A second
    build of the folder the helper came from reuses that module.
    """
    from ux_compose.build import build

    p1 = tmp_path / "P1" / "myapp"
    p2 = tmp_path / "P2" / "myapp"
    for folder, mark in ((p1, "FROM_P1"), (p2, "FROM_P2")):
        (folder / "routes").mkdir(parents=True)
        (folder / "__init__.py").write_text("", encoding="utf-8")
        (folder / "routes" / "__init__.py").write_text("", encoding="utf-8")
        (folder / "helpers.py").write_text(f"MARK = {mark!r}\n", encoding="utf-8")
        (folder / "routes" / "home.py").write_text(
            "from myapp.helpers import MARK\n"
            "class Home:\n"
            "    routes = ('get',)\n"
            "    def render(self):\n"
            "        return MARK\n",
            encoding="utf-8",
        )
    monkeypatch.syspath_prepend(str(p1.parent))
    try:
        _purge_package("myapp")
        importlib.invalidate_caches()
        preloaded = importlib.import_module("myapp.helpers")
        assert preloaded.MARK == "FROM_P1"
        built = build(p2, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/home").text == "FROM_P2"
        first = build(p1, name="X", host="asgi", live="null", level=1)
        assert asgi_get(first[1], "/home").text == "FROM_P1"
        helper = sys.modules["myapp.helpers"]
        assert helper.MARK == "FROM_P1"
        second = build(p1, name="X", host="asgi", live="null", level=1)
        assert asgi_get(second[1], "/home").text == "FROM_P1"
        assert sys.modules["myapp.helpers"] is helper
    finally:
        _purge_package("myapp")
        _drop_tree(tmp_path)


def test_pin_serves_a_py_submodule_while_the_parent_is_another_folder(
    tmp_path, monkeypatch
):
    """An uncached ``helpers.py`` comes from the pinned folder.

    The parent package is already loaded from somewhere else, so its
    ``__path__`` points there. The pin still has to serve this folder's
    file. A finder that only returns ``__init__.py`` serves the parent
    path instead. A helper already loaded from the pinned folder is the
    same module object on the next import.
    """
    from ux_compose.routing.core import pin_package_finder, unpin_package_finder

    p1 = tmp_path / "P1" / "myapp"
    p2 = tmp_path / "P2" / "myapp"
    for folder, mark in ((p1, "FROM_P1"), (p2, "FROM_P2")):
        folder.mkdir(parents=True)
        (folder / "__init__.py").write_text("", encoding="utf-8")
        (folder / "helpers.py").write_text(f"MARK = {mark!r}\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(p1.parent))
    finder = None
    try:
        _purge_package("myapp")
        importlib.invalidate_caches()
        parent = importlib.import_module("myapp")
        assert Path(parent.__file__).resolve() == (p1 / "__init__.py").resolve()
        finder = pin_package_finder(p2)
        loaded = importlib.import_module("myapp.helpers")
        assert loaded.MARK == "FROM_P2"
        assert Path(loaded.__file__).resolve() == (p2 / "helpers.py").resolve()
        assert importlib.import_module("myapp.helpers") is loaded
    finally:
        if finder is not None:
            unpin_package_finder(finder)
        _purge_package("myapp")
        _drop_tree(tmp_path)


def test_failed_route_exec_does_not_leave_the_module(tmp_path):
    """``import_route_module`` drops a module whose body raised.

    The name is inserted before exec. A failed exec has to pop it.
    ``discover`` is not involved, so nothing else removes the name.
    """
    from ux_compose.routing.core import import_route_module

    name = "boommod.routes.home"
    file = tmp_path / "home.py"
    file.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
    try:
        with pytest.raises(RuntimeError, match="boom"):
            import_route_module(name, file)
        assert name not in sys.modules
    finally:
        sys.modules.pop(name, None)


def _plain_off_path(root: Path, name: str) -> Path:
    return _write(
        root / name,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    id = 'hello'\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'hello'\n"
            ),
        },
    )


def test_off_path_first_build_does_not_log_component_replace(tmp_path, caplog):
    """Scan already registered the id. The dotted swap must not warn."""
    from ux_compose.build import build

    name = "quietapp"
    pkg = _plain_off_path(tmp_path, name)
    try:
        with caplog.at_level(logging.WARNING, logger="ux_behavior"):
            built = build(pkg, name="X", host="asgi", live="null", level=1)
        assert asgi_get(built[1], "/hello").text == "hello"
        assert "COMPONENT_REPLACE" not in caplog.text
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_scaffold_build_does_not_log_component_replace(tmp_path, caplog):
    """A fresh scaffold build logs no COMPONENT_REPLACE, the same as main."""
    from ux_compose.build import build
    from ux_compose.scaffold import create_app

    dest = create_app(tmp_path / "myapp", name="myapp", level=1)
    try:
        with caplog.at_level(logging.WARNING, logger="ux_behavior"):
            build(dest, name="X", host="asgi", live="null", level=1)
        assert "COMPONENT_REPLACE" not in caplog.text
    finally:
        _purge_package("myapp")
        _drop_tree(tmp_path)


def test_unit_registry_holds_the_dotted_route_instance(tmp_path):
    """The registry instance is the dotted module, not the scan copy."""
    from ux_compose.build import build

    name = "dotreg"
    pkg = _plain_off_path(tmp_path, name)
    try:
        built = build(pkg, name="X", host="asgi", live="null", level=1)
        inst = built[2].unit_registry["hello"]
        assert type(inst).__module__ == f"{name}.routes.hello"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_rebuild_does_not_rebind_an_unchanged_page(tmp_path):
    """A second build of the same file constructs the page once.

    The registry already holds the dotted class, so rebind leaves it.
    """
    from ux_compose.build import build

    name = "samepage"
    pkg = _plain_off_path(tmp_path, name)
    try:
        build(pkg, name="X", host="asgi", live="null", level=1)
        cls = sys.modules[f"{name}.routes.hello"].Hello
        calls = {"n": 0}
        original = cls.__init__

        def wrapped(self, *args, **kwargs):
            calls["n"] += 1
            original(self, *args, **kwargs)

        cls.__init__ = wrapped
        try:
            built = build(pkg, name="X", host="asgi", live="null", level=1)
            assert calls["n"] == 1
            assert type(built[2].unit_registry["hello"]) is cls
        finally:
            cls.__init__ = original
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_route_shell_without_path_is_dropped(tmp_path):
    """routes/__init__.py with no __path__ is a package shell, so release drops it.

    A helper would stay. Classifying that file as a route package is what
    drops it.
    """
    from ux_compose.routing.core import release_build_package_modules

    name = "shellapp"
    root = tmp_path / name
    init = root / "routes" / "__init__.py"
    init.parent.mkdir(parents=True)
    (root / "__init__.py").write_text("", encoding="utf-8")
    init.write_text("", encoding="utf-8")
    key = f"{name}.routes"
    mod = types.ModuleType(key)
    mod.__file__ = str(init.resolve())
    sys.modules[key] = mod
    try:
        release_build_package_modules(root, {})
        assert key not in sys.modules
    finally:
        sys.modules.pop(key, None)
        _purge_package(name)


def test_detached_loads_keep_distinct_module_keys(tmp_path):
    """Two detached files stay in sys.modules under different names."""
    from ux_compose.routing.core import load_detached_module

    left = tmp_path / "left.py"
    right = tmp_path / "right.py"
    left.write_text("MARK = 'LEFT'\n", encoding="utf-8")
    right.write_text("MARK = 'RIGHT'\n", encoding="utf-8")
    first = load_detached_module(left)
    second = load_detached_module(right)
    try:
        assert first.MARK == "LEFT"
        assert second.MARK == "RIGHT"
        assert first.__name__ != second.__name__
        assert sys.modules[first.__name__] is first
        assert sys.modules[second.__name__] is second
    finally:
        sys.modules.pop(first.__name__, None)
        sys.modules.pop(second.__name__, None)


def _lock_inversion_once(
    tmp_path, monkeypatch, *, tag: str, lock_timeout, env: str | None
) -> tuple[float, BaseException | None]:
    """Thread B's main.py calls build(). Thread A builds the other folder.

    A must not keep the name lock while it waits for that import. The
    hard limit is 2s even when the wait is ``None`` or the default 60s.
    """
    from ux_compose.build import build
    from ux_compose.routing.core import PackageImportConflict

    if env is None:
        monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
    else:
        monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", env)
    gate_name = f"invgate_{tag}"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = f"invapp_{tag}"
    folder_b = tmp_path / "b" / name
    folder_a = tmp_path / "a" / name
    _write(
        folder_b,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    id = 'hello'\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'FROM_B'\n"
            ),
        },
    )
    (folder_b / "main.py").write_text(
        f"import {gate_name}\n"
        "import time\n"
        "from pathlib import Path\n"
        "from ux_compose.build import build\n"
        f"{gate_name}.IN.set()\n"
        "time.sleep(0.2)\n"
        "build(\n"
        "    Path(__file__).resolve().parent,\n"
        "    name='B',\n"
        "    host='asgi',\n"
        "    live='null',\n"
        "    level=1,\n"
        ")\n",
        encoding="utf-8",
    )
    _write(
        folder_a,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    id = 'hello'\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'FROM_A'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(folder_b.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}
    # None waits without a bound. The sentinel omits the argument so the
    # environment, or the default 60s, is what build() uses.
    build_kwargs: dict[str, object] = {}
    if lock_timeout is not _UNSET_LOCK:
        build_kwargs["lock_timeout"] = lock_timeout

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    def builder() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(
                folder_a,
                name="A",
                host="asgi",
                live="null",
                level=1,
                **build_kwargs,
            )
            out["served"] = asgi_get(built[1], "/hello").text
        except BaseException as exc:
            out["err"] = exc

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=builder, daemon=True)
    limit = 2.0
    started = time.monotonic()
    deadline = started + limit
    try:
        left.start()
        right.start()
        left.join(max(0.0, deadline - time.monotonic()))
        right.join(max(0.0, deadline - time.monotonic()))
        elapsed = time.monotonic() - started
        assert elapsed < limit, f"still running after {elapsed:.2f}s"
        assert not left.is_alive() and not right.is_alive()
        err = out.get("err")
        assert isinstance(err, PackageImportConflict), out.get("served")
        assert err.loaded_from == folder_b.resolve()
        assert err.building == folder_a.resolve()
        assert out.get("served") != "FROM_B"
        return elapsed, err
    finally:
        _purge_package(name)
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


_UNSET_LOCK = object()


def test_lock_inversion_with_lock_timeout_none(tmp_path, monkeypatch):
    elapsed, _err = _lock_inversion_once(
        tmp_path, monkeypatch, tag="kw", lock_timeout=None, env=None
    )
    assert elapsed < 2.0


def test_lock_inversion_with_env_none(tmp_path, monkeypatch):
    elapsed, _err = _lock_inversion_once(
        tmp_path, monkeypatch, tag="env", lock_timeout=_UNSET_LOCK, env="none"
    )
    assert elapsed < 2.0


def test_lock_inversion_with_default_timeout(tmp_path, monkeypatch):
    elapsed, _err = _lock_inversion_once(
        tmp_path, monkeypatch, tag="def", lock_timeout=_UNSET_LOCK, env=None
    )
    assert elapsed < 2.0


def test_zero_lock_timeout_raises_before_the_import_wait(tmp_path, monkeypatch):
    """lock_timeout=0 is BuildLockTimeout, and the error's timeout is 0.

    The foreign import is still running. Returning from the deadline
    check would continue and serve a page. The configured timeout is 0,
    not a leftover 0.0 from the unset branch.
    """
    from ux_compose.build import BuildLockTimeout, build

    gate_name = "gate_zero_timeout"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nOUT = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    held = tmp_path / "held" / "myapp"
    other = tmp_path / "other" / "myapp"
    held.mkdir(parents=True)
    (held / "__init__.py").write_text("", encoding="utf-8")
    (held / "main.py").write_text(
        f"import {gate_name}\n"
        f"{gate_name}.IN.set()\n"
        f"{gate_name}.OUT.wait(5)\n"
        "VALUE = 'HELD'\n",
        encoding="utf-8",
    )
    _write(
        other,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OTHER'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(held.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module("myapp.main")
        except BaseException as exc:
            out["loader"] = exc

    def builder() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(
                other, name="X", host="asgi", live="null", level=1, lock_timeout=0
            )
            out["served"] = asgi_get(built[1], "/a").text
        except BaseException as exc:
            out["err"] = exc
        finally:
            gate.OUT.set()

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=builder, daemon=True)
    try:
        left.start()
        right.start()
        left.join(3)
        right.join(3)
        assert not left.is_alive() and not right.is_alive()
        err = out.get("err")
        assert isinstance(err, BuildLockTimeout), out.get("served")
        assert err.package == "myapp"
        assert err.timeout == 0
        assert "served" not in out
    finally:
        gate.OUT.set()
        _purge_package("myapp")
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def _thread_in_function(name: str) -> bool:
    for frame in sys._current_frames().values():
        while frame is not None:
            if frame.f_code.co_name == name:
                return True
            frame = frame.f_back
    return False


def test_second_import_past_the_budget_raises_build_lock_timeout(
    tmp_path, monkeypatch
):
    """The next foreign import starts as the first one releases, past the budget.

    That deadline check has to raise BuildLockTimeout. Returning from it
    continues, and a page can be served from the folder that is still importing.
    """
    import ux_compose.routing.core as routing_core
    from ux_compose.build import BuildLockTimeout, build

    class _Clock:
        now = 0.0

        def __call__(self) -> float:
            return self.now

    clock = _Clock()
    monkeypatch.setattr(routing_core.time, "monotonic", clock)
    real_wait = routing_core._wait_for_import_or_name_lock
    gate_name = "gate_second_import"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\n"
        "IN = threading.Event()\n"
        "RELEASE = threading.Event()\n"
        "START_SECOND = threading.Event()\n"
        "SECOND_HELD = threading.Event()\n"
        "OUT = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    gate = importlib.import_module(gate_name)

    def _wait_then_second_import(names, lock, timeout):
        result = real_wait(names, lock, timeout)
        if result is None and not gate.START_SECOND.is_set():
            gate.START_SECOND.set()
            assert gate.SECOND_HELD.wait(2)
            clock.now += 10
        return result

    monkeypatch.setattr(
        routing_core, "_wait_for_import_or_name_lock", _wait_then_second_import
    )
    held = tmp_path / "held" / "myapp"
    other = tmp_path / "other" / "myapp"
    held.mkdir(parents=True)
    (held / "__init__.py").write_text("", encoding="utf-8")
    (held / "first.py").write_text(
        f"import {gate_name}\n"
        f"{gate_name}.IN.set()\n"
        f"{gate_name}.RELEASE.wait(5)\n",
        encoding="utf-8",
    )
    (held / "second.py").write_text(
        f"import {gate_name}\n"
        f"{gate_name}.SECOND_HELD.set()\n"
        f"{gate_name}.OUT.wait(5)\n"
        "VALUE = 'SECOND'\n",
        encoding="utf-8",
    )
    _write(
        other,
        {
            "routes/a.py": (
                "class A:\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OTHER'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(held.parent))
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module("myapp.first")
        except BaseException as exc:
            out["loader"] = exc

    def second() -> None:
        assert gate.START_SECOND.wait(5)
        try:
            importlib.import_module("myapp.second")
        except BaseException as exc:
            out["second"] = exc
            gate.SECOND_HELD.set()

    def builder() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(
                other, name="X", host="asgi", live="null", level=1, lock_timeout=0.2
            )
            out["served"] = asgi_get(built[1], "/a").text
        except BaseException as exc:
            out["err"] = exc

    left = threading.Thread(target=loader, daemon=True)
    mid = threading.Thread(target=second, daemon=True)
    right = threading.Thread(target=builder, daemon=True)
    try:
        mid.start()
        left.start()
        right.start()
        assert gate.IN.wait(2)
        found = False
        for _ in range(200):
            if _thread_in_function("_wait_for_import_or_name_lock"):
                found = True
                break
            time.sleep(0.01)
        assert found, "build never waited for the first import"
        gate.RELEASE.set()
        right.join(3)
        left.join(3)
        assert not right.is_alive()
        err = out.get("err")
        assert isinstance(err, BuildLockTimeout), out.get("served") or out.get("second")
        assert err.package == "myapp"
        assert "served" not in out
        assert "second" not in out
    finally:
        gate.OUT.set()
        gate.RELEASE.set()
        gate.START_SECOND.set()
        _purge_package("myapp")
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def test_build_does_not_wait_for_this_threads_import_lock(tmp_path, monkeypatch):
    """A lock this thread holds is not another importer.

    The foreign helper is already in sys.modules and this thread holds
    its import lock. build() serves this folder. Counting that owner
    waits for a lock this thread will not release, and the short timeout
    becomes BuildLockTimeout instead of this folder's page.
    """
    import importlib._bootstrap as bootstrap

    from ux_compose.build import build

    name = "ownlockapp"
    folder_b = tmp_path / "b" / name
    folder_a = tmp_path / "a" / name
    for folder, mark in ((folder_b, "FROM_B"), (folder_a, "FROM_A")):
        (folder / "routes").mkdir(parents=True)
        (folder / "__init__.py").write_text("", encoding="utf-8")
        (folder / "routes" / "__init__.py").write_text("", encoding="utf-8")
        (folder / "helpers.py").write_text(f"MARK = {mark!r}\n", encoding="utf-8")
        (folder / "routes" / "home.py").write_text(
            f"from {name}.helpers import MARK\n"
            "class Home:\n"
            "    routes = ('get',)\n"
            "    def render(self):\n"
            "        return MARK\n",
            encoding="utf-8",
        )
    monkeypatch.syspath_prepend(str(folder_b.parent))
    lock = None
    try:
        _purge_package(name)
        importlib.invalidate_caches()
        importlib.import_module(f"{name}.helpers")
        lock = bootstrap._get_module_lock(f"{name}.helpers")
        lock.acquire()
        built = build(
            folder_a, name="X", host="asgi", live="null", level=1, lock_timeout=0.4
        )
        assert asgi_get(built[1], "/home").text == "FROM_A"
    finally:
        if lock is not None and getattr(lock, "owner", None) is not None:
            lock.release()
        _purge_package(name)
        _drop_tree(tmp_path)


def test_snapshot_package_modules_waits_for_the_import_lock():
    """snapshot_package_modules does not read sys.modules unlocked.

    Another thread holding package_import_lock blocks the snapshot until
    that thread releases it.
    """
    from ux_compose.routing.core import package_import_lock, snapshot_package_modules

    release = threading.Event()
    held = threading.Event()
    done = threading.Event()

    def holder() -> None:
        package_import_lock.acquire()
        try:
            held.set()
            release.wait(5)
        finally:
            package_import_lock.release()

    def worker() -> None:
        snapshot_package_modules(Path("/tmp/ux-compose-snapshot-probe"))
        done.set()

    owner = threading.Thread(target=holder, daemon=True)
    other = threading.Thread(target=worker, daemon=True)
    owner.start()
    assert held.wait(2)
    other.start()
    try:
        assert not done.wait(0.3)
        release.set()
        assert done.wait(2)
        owner.join(2)
        other.join(2)
        assert not owner.is_alive() and not other.is_alive()
    finally:
        release.set()


def test_behavior_and_registry_are_one_dotted_instance(tmp_path):
    """The behavior map and the unit registry hold the same instance.

    Main keeps one object, and its class is the dotted route module.
    Leaving the scan instance in the behavior map splits them.
    """
    from ux_compose.build import build

    name = "sameobj"
    pkg = _plain_off_path(tmp_path, name)
    try:
        app, _asgi, bundle = build(pkg, name="X", host="asgi", live="null", level=1)
        behavior = app._behavior.get("hello")
        registered = bundle.unit_registry["hello"]
        assert behavior is registered
        assert type(behavior).__module__ == f"{name}.routes.hello"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_plain_page_keeps_the_app_behavior(tmp_path):
    """A page class with no bind_behavior still points at the app behavior.

    Rebind builds a new instance. That instance's behavior is the app's.
    """
    from ux_compose.build import build

    name = "plainbeh"
    pkg = _plain_off_path(tmp_path, name)
    try:
        app, _asgi, _bundle = build(pkg, name="X", host="asgi", live="null", level=1)
        page = app._behavior._components["hello"]
        assert page._behavior is app._behavior
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


@pytest.mark.parametrize("env", [None, "none", "inf", "2"])
@pytest.mark.parametrize("entry", ["mount", "discover"])
def test_mount_and_discover_wait_out_a_short_foreign_import(
    tmp_path, monkeypatch, env: str | None, entry: str
):
    """App.mount and DirectoryRoutes.discover wait out a short import.

    Neither call is build(), so the wait is the environment. Unset, none,
    inf, and a real number of seconds all let a short import finish.
    """
    from ux_compose.app import App
    from ux_compose.routing.core import DirectoryRoutes

    if env is None:
        monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
        label = "unset"
    else:
        monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", env)
        label = "neg" if env == "-1" else env.replace(".", "p")
    gate_name = f"gate_{entry}_{label}"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = f"w{entry[:1]}{label}"
    folder_b = tmp_path / "b" / name
    folder_a = tmp_path / "a" / name
    folder_b.mkdir(parents=True)
    (folder_b / "__init__.py").write_text("", encoding="utf-8")
    (folder_b / "main.py").write_text(
        f"import {gate_name}\n"
        "import time\n"
        f"{gate_name}.IN.set()\n"
        "time.sleep(0.2)\n"
        "VALUE = 'B'\n",
        encoding="utf-8",
    )
    _write(
        folder_a,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    id = 'hello'\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OURS'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(folder_b.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    left = threading.Thread(target=loader, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        if entry == "mount":
            bundle = App().mount(folder_a)
            assert bundle.unit_registry["hello"].render() == "OURS"
        elif entry == "discover":
            records = DirectoryRoutes(folder_a).discover()
            assert records[0].page_cls().render() == "OURS"
        else:
            raise AssertionError(entry)
        left.join(2)
        assert not left.is_alive()
        assert out.get("loader") is None
    finally:
        left.join(2)
        _purge_package(name)
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


@pytest.mark.parametrize("entry", ["mount", "discover"])
def test_mount_and_discover_timeout_names_the_env_budget(
    tmp_path, monkeypatch, entry: str
):
    """A short environment budget is the BuildLockTimeout value.

    App.mount and DirectoryRoutes.discover read the environment, not a
    build() argument. The import is still held. The error names 0.05s.
    """
    from ux_compose.app import App
    from ux_compose.routing.core import BuildLockTimeout, DirectoryRoutes

    monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", "0.05")
    gate_name = f"gate_budget_{entry}"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nOUT = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = f"budget{entry[:1]}"
    folder_b = tmp_path / "b" / name
    folder_a = tmp_path / "a" / name
    folder_b.mkdir(parents=True)
    (folder_b / "__init__.py").write_text("", encoding="utf-8")
    (folder_b / "main.py").write_text(
        f"import {gate_name}\n"
        f"{gate_name}.IN.set()\n"
        f"{gate_name}.OUT.wait(5)\n"
        "VALUE = 'B'\n",
        encoding="utf-8",
    )
    _write(
        folder_a,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    id = 'hello'\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OURS'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(folder_b.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    left = threading.Thread(target=loader, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        with pytest.raises(BuildLockTimeout) as caught:
            if entry == "mount":
                App().mount(folder_a)
            elif entry == "discover":
                DirectoryRoutes(folder_a).discover()
            else:
                raise AssertionError(entry)
        assert caught.value.package == name
        assert caught.value.timeout == 0.05
        assert out.get("loader") is None
    finally:
        gate.OUT.set()
        left.join(2)
        _purge_package(name)
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


@pytest.mark.parametrize("entry", ["mount", "discover"])
def test_direct_call_default_wait_exceeds_one_second(tmp_path, monkeypatch, entry: str):
    """Unset UX_COMPOSE_BUILD_LOCK_TIMEOUT waits longer than one second.

    App.mount and DirectoryRoutes.discover are not build(), so they use
    that default. An import that holds for just over a second still
    finishes. A one-second default raises BuildLockTimeout instead.
    """
    from ux_compose.app import App
    from ux_compose.routing.core import DirectoryRoutes

    monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
    gate_name = f"gate_long_{entry}"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = f"long{entry[:1]}"
    folder_b = tmp_path / "b" / name
    folder_a = tmp_path / "a" / name
    folder_b.mkdir(parents=True)
    (folder_b / "__init__.py").write_text("", encoding="utf-8")
    (folder_b / "main.py").write_text(
        f"import {gate_name}\n"
        "import time\n"
        f"{gate_name}.IN.set()\n"
        "time.sleep(1.3)\n"
        "VALUE = 'B'\n",
        encoding="utf-8",
    )
    _write(
        folder_a,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    id = 'hello'\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OURS'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(folder_b.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    left = threading.Thread(target=loader, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        if entry == "mount":
            bundle = App().mount(folder_a)
            assert bundle.unit_registry["hello"].render() == "OURS"
        elif entry == "discover":
            records = DirectoryRoutes(folder_a).discover()
            assert records[0].page_cls().render() == "OURS"
        else:
            raise AssertionError(entry)
        left.join(3)
        assert not left.is_alive()
        assert out.get("loader") is None
    finally:
        left.join(3)
        _purge_package(name)
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def test_build_timeout_does_not_stick_for_a_later_mount(tmp_path, monkeypatch):
    """A finished build() does not leave its timeout on this thread.

    The next App.mount is not build(), so a leaked lock_timeout would
    bound that mount. A short import after build(lock_timeout=0.05)
    still finishes.
    """
    from ux_compose.app import App
    from ux_compose.build import build

    monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
    name = "stickapp"
    quiet = _plain_off_path(tmp_path / "quiet", name)
    try:
        build(quiet, name="X", host="asgi", live="null", level=1, lock_timeout=0.05)
    finally:
        _purge_package(name)
    gate_name = "gate_stick"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    folder_b = tmp_path / "b" / name
    folder_a = tmp_path / "a" / name
    folder_b.mkdir(parents=True)
    (folder_b / "__init__.py").write_text("", encoding="utf-8")
    (folder_b / "main.py").write_text(
        f"import {gate_name}\n"
        "import time\n"
        f"{gate_name}.IN.set()\n"
        "time.sleep(0.4)\n"
        "VALUE = 'B'\n",
        encoding="utf-8",
    )
    _write(
        folder_a,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    id = 'hello'\n"
                "    routes = ('get',)\n"
                "    def render(self):\n"
                "        return 'OURS'\n"
            ),
        },
    )
    monkeypatch.syspath_prepend(str(folder_b.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    left = threading.Thread(target=loader, daemon=True)
    try:
        left.start()
        assert gate.IN.wait(2)
        bundle = App().mount(folder_a)
        assert bundle.unit_registry["hello"].render() == "OURS"
        left.join(2)
        assert not left.is_alive()
        assert out.get("loader") is None
    finally:
        left.join(2)
        _purge_package(name)
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def test_in_use_package_both_folders_ship_is_a_conflict(tmp_path, monkeypatch):
    """A package both folders ship is PackageImportConflict while it is importing.

    ``plugins/__init__.py`` is that module. A check that only sees
    ``plugins.py`` misses it and can serve the other folder's copy.
    """
    from ux_compose.build import build
    from ux_compose.routing.core import PackageImportConflict

    gate_name = "gate_plugins"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = "plugapp"
    p1 = tmp_path / "p1" / name
    p2 = tmp_path / "p2" / name
    for folder, mark in ((p1, "FROM_P1"), (p2, "FROM_P2")):
        (folder / "plugins").mkdir(parents=True)
        (folder / "__init__.py").write_text("", encoding="utf-8")
        (folder / "routes").mkdir()
        (folder / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (p1 / "plugins" / "__init__.py").write_text(
        f"import {gate_name}\n"
        "import time\n"
        "MARK = 'FROM_P1'\n"
        f"{gate_name}.IN.set()\n"
        "time.sleep(0.2)\n",
        encoding="utf-8",
    )
    (p2 / "plugins" / "__init__.py").write_text(
        "MARK = 'FROM_P2'\n",
        encoding="utf-8",
    )
    (p2 / "routes" / "home.py").write_text(
        f"from {name}.plugins import MARK\n"
        "class Home:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return MARK\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(p1.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.plugins")
        except BaseException as exc:
            out["loader"] = exc

    def builder() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(p2, name="X", host="asgi", live="null", level=1)
            out["served"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=builder, daemon=True)
    try:
        left.start()
        right.start()
        left.join(4)
        right.join(4)
        assert not left.is_alive() and not right.is_alive()
        err = out.get("err")
        assert isinstance(err, PackageImportConflict), out.get("served")
        assert err.loaded_from == p1.resolve()
        assert err.building == p2.resolve()
        assert out.get("served") != "FROM_P1"
    finally:
        _purge_package(name)
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)


def test_deep_module_only_the_other_folder_ships_is_not_a_conflict(
    tmp_path, monkeypatch
):
    """A deep module this folder does not ship is not a conflict.

    This folder has the top package ``extra`` and not ``extra/nested/leaf.py``.
    The other folder is importing that leaf. build() serves this folder.
    Treating the top segment as the whole module raises PackageImportConflict.
    """
    from ux_compose.build import build

    gate_name = "gate_leaf"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = "leafapp"
    p1 = tmp_path / "p1" / name
    p2 = tmp_path / "p2" / name
    leaf = p1 / "extra" / "nested"
    leaf.mkdir(parents=True)
    (p1 / "__init__.py").write_text("", encoding="utf-8")
    (p1 / "extra" / "__init__.py").write_text("", encoding="utf-8")
    (p1 / "extra" / "nested" / "__init__.py").write_text("", encoding="utf-8")
    (leaf / "leaf.py").write_text(
        f"import {gate_name}\n"
        "import time\n"
        f"{gate_name}.IN.set()\n"
        "time.sleep(0.2)\n"
        "MARK = 'LEAF'\n",
        encoding="utf-8",
    )
    (p2 / "extra").mkdir(parents=True)
    (p2 / "__init__.py").write_text("", encoding="utf-8")
    (p2 / "extra" / "__init__.py").write_text("MARK = 'TOP'\n", encoding="utf-8")
    (p2 / "routes").mkdir()
    (p2 / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (p2 / "routes" / "home.py").write_text(
        "class Home:\n"
        "    routes = ('get',)\n"
        "    def render(self):\n"
        "        return 'OURS'\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(p1.parent))
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.extra.nested.leaf")
        except BaseException as exc:
            out["loader"] = exc

    def builder() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(p2, name="X", host="asgi", live="null", level=1)
            out["served"] = asgi_get(built[1], "/home").text
        except BaseException as exc:
            out["err"] = exc

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=builder, daemon=True)
    try:
        left.start()
        right.start()
        left.join(4)
        right.join(4)
        assert not left.is_alive() and not right.is_alive()
        assert out.get("loader") is None, out.get("loader")
        assert "err" not in out, out.get("err")
        assert out.get("served") == "OURS"
    finally:
        _purge_package(name)
        sys.modules.pop(gate_name, None)
        _drop_tree(tmp_path)
