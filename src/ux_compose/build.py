"""Composition root — one place to set host + live plane.

::

    from ux_compose.build import build
    from document import document

    app, asgi, bundle = build(
        Path(__file__).parent,
        name="Shop",
        host="auto",   # auto|fastapi|asgi
        live="auto",   # auto|channel|null
        level="auto",
        document=document,
        wrap=document,
        cek="require",  # product Cap Host after use_channel
    )

Orchestra only: host.open → L1 boot → document → channel on asgi →
App.mount (catalog scan, bind_pages=False) → DirectoryRoutes.discover
(HTTP path law) → host.bind. Two walkers, one product door. Path law
and HTML wrap live elsewhere.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ux_compose.routing.core import (
    BuildLockTimeout,
    begin_build_import_wait,
    end_build_import_wait,
    lock_timeout_from_env,
    parse_lock_timeout,
)

__all__ = ["BuildLockTimeout", "build", "BuildResult"]

_UNSET = object()


def _rebind_detached_pages(app: Any, registry: dict, bundle: Any, records: list) -> None:
    """Dispatch and GET use the dotted route class, not the scan copy.

    Scan already registered this id in this build. The path-unique module
    is dropped when the build ends, so the dotted instance has to take
    its place. That swap is bookkeeping: it must not go through
    ``behavior.add``, which logs COMPONENT_REPLACE. A page whose registry
    instance is already the dotted class is left as it is.
    """
    behavior = getattr(app, "_behavior", None)
    if behavior is None:
        return
    components = getattr(behavior, "_components", None)
    if not isinstance(components, dict):
        return
    for rec in records:
        page_cls = getattr(rec, "page_cls", None)
        if not isinstance(page_cls, type):
            continue
        sid = str(getattr(page_cls, "id", None) or page_cls.__name__.lower())
        inst = registry.get(sid)
        if inst is None:
            continue
        inst_mod = str(getattr(type(inst), "__module__", ""))
        page_mod = str(getattr(page_cls, "__module__", ""))
        if inst_mod == page_mod or not inst_mod.startswith("ux_surface_"):
            continue
        replacement = page_cls()
        bind = getattr(replacement, "bind_behavior", None)
        if callable(bind):
            bind(behavior)
        else:
            setattr(replacement, "_behavior", behavior)
        components[sid] = replacement
        registry[sid] = replacement
        unit_registry = getattr(bundle, "unit_registry", None)
        if isinstance(unit_registry, dict):
            unit_registry[sid] = replacement


def _resolve_lock_timeout(lock_timeout: Any) -> float | None:
    """None waits until the other build finishes. Omitted reads the env, else 60."""
    if lock_timeout is _UNSET:
        return lock_timeout_from_env()
    return parse_lock_timeout(lock_timeout, where="UX_COMPOSE_BUILD_LOCK_TIMEOUT")


def _const_bool(node: ast.AST) -> bool | None:
    if isinstance(node, ast.Constant):
        return bool(node.value)
    return None


def _settings_openapi(package_dir: Path) -> bool | None:
    """Read ``OPENAPI = True/False`` from ``settings.py`` without importing it."""
    path = package_dir / "settings.py"
    if not path.is_file():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "OPENAPI":
                    flag = _const_bool(node.value)
                    if flag is not None:
                        return flag
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "OPENAPI" and node.value is not None:
                flag = _const_bool(node.value)
                if flag is not None:
                    return flag
    return None


class BuildResult(tuple):
    """(compose_app, asgi_app, bundle) with named attributes."""

    @property
    def app(self):
        return self[0]

    @property
    def asgi(self):
        return self[1]

    @property
    def bundle(self):
        return self[2]


def _attach_document(app: Any, document: Any, *, use_htmx: bool) -> Any:
    """Attach the author's Document, or synthesize one if none given.

    Author-provided Document is the SSoT. HTMX stays opt-in.
    Missing ux-dom fails loud (hard dependency, Python ≥3.14).
    """
    try:
        if document is not None:
            if use_htmx:
                from ux_compose.htmx import Htmx

                document.use(Htmx())
            app.use_dom(document)
            return document
        from ux_dom import Csp, Document, XElement

        runtimes: list[Any] = [XElement(), Csp.auto()]
        if use_htmx:
            from ux_compose.htmx import Htmx

            runtimes.insert(1, Htmx())
        document = Document(head=[], body=[], ensure_csrf_token=False).use(*runtimes)
        app.use_dom(document, author=False)
        return document
    except ImportError as exc:
        raise ImportError(
            "ux-dom is required (Python ≥3.14). "
            "ux-compose hard-depends on the pinned specialist stack. "
            "Pass build(document=) with an author Document."
        ) from exc


def build(
    package_dir: str | Path,
    *,
    name: str = "App",
    host: str = "auto",
    live: str = "auto",
    level: int | str = "auto",
    base: str = "routes",
    fail_closed: bool = True,
    use_htmx: bool = False,
    asgi_app: Any = None,
    document: Any = None,
    wrap: Any = _UNSET,
    cek: str = "require",
    openapi: Any = _UNSET,
    strict_caps: bool = True,
    lock_timeout: Any = _UNSET,
) -> BuildResult:
    """Boot specialists + mount page units. Host and live set only here.

    wrap:
      Author GET shell. Defaults to ``document`` (Document SSoT).
      ``wrap=None`` is a bare fragment. Never a synthesized Document
      (string fragment → script src).

    use_htmx:
      Attach :class:`ux_compose.htmx.Htmx` (pinned htmx scripts with SRI).
      A page GET with ``HX-Request: true`` that is not a history restore
      gets the fragment, not the Document shell; HTML page responses send
      ``Vary: HX-Request``.

    openapi:
      FastAPI Swagger / ReDoc / ``/openapi.json``. Default off so
      ``routes/docs.py`` can own GET ``/docs``. ``True`` opts in.
      When omitted, ``settings.OPENAPI`` is honoured if present.

    host:
      - ``"auto"`` — FastAPI if importable, else DirectoryASGI
      - ``"fastapi"`` — FastAPI + page binder (preferred)
      - ``"asgi"`` — DirectoryASGI (no FastAPI)

    live:
      - ``"auto"`` — Channel when ux_channel importable
      - ``"channel"`` — prefer Channel
      - ``"null"`` — offline Behavior only

    cek:
      - ``"require"`` — product Cap Host (cek-runtime via ``App.use_cek``).
        Default. Skipped when ``live="null"`` or Channel did not attach.
        Cap Host ≠ HTTP Product host (ADR 0002).
      - ``"adapt"`` — compare-only lab
      - ``"off"`` — do not attach Cap Host (honest off; see ``App.use_cek``)

    lock_timeout:
      Seconds to wait while another thread is importing this package name.
      Omitted reads ``UX_COMPOSE_BUILD_LOCK_TIMEOUT``, otherwise 60.
      A blank string is that same default. ``0`` tries once and raises
      ``BuildLockTimeout`` without waiting. ``None``, ``none``, and
      ``inf`` (any case) wait until the other import ends. A negative
      number, ``nan``, or any other bad value raises ``ValueError``.
      The message names ``UX_COMPOSE_BUILD_LOCK_TIMEOUT``. ``-1`` does
      not wait forever. ``App.mount`` and ``DirectoryRoutes.discover``
      use this same parser.
    """
    from ux_compose import App
    from ux_compose.routing.core import DirectoryRoutes, RouterHooks
    from ux_compose.routing.core import begin_build_module_notes, end_build_module_notes
    from ux_compose.routing.core import isolate_package_imports, package_build_lock
    from ux_compose.routing.core import pin_package_finder, unpin_package_finder
    from ux_compose.routing.core import (
        release_build_package_modules,
        snapshot_package_modules,
    )
    from ux_compose.routing.host import KIND_FASTAPI, bind as host_bind
    from ux_compose.routing.host import open as host_open

    package_dir = Path(package_dir).resolve()
    host_l = (host or "auto").lower()
    live_l = (live or "auto").lower()

    want_channel = live_l in ("auto", "channel")
    if live_l == "null":
        want_channel = False

    auto_level = isinstance(level, str) and str(level).lower() == "auto"
    # Boot is L1. Channel/Motion attach below, after the process exists.
    boot_level: int | str = 1 if auto_level else min(int(level), 1)

    if openapi is _UNSET:
        settings_flag = _settings_openapi(package_dir)
        openapi_flag = bool(settings_flag) if settings_flag is not None else False
    else:
        openapi_flag = bool(openapi)

    asgi, kind = host_open(
        name=name, host=host_l, asgi_app=asgi_app, openapi=openapi_flag
    )

    app = App.boot(name, strict_caps=strict_caps, level=boot_level)
    author_document = document
    author_wrap = author_document if wrap is _UNSET else wrap
    document = _attach_document(app, author_document, use_htmx=use_htmx)
    partial = None
    if use_htmx:
        from ux_compose.htmx import is_partial

        partial = is_partial

    if want_channel and kind == KIND_FASTAPI and asgi is not None:
        # strict_attach lives on the wire attach. A failure raises there.
        app.use_channel(asgi_app=asgi)
    elif want_channel:
        try:
            app.use_channel()
        except ImportError:
            raise
        except Exception:
            if live_l == "channel":
                raise

    # Product Cap Host: App door → Channel → CekHostCapService → cek-runtime.
    # Isolation: no ux_channel import here. Skip when live=null / no channel.
    if live_l != "null" and getattr(app, "_channel", None) is not None:
        cek_l = "require" if cek is None else str(cek).strip().lower()
        try:
            app.use_cek(mode=cek_l)
        except ValueError:
            raise
        except Exception:
            if live_l == "channel" and cek_l not in ("off", "0", "false", "no", "adapt"):
                raise

    pinned = None if auto_level else max(0, min(3, int(level)))
    want_motion = live_l != "null" and (auto_level or (pinned is not None and pinned >= 3))
    if want_motion:
        try:
            app.use_motion()
        except ImportError:
            raise
        except Exception:
            if pinned is not None and pinned >= 3:
                raise

    # Same folder name imports one at a time. The lock is reentrant for
    # this thread and times out for another thread. It is not global, so
    # other package names keep running, and package_import_lock stays off
    # the route body. isolate releases this lock while it waits for another
    # folder's import, then takes it again. Holding it across that wait
    # deadlocks a main.py that calls build().
    name_lock = package_build_lock(package_dir.name)
    timeout = _resolve_lock_timeout(lock_timeout)
    wait_token = begin_build_import_wait(timeout)
    acquired = False
    try:
        if timeout is None:
            name_lock.acquire()
            acquired = True
        elif name_lock.acquire(timeout=timeout):
            acquired = True
        else:
            raise BuildLockTimeout(package_dir.name, timeout)
        finder = pin_package_finder(package_dir)
        try:
            before = snapshot_package_modules(package_dir)
            begin_build_module_notes()
            try:
                isolate_package_imports(package_dir)

                bundle = app.mount(
                    package_dir,
                    asgi_app=None,
                    base=base,
                    fail_closed=fail_closed,
                    bind_pages=False,
                )

                registry = dict(getattr(bundle, "unit_registry", {}) or {})

                def _resolve(cls, path, name):
                    sid = str(getattr(cls, "id", None) or cls.__name__.lower())
                    return registry.get(sid)

                core = DirectoryRoutes(
                    package_dir,
                    base_directory=base,
                    hooks=RouterHooks(resolve_unit=_resolve),
                    fail_closed=fail_closed,
                )
                core.discover()
                _rebind_detached_pages(app, registry, bundle, core.records)
                asgi = host_bind(
                    asgi=asgi,
                    kind=kind,
                    core=core,
                    document=document,
                    wrap=author_wrap,
                    resolve_unit=_resolve,
                    partial=partial,
                )
                if bundle is not None and core.records:
                    bundle.route_table = core.route_table()
            finally:
                end_build_module_notes()
                release_build_package_modules(package_dir, before)
        finally:
            unpin_package_finder(finder)
    finally:
        if acquired and name_lock.depth_of_current() > 0:
            name_lock.release()
        end_build_import_wait(wait_token)

    return BuildResult((app, asgi, bundle))
