"""Product page-unit routing — filesystem → RouteRecord.

This is Next's app router, not React. ux-dom renders trees; ux-compose
owns ``routes/`` discovery and host bind.

No FastAPI / Starlette imports. Host adapters materialize framework
routes from :class:`DirectoryRoutes`.

Locked model:
  - URL path = filesystem relative to base (class name never in path)
  - Page unit = renderable class whose name matches the module stem
  - fail_closed on ambiguity / duplicates
  - RouterHooks.resolve_unit only for synthetic page GET
"""
from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, runtime_checkable

logger = logging.getLogger("ux_compose.routing.core")

__all__ = [
    "DirectoryRoutesError",
    "DirectoryRouterError",
    "RouterHooks",
    "ResolveUnit",
    "AcceptSymbol",
    "OnRoute",
    "DirectoryRoutes",
    "RouteRecord",
    "pick_page_type",
    "module_exports",
    "http_path",
    "is_json_payload",
    "is_stream_payload",
    "apply_html_document",
]


class DirectoryRoutesError(RuntimeError):
    """Fail-closed routing errors (ambiguous page, invalid export, etc.)."""


# Historical name from the ux-dom leftover DirectoryRouter era.
DirectoryRouterError = DirectoryRoutesError


@runtime_checkable
class ResolveUnit(Protocol):
    """(cls, path, name) → instance | None. None → caller falls back to cls()."""

    def __call__(self, cls: type, path: str, name: str) -> Any: ...


@runtime_checkable
class AcceptSymbol(Protocol):
    """(name, obj, module) → bool. False skips the symbol; raise → error."""

    def __call__(self, name: str, obj: Any, module: Any) -> bool: ...


@runtime_checkable
class OnRoute(Protocol):
    """(record) → None. record = {method, path, name}. Raise → error if fail_closed."""

    def __call__(self, record: dict) -> None: ...


class RouterHooks:
    """Generic extension sockets — host-agnostic.

    resolve_unit is used only for the synthetic page GET.
    Page units have no HTTP verbs; extra APIs live on the FastAPI process.
    """

    __slots__ = ("resolve_unit", "accept_symbol", "on_route")

    def __init__(
        self,
        resolve_unit: Optional[ResolveUnit] = None,
        accept_symbol: Optional[AcceptSymbol] = None,
        on_route: Optional[OnRoute] = None,
    ):
        self.resolve_unit = resolve_unit
        self.accept_symbol = accept_symbol
        self.on_route = on_route


def module_exports(route_file: Any) -> list:
    if hasattr(route_file, "__all__"):
        return [str(x) for x in list(route_file.__all__)]
    mod_name = getattr(route_file, "__name__", "")
    names = []
    for r in dir(route_file):
        if r.startswith("_"):
            continue
        obj = getattr(route_file, r, None)
        if isinstance(obj, type) and getattr(obj, "__module__", None) == mod_name:
            names.append(r)
        elif callable(obj) and not isinstance(obj, type):
            if getattr(obj, "__module__", None) == mod_name:
                names.append(r)
    return names


def http_path(*segments: str) -> str:
    """Filesystem relative to ``routes/`` → URL.

    Locked path law (one scanner):
      * class name never in the path
      * ``index.py`` / ``route.py`` → folder prefix or ``/``
      * ``[param]`` → ``{param}``
    """
    parts = [s for s in segments if s and s not in (".",)]
    if parts and parts[-1] in ("index", "route"):
        parts = parts[:-1]
    out: list[str] = []
    for part in parts:
        if part.startswith("_"):
            continue
        if part == "..":
            if out:
                out.pop()
            continue
        if len(part) >= 2 and part[0] == "[" and part[-1] == "]":
            out.append("{" + part[1:-1] + "}")
        elif part.startswith("(") and part.endswith(")"):
            continue
        else:
            out.append(part)
    return ("/" + "/".join(out)) if out else "/"


def is_json_payload(obj: Any) -> bool:
    """True when the return value is a JSON body, not an HTML tree.

    Payload type picks media type (not Accept):
      dict / list-of-dicts → JSON (FastAPI encodes)
      async/sync generator → StreamingResponse
      str / bytes / tag / Document / Component → HTML
      Response subclass → pass through
    """
    if isinstance(obj, dict):
        return True
    if isinstance(obj, (list, tuple)):
        if not obj:
            return True
        return all(isinstance(x, dict) for x in obj)
    return False


def is_stream_payload(obj: Any) -> bool:
    """True when the return value is a body stream, not a buffered tree.

    Trees stay HTMLResponse. ``str`` is iterable — it is not a stream.
    Authors stream by returning a generator / async generator (or an
    explicit StreamingResponse).
    """
    if obj is None or isinstance(obj, (str, bytes, bytearray, memoryview, dict)):
        return False
    if is_json_payload(obj):
        return False
    if inspect.isasyncgen(obj) or inspect.isgenerator(obj):
        return True
    if hasattr(obj, "__aiter__") and not hasattr(obj, "__render__") and not hasattr(
        obj, "children"
    ):
        return True
    return False


def apply_html_document(document: Any, payload: Any) -> Any:
    """Put an HTML fragment into the Document shell. Never drop the payload.

    Both hosts call this on the HTML branch only (JSON / stream / Response
    skip it). Author-provided ``document=`` is the SSoT. A synthesized
    Document is for ``document.mount`` (CSP / static), not for wrapping.

    HTML strings are not valid ``Document(*args)`` children — ux-dom treats
    a positional str on ``<body>`` as a script ``src``. Convert via ``raw()``
    so the fragment lands in the body as markup.
    """
    if document is None or not callable(document):
        return payload
    child = _document_child(payload)
    try:
        if child is None:
            return document()
        return document(child)
    except Exception:
        return payload


def _document_child(payload: Any) -> Any:
    if payload is None:
        return None
    if isinstance(payload, (bytes, bytearray, memoryview)):
        payload = bytes(payload).decode("utf-8")
    if isinstance(payload, str):
        try:
            from ux_dom.dom.src.utils.dom_util import raw

            return raw(payload)
        except Exception:
            return payload
    return payload


def is_renderable_unit(klass: type) -> bool:
    return any(
        callable(getattr(klass, n, None))
        for n in ("render", "__render__", "__async_render__")
    )


def _stem_key(stem: str) -> str:
    s = (stem or "").lower()
    if len(s) >= 2 and s[0] == "[" and s[-1] == "]":
        s = s[1:-1]
        if s.startswith("..."):
            s = s[3:]
    return s


def pick_page_type(
    route_file: Any,
    exported: list,
    file_stem: str,
    *,
    accept_symbol: Optional[Callable[..., bool]] = None,
    fail_closed: bool = True,
):
    """Select the page unit: renderable class whose name matches the file stem."""
    mod_name = getattr(route_file, "__name__", "")
    stem = _stem_key(file_stem)
    matches = []
    for name in exported:
        obj = getattr(route_file, name, None)
        if not isinstance(obj, type):
            continue
        if getattr(obj, "__module__", None) != mod_name:
            continue
        if accept_symbol is not None:
            try:
                if not accept_symbol(name, obj, route_file):
                    continue
            except Exception:
                continue
        if not is_renderable_unit(obj):
            continue
        if name.lower() == stem or getattr(obj, "__name__", "").lower() == stem:
            matches.append(obj)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        msg = (
            f"Ambiguous page unit in {getattr(route_file, '__name__', '?')}: "
            f"multiple renderable classes match stem {file_stem!r}: "
            f"{[m.__name__ for m in matches]}"
        )
        if fail_closed:
            raise DirectoryRoutesError(msg)
        logger.warning("%s", msg)
        return None
    return None


def import_route_module(module: str, file: Path) -> Any:
    if module in sys.modules:
        return sys.modules[module]
    spec = importlib.util.spec_from_file_location(module, file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {file}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module] = mod
    spec.loader.exec_module(mod)
    return mod


@dataclass
class RouteRecord:
    """Pure route record — host adapters bind callables to framework routes."""

    method: str
    path: str
    name: str
    handler: Any = None
    page_cls: Any = None
    kind: str = "page"  # page | explicit | route_module


@dataclass
class DirectoryRoutes:
    """Discover page units under base_directory. No framework imports.

    Usage::

        from ux_compose.routing import DirectoryRoutes, RouterHooks
        core = DirectoryRoutes(package_dir, hooks=hooks)
        records = core.discover()
        # adapter.mount(core, asgi_app)
    """

    package_dir: Path
    base_directory: str = "routes"
    hooks: Optional[RouterHooks] = None
    fail_closed: bool = True
    records: list = field(default_factory=list)

    def discover(self) -> list:
        parent = Path(self.package_dir).resolve()
        base = parent / self.base_directory
        self.records = []
        if not base.exists():
            logger.warning("DirectoryRoutes missing base %s", base)
            return self.records

        package_name = parent.name
        hooks = self.hooks or RouterHooks()

        for file in sorted(base.rglob("*.py")):
            if file.name == "__init__.py" or file.stem.startswith("_"):
                continue
            if any(part.startswith("_") for part in file.relative_to(parent).parts[:-1]):
                continue

            rel_folder = str(Path(file.parent).relative_to(parent)).replace("\\", "/")
            file_package_path = f"{package_name}/{rel_folder}".replace("\\", "/")
            module = file_package_path.replace("/", ".") + "." + file.stem
            try:
                route_file = import_route_module(module, file)
            except Exception:
                logger.exception("DirectoryRoutes failed to import %s", module)
                continue

            try:
                rel = file.relative_to(base).with_suffix("")
            except ValueError:
                continue
            path = http_path(*rel.parts)

            exported = module_exports(route_file)
            page_cls = pick_page_type(
                route_file,
                exported,
                file.stem,
                accept_symbol=hooks.accept_symbol,
                fail_closed=self.fail_closed,
            )
            if page_cls is None:
                continue

            # Page GET is always synthetic. HTTP verbs do not live on the
            # Component (FastAPI must not inspect classmethods). Extra APIs
            # are author routes on the FastAPI process.
            rec = RouteRecord(
                method="GET",
                path=path,
                name=page_cls.__name__,
                handler=None,
                page_cls=page_cls,
                kind="page",
            )
            self._emit(rec, hooks)

        return self.records

    def _emit(self, rec: RouteRecord, hooks: RouterHooks) -> None:
        payload = {
            "method": rec.method,
            "path": rec.path,
            "name": rec.name,
            "kind": rec.kind,
            "page_cls": rec.page_cls,
        }
        if hooks.on_route is not None:
            try:
                hooks.on_route(payload)
            except Exception as exc:
                if self.fail_closed:
                    raise DirectoryRoutesError(str(exc)) from exc
        self.records.append(rec)

    def route_table(self) -> list:
        return [
            {"method": r.method, "path": r.path, "name": r.name, "kind": r.kind}
            for r in self.records
        ]
