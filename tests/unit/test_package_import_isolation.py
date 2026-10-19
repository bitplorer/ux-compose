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

    Thread A holds the package import lock while its route imports
    shared_mod. Joins are timed so a deadlock fails the test.
    """
    from starlette.testclient import TestClient

    from ux_compose.build import build

    root = tmp_path
    probe: dict[str, str] = {}

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

    inner = mk("p2", {"routes/b.py": route("B", "'<p>b</p>'")}, name="other")
    (root / "shared_mod.py").write_text(
        "import time\n"
        "time.sleep(0.5)\n"
        "from pathlib import Path\n"
        "from ux_compose.build import build\n"
        f"build(Path({str(inner)!r}), name='S', host='asgi', live='null', level=1)\n"
        "X = 1\n",
        encoding="utf-8",
    )
    outer = mk(
        "p1",
        {
            "routes/a.py": "import time\ntime.sleep(0.2)\nimport shared_mod\n"
            + route("A", "'<p>a</p>'"),
        },
    )
    monkeypatch.syspath_prepend(str(root))

    def import_shared() -> None:
        importlib.import_module("shared_mod")

    def build_outer() -> None:
        probe["body"] = get(outer, "/a")

    try:
        importer = threading.Thread(target=import_shared, daemon=True)
        builder = threading.Thread(target=build_outer, daemon=True)
        importer.start()
        time.sleep(0.05)
        builder.start()
        builder.join(15)
        importer.join(1)
        assert not builder.is_alive() and not importer.is_alive()
        assert probe["body"].startswith("200:")
        assert "<p>a</p>" in probe["body"]
    finally:
        _drop_tree(root)
        for key in list(sys.modules):
            if key in {"shared_mod", "myapp", "other"} or key.startswith(
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


def test_repeated_builds_do_not_grow_sys_modules(tmp_path):
    """One folder stays flat. A new folder may add its modules once."""
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
            built = build(pkg, name="N", host="asgi", live="null", level=1)
            assert asgi_get(built[1], "/hello").text == f"n{index}"
            after = len(sys.modules)
            built = build(pkg, name="N", host="asgi", live="null", level=1)
            assert len(sys.modules) == after
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
        f"        build(Path({str(inner)!r}), name='B2', host='fastapi', live='null', level=1)\n"
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


def test_type_hints_survive_build_on_and_off_path(tmp_path):
    """Future annotations resolve after build, whether or not the folder is on sys.path."""
    from starlette.testclient import TestClient

    from ux_compose.build import build

    for label, on_path in (("off", False), ("on", True)):
        name = f"hint{label}"
        counter = tmp_path / f"{name}-runs.txt"
        counter.write_text("", encoding="utf-8")
        pkg = _hints_package(tmp_path / label, name, counter)
        if on_path:
            sys.path.insert(0, str(pkg.parent))
        try:
            _app, asgi, _bundle = build(pkg, name="X", host="asgi", live="null", level=1)
            response = TestClient(asgi).get("/h")
            assert response.status_code == 200, response.text
            assert "M" in response.text
        finally:
            if on_path:
                sys.path.remove(str(pkg.parent))
            _purge_package(name)
            _drop_tree(tmp_path)


def test_route_file_runs_once_over_three_builds(tmp_path):
    from ux_compose.build import build

    name = "onceapp"
    counter = tmp_path / "once-runs.txt"
    counter.write_text("", encoding="utf-8")
    pkg = _hints_package(tmp_path, name, counter)
    try:
        for _ in range(3):
            build(pkg, name="X", host="asgi", live="null", level=1)
        assert counter.read_text(encoding="utf-8") == "x"
    finally:
        _purge_package(name)
        _drop_tree(tmp_path)


def test_import_after_build_is_the_served_module(tmp_path):
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
