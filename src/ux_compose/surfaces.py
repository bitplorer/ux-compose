"""
Surface catalog + mount — additive world-builder.

Does not replace App.add or Channel.
It unifies scan → validate → Behavior registration → optional Page gate.

Laws enforced here:
* fail-closed id / path clashes
* ≤1 page owner per file (extra renderables become fragments: no URL)
* define-in-module only (imported classes are not auto-registered)

Page unit + host bind (when asgi_app is provided):
* Page units live under ``base_directory`` (default ``routes/``).
* Class name should match the module stem (``hello.py`` → ``Hello``).
* ``mount_surfaces`` builds ``RouterHooks(resolve_unit=...)`` so the
  synthetic page GET receives the live Behavior instance from
  ``unit_registry`` (keyed by ``cls.id`` or ``cls.__name__.lower()``).
* Explicit ``get``/``post`` methods on the class bypass ``resolve_unit``
  (ux-dom contract). Isolation: no Compose types leak into ux-dom.
* Host bind lives in ``surfaces_host`` (Invisible Strategy — pure core preferred).
"""

from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

logger = logging.getLogger("ux_compose.surfaces")

__all__ = [
    "ActionInfo",
    "Surface",
    "SurfaceBundle",
    "SurfaceError",
    "scan_surfaces",
    "validate_surfaces",
    "mount_surfaces",
]


class SurfaceError(Exception):
    def __init__(self, message: str, *, errors: Optional[list[str]] = None):
        super().__init__(message)
        self.errors = list(errors or [])


@dataclass(frozen=True)
class ActionInfo:
    name: str
    publish: bool = True
    caps: tuple[str, ...] = ()


@dataclass
class Surface:
    """One product unit in the catalog."""

    id: str
    cls: type
    module: str
    symbol: str
    source_file: str
    is_page: bool = False
    url_path: str = ""
    actions: tuple[ActionInfo, ...] = ()
    instance: Any = None


@dataclass
class SurfaceBundle:
    """Sealed mount evidence — additive observability."""

    surfaces: dict[str, Surface] = field(default_factory=dict)
    route_table: list[dict[str, Any]] = field(default_factory=list)
    action_table: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    sealed: bool = False
    unit_registry: dict[str, Any] = field(default_factory=dict)

    def action_names(self) -> list[str]:
        return [a["name"] for a in self.action_table]


def _is_action(obj: Any) -> bool:
    if obj is None or not callable(obj):
        return False
    if getattr(obj, "_ux_behavior_action", False):
        return True
    fn = getattr(obj, "__func__", None)
    if fn is not None and getattr(fn, "_ux_behavior_action", False):
        return True
    if type(obj).__name__ in ("ActionMethod", "BoundAction"):
        return True
    if getattr(obj, "_ux_action", False):
        return True
    return False


def _action_infos(cls: type) -> tuple[ActionInfo, ...]:
    out: list[ActionInfo] = []
    for name, val in vars(cls).items():
        if name.startswith("_") or not _is_action(val):
            continue
        caps = tuple(
            getattr(val, "_ux_behavior_caps", None)
            or getattr(val, "_ux_caps", ())
            or ()
        )
        publish = bool(getattr(val, "_ux_publish", True))
        out.append(ActionInfo(name=name, publish=publish, caps=caps))
    return tuple(sorted(out, key=lambda a: a.name))


def _is_renderable(cls: type) -> bool:
    return any(
        callable(getattr(cls, n, None))
        for n in ("render", "__render__", "__async_render__")
    )


def _is_unit_cls(cls: type) -> bool:
    if not isinstance(cls, type) or cls.__name__.startswith("_"):
        return False
    for b in cls.__mro__:
        mod = getattr(b, "__module__", "") or ""
        if b.__name__ == "Component" and (
            mod.startswith("ux_compose") or mod.startswith("ux_behavior")
        ):
            return True
    if _is_renderable(cls) and (_action_infos(cls) or getattr(cls, "routes", None)):
        return True
    return False


def _folder_url_prefix(rel_dir: str, base_directory: str) -> str:
    rel = rel_dir.replace("\\", "/").strip("/")
    base = base_directory.replace("\\", "/").strip("/")
    if rel == base or not rel:
        return ""
    if rel.startswith(base + "/"):
        parts = rel[len(base) + 1 :].split("/")
    else:
        parts = rel.split("/") if rel else []
    cleaned: list[str] = []
    for part in parts:
        if not part or part.startswith("_") or part == ".":
            continue
        if part == "..":
            if cleaned:
                cleaned.pop()
            continue
        if len(part) >= 2 and part[0] == "[" and part[-1] == "]":
            cleaned.append("{" + part[1:-1] + "}")
        elif part.startswith("(") and part.endswith(")"):
            continue
        else:
            cleaned.append(part)
    return ("/" + "/".join(cleaned)) if cleaned else ""


def _file_url(prefix: str, stem: str, route_file_name: str = "route") -> str:
    if stem in (route_file_name, "index"):
        return prefix or "/"
    if stem.startswith("_"):
        return prefix or "/"
    return f"{prefix}/{stem}".replace("//", "/") or f"/{stem}"


def _import_module(module: str, file: Path) -> Any:
    try:
        return importlib.import_module(module)
    except Exception:
        import importlib.util as ilu

        safe = module.replace("/", "_").replace(".", "_").replace("-", "_")
        if not safe.isidentifier():
            safe = "ux_surface_" + str(abs(hash(str(file))))
        spec = ilu.spec_from_file_location(safe, file)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {file}")
        mod = ilu.module_from_spec(spec)
        sys.modules[safe] = mod
        spec.loader.exec_module(mod)
        return mod


def scan_surfaces(
    package_dir: str | Path,
    *,
    base_directory: str = "routes",
    package_name: Optional[str] = None,
) -> list[Surface]:
    """Discover units under package_dir/base_directory (define-in-module only)."""
    root = Path(package_dir).resolve()
    base = root / base_directory
    if not base.exists():
        return []

    pkg = package_name or root.name
    found: list[Surface] = []

    for file in sorted(base.rglob("*.py")):
        if file.name == "__init__.py" or file.stem.startswith("_"):
            continue
        if any(p.startswith("_") for p in file.relative_to(root).parts[:-1]):
            continue

        rel_parent = str(file.parent.relative_to(root)).replace("\\", "/")
        module = f"{pkg}.{rel_parent.replace('/', '.')}.{file.stem}".replace("..", ".")
        while ".." in module:
            module = module.replace("..", ".")

        try:
            mod = _import_module(module, file)
        except Exception as exc:
            logger.exception("surface scan import failed %s: %s", file, exc)
            continue

        mod_name = getattr(mod, "__name__", module)
        prefix = _folder_url_prefix(rel_parent, base_directory)
        url = _file_url(prefix, file.stem)

        units_in_file: list[tuple[str, type]] = []
        for name, obj in vars(mod).items():
            if name.startswith("_") or not isinstance(obj, type):
                continue
            if not _is_unit_cls(obj):
                continue
            if getattr(obj, "__module__", None) not in (mod_name, module, file.stem):
                continue
            units_in_file.append((name, obj))

        page_assigned = False
        for name, obj in units_in_file:
            sid = str(getattr(obj, "id", None) or obj.__name__.lower())
            renderable = _is_renderable(obj)
            is_page = bool(renderable and not page_assigned)
            if is_page:
                page_assigned = True
            found.append(
                Surface(
                    id=sid,
                    cls=obj,
                    module=mod_name,
                    symbol=name,
                    source_file=str(file),
                    is_page=is_page,
                    url_path=url if is_page else "",
                    actions=_action_infos(obj),
                )
            )

    return found


def validate_surfaces(surfaces: Sequence[Surface], *, fail: bool = True) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    paths: set[str] = set()

    for s in surfaces:
        if not s.id or not str(s.id).strip():
            errors.append(f"{s.symbol}: empty id")
        if s.id in ids:
            errors.append(f"duplicate surface id {s.id!r}")
        ids.add(s.id)

        if s.is_page:
            if not s.url_path:
                errors.append(f"{s.id}: page without url_path")
            elif s.url_path in paths:
                errors.append(f"duplicate page path {s.url_path!r}")
            else:
                paths.add(s.url_path)

        for a in s.actions:
            if not hasattr(s.cls, a.name):
                errors.append(f"{s.id}.{a.name}: method missing")

    if errors and fail:
        raise SurfaceError(
            "surface validation failed:\n  - " + "\n  - ".join(errors),
            errors=errors,
        )
    return errors


def mount_surfaces(
    *,
    package_dir: str | Path,
    base_directory: str = "routes",
    compose_app: Any = None,
    asgi_app: Any = None,
    fail_closed: bool = True,
    bind_pages: bool = True,
    include_directory_router: bool | None = None,
    on_surface: Optional[Callable[[Surface], None]] = None,
    package_name: Optional[str] = None,
    host: str = "auto",
) -> SurfaceBundle:
    """Scan → validate → Behavior.add → optional page router.

    Host bind is delegated to ``surfaces_host.attach_page_router``
    (Invisible Strategy: pure core preferred; batteries only on host="batteries").
    ``include_directory_router`` is a deprecated alias of ``bind_pages``.
    """
    if include_directory_router is not None:
        bind_pages = include_directory_router
    surfaces = scan_surfaces(
        package_dir,
        base_directory=base_directory,
        package_name=package_name,
    )
    errors = validate_surfaces(surfaces, fail=fail_closed)
    bundle = SurfaceBundle(errors=list(errors))

    if compose_app is not None and surfaces:
        classes = [s.cls for s in surfaces]
        if hasattr(compose_app, "add"):
            compose_app.add(*classes)

        behavior = getattr(compose_app, "_behavior", None) or getattr(
            compose_app, "behavior", None
        )
        components = {}
        if behavior is not None and hasattr(behavior, "components"):
            try:
                components = dict(behavior.components())
            except Exception:
                components = {}

        for s in surfaces:
            inst = components.get(s.id)
            if inst is None:
                try:
                    inst = s.cls()
                except Exception:
                    inst = None
            s.instance = inst
            bundle.surfaces[s.id] = s
            if inst is not None:
                bundle.unit_registry[s.id] = inst
            for a in s.actions:
                bundle.action_table.append(
                    {
                        "name": f"{s.id}.{a.name}",
                        "surface": s.id,
                        "publish": a.publish,
                        "caps": list(a.caps),
                    }
                )
            if s.is_page and s.url_path:
                bundle.route_table.append(
                    {
                        "method": ["get"],
                        "path": s.url_path,
                        "surface": s.id,
                        "file": s.source_file,
                    }
                )
            if on_surface is not None:
                on_surface(s)
    else:
        for s in surfaces:
            bundle.surfaces[s.id] = s
            for a in s.actions:
                bundle.action_table.append(
                    {
                        "name": f"{s.id}.{a.name}",
                        "surface": s.id,
                        "publish": a.publish,
                        "caps": list(a.caps),
                    }
                )
            if s.is_page and s.url_path:
                bundle.route_table.append(
                    {
                        "method": ["get"],
                        "path": s.url_path,
                        "surface": s.id,
                        "file": s.source_file,
                    }
                )

    if bind_pages and asgi_app is not None:
        try:
            from ux_compose.surfaces_host import attach_page_router

            table = attach_page_router(
                asgi_app=asgi_app,
                package_dir=package_dir,
                base_directory=base_directory,
                unit_registry=bundle.unit_registry,
                fail_closed=fail_closed,
                host=host,
            )
            if table:
                bundle.route_table = table
        except ImportError:
            if fail_closed:
                raise SurfaceError(
                    "ux-dom routing unavailable (install ux-dom) but asgi_app was provided"
                )
            logger.warning("page router not available; page gate skipped")

    bundle.sealed = True
    return bundle
