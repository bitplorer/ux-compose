"""Two folders of one package name, each with its own component HTML.

B's main.py calls build() while A is building, and the swapped order.
The build already in progress raises PackageImportConflict and does not
serve the other folder. On main c22e419 that build serves the other
folder's component HTML and reports the other folder as the source.
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


def _write_app(root: Path, name: str, marker: str, *, calls_build: bool, gate: str) -> None:
    (root / "components").mkdir(parents=True)
    (root / "routes").mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "components" / "__init__.py").write_text("", encoding="utf-8")
    (root / "routes" / "__init__.py").write_text("", encoding="utf-8")
    (root / "components" / "badge.py").write_text(
        f'HTML = "<p>{marker}</p>"\n',
        encoding="utf-8",
    )
    (root / "routes" / "home.py").write_text(
        textwrap.dedent(
            f"""\
            from {name}.components.badge import HTML
            class Home:
                id = 'home'
                routes = ('get',)
                def render(self):
                    return HTML
            """
        ),
        encoding="utf-8",
    )
    if calls_build:
        (root / "main.py").write_text(
            textwrap.dedent(
                f"""\
                import {gate}
                from pathlib import Path
                from ux_compose.build import build
                {gate}.IN.set()
                import time
                time.sleep(0.2)
                try:
                    {gate}.RESULT = build(
                        Path(__file__).resolve().parent,
                        name='Nested',
                        host='asgi',
                        live='null',
                        level=1,
                    )
                    {gate}.ERR = None
                except BaseException as exc:
                    {gate}.ERR = exc
                """
            ),
            encoding="utf-8",
        )
        return
    (root / "main.py").write_text(f"MARKER = {marker!r}\n", encoding="utf-8")


def _purge(name: str) -> None:
    for key in list(sys.modules):
        if key == name or key.startswith(name + "."):
            sys.modules.pop(key, None)


def _page_source(bundle, name: str) -> str:
    for surface in bundle.surfaces.values():
        if surface.id == "home":
            return str(surface.source_file)
    page = bundle.unit_registry["home"]
    mod = sys.modules.get(type(page).__module__)
    return str(getattr(mod, "__file__", ""))


@pytest.mark.parametrize("env", ["none", "unset"])
@pytest.mark.parametrize("first", ["a", "b"])
def test_mixed_folders_do_not_serve_the_other_components(
    tmp_path, monkeypatch, env: str, first: str
):
    """The in-progress build keeps its own folder.

    ``first`` is the folder whose build() starts while the other folder's
    main.py is about to call build(). That in-progress build raises
    PackageImportConflict, names its own folder as ``building``, and does
    not serve the other component. The build() inside main.py serves that
    folder's own HTML from that folder's source file. Both finish inside 2s.
    """
    from ux_compose.build import build

    if env == "unset":
        monkeypatch.delenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", raising=False)
    else:
        monkeypatch.setenv("UX_COMPOSE_BUILD_LOCK_TIMEOUT", env)
    gate_name = f"gate_mix_{first}_{env}"
    (tmp_path / f"{gate_name}.py").write_text(
        "import threading\nIN = threading.Event()\nRESULT = None\nERR = None\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    name = f"mix{first}{env}"
    folder_a = tmp_path / "a" / name
    folder_b = tmp_path / "b" / name
    _write_app(
        folder_a,
        name,
        "MARK_A",
        calls_build=first == "b",
        gate=gate_name,
    )
    _write_app(
        folder_b,
        name,
        "MARK_B",
        calls_build=first == "a",
        gate=gate_name,
    )
    outer = folder_a if first == "a" else folder_b
    nested = folder_b if first == "a" else folder_a
    own = "MARK_A" if first == "a" else "MARK_B"
    other = "MARK_B" if first == "a" else "MARK_A"
    monkeypatch.syspath_prepend(str(nested.parent))
    importlib.invalidate_caches()
    gate = importlib.import_module(gate_name)
    out: dict[str, object] = {}

    def loader() -> None:
        try:
            importlib.import_module(f"{name}.main")
        except BaseException as exc:
            out["loader"] = exc

    def builder() -> None:
        assert gate.IN.wait(2)
        try:
            built = build(outer, name="Outer", host="asgi", live="null", level=1)
            out["text"] = asgi_get(built[1], "/home").text
            out["source"] = _page_source(built[2], name)
        except BaseException as exc:
            out["err"] = exc

    left = threading.Thread(target=loader, daemon=True)
    right = threading.Thread(target=builder, daemon=True)
    limit = 2.0
    started = time.monotonic()
    try:
        left.start()
        right.start()
        left.join(limit)
        right.join(max(0.0, started + limit - time.monotonic()))
        elapsed = time.monotonic() - started
        assert elapsed < limit, f"still running after {elapsed:.2f}s"
        assert not left.is_alive() and not right.is_alive()
        assert out.get("loader") is None, out.get("loader")

        text = out.get("text")
        if text is not None:
            assert own in str(text) and other not in str(text), text
            source = Path(str(out.get("source"))).resolve()
            assert source.is_relative_to(outer.resolve()), source
        else:
            err = out.get("err")
            assert type(err).__name__ == "PackageImportConflict", err
            assert err.building == outer.resolve()
            assert err.loaded_from == nested.resolve()

        assert gate.ERR is None, gate.ERR
        nested_built = gate.RESULT
        nested_text = asgi_get(nested_built[1], "/home").text
        nested_source = Path(_page_source(nested_built[2], name)).resolve()
        nested_marker = "MARK_B" if first == "a" else "MARK_A"
        foreign_marker = own
        assert nested_marker in nested_text and foreign_marker not in nested_text
        assert nested_source.is_relative_to(nested.resolve()), nested_source
        if first == "b":
            assert "MARK_A" in nested_text and "MARK_B" not in nested_text
            assert nested_source.is_relative_to(folder_a.resolve())
        else:
            assert err.building == folder_a.resolve()
    finally:
        _purge(name)
        sys.modules.pop(gate_name, None)
