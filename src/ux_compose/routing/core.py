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

import contextvars
import hashlib
import importlib
import importlib._bootstrap as _import_bootstrap
import importlib.util
import inspect
import linecache
import logging
import os
import re
import sys
import sysconfig
import threading
import time
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, runtime_checkable

logger = logging.getLogger("ux_compose.routing.core")

__all__ = [
    "DirectoryRoutesError",
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


_PY_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\Z")


def _non_identifier_param(path: str) -> str | None:
    """First ``{name}`` that cannot be a ``re`` group, else None."""
    for seg in str(path or "").strip("/").split("/"):
        if len(seg) >= 2 and seg.startswith("{") and seg.endswith("}"):
            name = seg[1:-1]
            if _PY_IDENT.fullmatch(name) is None:
                return name
    return None


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

    A ``str`` / ``bytes`` payload is untrusted HTML: it goes through
    ux-dom's ``sanitize_html`` whether or not there is a Document.
    ``Markup`` is explicit trust and stays as written. HTML strings are not
    valid ``Document(*args)`` children (ux-dom treats a positional str on
    ``<body>`` as a script ``src``), so the sanitized fragment goes in
    through ``raw()``.
    """
    payload = sanitize_html_payload(payload)
    if document is None or not callable(document):
        return payload
    child = _document_child(payload)
    try:
        if child is None:
            return document()
        return document(child)
    except Exception:
        logger.exception("apply_html_document failed; returning the fragment")
        return payload


def sanitize_html_payload(payload: Any) -> Any:
    """``str`` / ``bytes`` route body → ``sanitize_html`` str. Others unchanged."""
    from ux_dom.response import sanitize_html

    if isinstance(payload, (bytes, bytearray, memoryview)):
        payload = bytes(payload).decode("utf-8")
    if isinstance(payload, str):
        return sanitize_html(payload)
    return payload


def _document_child(payload: Any) -> Any:
    if isinstance(payload, str):
        from ux_dom.dom import raw

        return raw(payload)
    return payload


class _Rendered:
    """A tree chunk rendered by ux-dom: trusted (``__html__``) in the stream."""

    __slots__ = ("html",)

    def __init__(self, html: str) -> None:
        self.html = html

    def __html__(self) -> str:
        return self.html


def _stream_text(chunk: Any, decoder: Any) -> Any:
    if chunk is None:
        return ""
    if isinstance(chunk, (bytes, bytearray, memoryview)):
        return decoder.decode(bytes(chunk))
    if isinstance(chunk, str) or hasattr(chunk, "__html__"):
        return chunk
    from ux_dom.response import to_html_bytes

    return _Rendered(to_html_bytes(chunk).decode("utf-8"))


def sanitize_stream_payload(payload: Any) -> Any:
    """Generator route body → ``sanitize_html_stream`` of its text.

    Sync stays sync, async stays async. ``bytes`` chunks are decoded as one
    UTF-8 stream; ``str`` chunks are untrusted; ``Markup`` and tree chunks
    are sent as written. Joined, the pieces equal ``sanitize_html`` of the
    joined text. A stream that holds more than ``MAX_BUFFER_CHARS``
    characters without a safe boundary raises ``HtmlStreamOverflow`` and
    sends none of the held text.
    """
    import codecs

    from ux_dom.response import sanitize_html_stream

    decoder = codecs.getincrementaldecoder("utf-8")()
    if hasattr(payload, "__aiter__"):

        async def atexts():
            async for chunk in payload:
                yield _stream_text(chunk, decoder)
            yield decoder.decode(b"", final=True)

        return sanitize_html_stream(atexts())

    def texts():
        for chunk in payload:
            yield _stream_text(chunk, decoder)
        yield decoder.decode(b"", final=True)

    return sanitize_html_stream(texts())


async def open_html_stream(payload: Any) -> Any:
    """Sanitized stream with its first piece already computed.

    Hosts call this before they send the status line, so a stream that
    fails before its first piece (``HtmlStreamOverflow`` included) becomes a
    500 with no body. A failure after that point is raised mid-response.
    A sync stream's first piece is computed off the event loop.
    """
    import asyncio

    stream = sanitize_stream_payload(payload)
    if hasattr(stream, "__aiter__"):
        first = await anext(stream, None)

        async def arest():
            if first is not None:
                yield first
            async for piece in stream:
                yield piece

        return arest()
    first = await asyncio.to_thread(next, stream, None)

    def rest():
        if first is not None:
            yield first
        yield from stream

    return rest()


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
                if fail_closed:
                    raise
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


def _resolved(path: Path) -> Path | None:
    try:
        return path.resolve()
    except OSError:
        return None


def _is_under(path: Path, root: Path) -> bool:
    resolved = _resolved(path)
    if resolved is None:
        return False
    try:
        resolved.relative_to(root)
    except ValueError:
        return False
    return True


def _module_paths(mod: Any) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()

    def add(value: object) -> None:
        if not isinstance(value, str) or not value or value in seen:
            return
        if value in {"built-in", "frozen", "namespace"}:
            return
        seen.add(value)
        found.append(Path(value))

    add(getattr(mod, "__file__", None))
    add(getattr(mod, "__cached__", None))
    spec = getattr(mod, "__spec__", None)
    add(getattr(spec, "origin", None) if spec is not None else None)
    pkg_paths = getattr(mod, "__path__", None)
    if pkg_paths is not None:
        for entry in pkg_paths:
            add(entry)
    return found


def _path_roots(*keys: str) -> tuple[Path, ...]:
    roots: list[Path] = []
    for key in keys:
        raw = sysconfig.get_path(key)
        if not raw:
            continue
        resolved = _resolved(Path(raw))
        if resolved is not None and resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def _module_matches_file(mod: Any, file: Path) -> bool:
    origin = getattr(mod, "__file__", None)
    if not isinstance(origin, str) or not origin:
        return False
    left = _resolved(Path(origin))
    right = _resolved(Path(file))
    return left is not None and left == right


def _clear_linecache(paths: list[Path], root: Path | None = None) -> None:
    targets = {item for item in (_resolved(path) for path in paths) if item is not None}
    root_resolved = _resolved(root) if root is not None else None
    raw_keys = {str(path) for path in paths}
    for key in list(linecache.cache):
        resolved = _resolved(Path(key))
        under_root = (
            root_resolved is not None
            and resolved is not None
            and _is_under(resolved, root_resolved)
        )
        if key in raw_keys or resolved in targets or under_root:
            linecache.cache.pop(key, None)
    linecache.checkcache()


def _other_thread_importing(name: str) -> bool:
    """True when another thread holds the import lock for ``name`` or a child.

    ``importlib._bootstrap._find_and_load_unlocked`` reads
    ``sys.modules[parent]`` while it still holds the child lock (the
    lookups are at lines 1319 and 1348). Popping the parent there raises
    ``KeyError``. This only reads the lock owner. The same thread is
    skipped: a module that calls ``build()`` already holds its own import
    lock, and ``_ModuleLock.acquire`` takes no timeout.
    """
    locks = getattr(_import_bootstrap, "_module_locks", None)
    if not isinstance(locks, dict):
        return False
    me = threading.get_ident()
    prefix = name + "."
    for key, ref in list(locks.items()):
        if key != name and not (isinstance(key, str) and key.startswith(prefix)):
            continue
        lock = ref() if callable(ref) else None
        owner = getattr(lock, "owner", None) if lock is not None else None
        if isinstance(owner, int) and owner != me:
            return True
    return False


def _forget_module(name: str) -> list[Path]:
    if _other_thread_importing(name):
        return []
    mod = sys.modules.pop(name, None)
    if mod is None:
        return []
    parent_name, _, child = name.rpartition(".")
    parent = sys.modules.get(parent_name) if parent_name else None
    if parent is not None and child and getattr(parent, child, None) is mod:
        delattr(parent, child)
    return _module_paths(mod)


# Sys.modules bookkeeping only. Do not hold this while route or module
# code runs: that deadlocks with the import lock when a module calls build().
package_import_lock = threading.RLock()

# One reentrant lock per package folder name. Held across that name's
# import phase so two directories cannot share sys.modules keys at once.
# Different names stay parallel. A cross-thread wait is bounded.
# The waiter set is how isolate sees that the importing thread is blocked
# on this lock. Waiting for that import while holding the lock deadlocks.
class _PackageBuildLock:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._guard = threading.Lock()
        self._owner: int | None = None
        self._depth = 0
        self._waiters: set[int] = set()
        self._generation = 0

    def depth_of_current(self) -> int:
        with self._guard:
            if self._owner != threading.get_ident():
                return 0
            return self._depth

    def owner(self) -> int | None:
        with self._guard:
            return self._owner

    def waiters(self) -> set[int]:
        with self._guard:
            return set(self._waiters)

    def generation(self) -> int:
        """How many times a thread newly acquired this lock."""
        with self._guard:
            return self._generation

    def acquire(self, timeout: float | None = None) -> bool:
        me = threading.get_ident()
        with self._guard:
            if self._owner == me:
                self._depth += 1
                self._lock.acquire()
                return True
            self._waiters.add(me)
        try:
            if timeout is None:
                acquired = bool(self._lock.acquire())
            else:
                acquired = bool(self._lock.acquire(timeout=timeout))
        finally:
            with self._guard:
                self._waiters.discard(me)
        if not acquired:
            return False
        with self._guard:
            self._owner = me
            self._depth = 1
            self._generation += 1
        return True

    def release(self) -> None:
        me = threading.get_ident()
        with self._guard:
            if self._owner != me or self._depth <= 0:
                raise RuntimeError("cannot release un-acquired build lock")
            self._depth -= 1
            if self._depth == 0:
                self._owner = None
        self._lock.release()


_package_build_locks: dict[str, _PackageBuildLock] = {}
_package_build_locks_guard = threading.Lock()


class PackageImportConflict(RuntimeError):
    """A module under this name is in use from a different folder.

    Main serves that other folder's code. ``build()`` fails instead, and
    the message names both directories.
    """

    def __init__(self, module: str, loaded_from: Path, building: Path) -> None:
        self.module = module
        self.loaded_from = loaded_from
        self.building = building
        super().__init__(
            f"{module} is already loaded from {loaded_from} while building {building}"
        )


def _top_package_dir(mod: Any, module_name: str) -> Path | None:
    """Directory of the top package, from a module file that belongs to it."""
    origins = _resolved_origins(mod)
    if not origins:
        return None
    file = origins[0]
    parts = module_name.split(".")
    index = len(parts) - 1 if file.name == "__init__.py" else len(parts) - 2
    if index < 0:
        return file.parent
    try:
        return file.parents[index]
    except IndexError:
        return file.parent


class BuildLockTimeout(TimeoutError):
    """Another thread is still importing this package name."""

    def __init__(self, package: str, timeout: float) -> None:
        self.package = package
        self.timeout = timeout
        super().__init__(
            f"timed out waiting to build {package!r} after {timeout:g}s; "
            "another thread is still importing it "
            "(UX_COMPOSE_BUILD_LOCK_TIMEOUT or build(lock_timeout=...); "
            "lock_timeout=None waits until that build finishes)"
        )


def package_build_lock(package: str) -> _PackageBuildLock:
    with _package_build_locks_guard:
        lock = _package_build_locks.get(package)
        if lock is None:
            lock = _PackageBuildLock()
            _package_build_locks[package] = lock
        return lock


_WAIT_UNSET = object()
_build_wait_timeout: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "ux_compose_build_wait",
    default=_WAIT_UNSET,
)


def begin_build_import_wait(timeout: float | None) -> contextvars.Token[Any]:
    """Remember this build's import wait. ``None`` waits until the import ends."""
    return _build_wait_timeout.set(timeout)


def end_build_import_wait(token: contextvars.Token[Any]) -> None:
    _build_wait_timeout.reset(token)


_DEFAULT_LOCK_TIMEOUT = 60.0


def parse_lock_timeout(value: Any, *, where: str) -> float | None:
    """Seconds, or None to wait until done.

    A blank string is the default, 60 seconds. ``0`` tries once and does
    not wait. ``none`` and ``inf``, any case, wait until done.
    ``infinite`` is the same as ``inf``. ``None`` waits until done, the
    same as ``lock_timeout=None``. A negative number, ``nan``, or other
    bad value raises ``ValueError``. The message names
    ``UX_COMPOSE_BUILD_LOCK_TIMEOUT``. ``build()``, ``App.mount``, and
    ``DirectoryRoutes.discover`` share this parser.
    """
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return _DEFAULT_LOCK_TIMEOUT
        token = value.strip().lower()
        if token in {"none", "inf", "infinite"}:
            return None
        text: Any = value.strip()
    else:
        text = value
    try:
        number = float(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"invalid {where} value {value!r}; expected seconds, inf, or none"
            " (UX_COMPOSE_BUILD_LOCK_TIMEOUT)"
        ) from exc
    if number != number or number < 0:
        raise ValueError(
            f"invalid {where} value {value!r}; expected a non-negative number of seconds"
            " (UX_COMPOSE_BUILD_LOCK_TIMEOUT)"
        )
    if number == float("inf"):
        return None
    return number


def _import_wait_seconds() -> float | None:
    """Seconds to wait for another thread's import. ``None`` waits until it ends.

    ``build()`` sets the value from ``lock_timeout`` or
    ``UX_COMPOSE_BUILD_LOCK_TIMEOUT``. A direct call uses that environment
    variable, otherwise 60. A bad value is ``ValueError``, the same as
    ``build()``.
    """
    current = _build_wait_timeout.get()
    if current is not _WAIT_UNSET:
        return current
    return lock_timeout_from_env()


def lock_timeout_from_env() -> float | None:
    """``UX_COMPOSE_BUILD_LOCK_TIMEOUT``, or 60 when that variable is unset."""
    raw = os.environ.get("UX_COMPOSE_BUILD_LOCK_TIMEOUT")
    if raw is None:
        return _DEFAULT_LOCK_TIMEOUT
    return parse_lock_timeout(raw, where="UX_COMPOSE_BUILD_LOCK_TIMEOUT")


def _exact_other_owner(name: str) -> bool:
    """True when another thread holds the import lock for this exact module."""
    locks = getattr(_import_bootstrap, "_module_locks", None)
    if not isinstance(locks, dict):
        return False
    ref = locks.get(name)
    lock = ref() if callable(ref) else None
    owner = getattr(lock, "owner", None) if lock is not None else None
    return isinstance(owner, int) and owner != threading.get_ident()


def _module_file_in_tree(root: Path, package: str, module: str) -> bool:
    """True when this folder has a file for ``module``."""
    if module != package and not module.startswith(package + "."):
        return False
    rel = module[len(package) :].lstrip(".")
    base = root.joinpath(*rel.split(".")) if rel else root
    return (base / "__init__.py").is_file() or base.with_suffix(".py").is_file()


def _wait_for_other_importers(names: list[str], timeout: float | None) -> bool:
    """Poll until those imports release. Do not acquire the import lock.

    ``_ModuleLock.acquire`` has no timeout. Taking it would also deadlock
    a module that calls ``build()`` on this thread. ``False`` means the
    budget ran out while another thread still held a lock.
    """
    deadline = None if timeout is None else time.monotonic() + timeout
    pending = list(names)
    while pending:
        if deadline is not None and time.monotonic() >= deadline:
            return False
        pending = [name for name in pending if _other_thread_importing(name)]
        if pending:
            time.sleep(0.01)
    return True


def _package_name_on_sys_path(package: str) -> bool:
    """True when a normal import of ``package`` could already see a file."""
    for entry in list(sys.path):
        root = Path(entry or ".").resolve()
        if (root / package / "__init__.py").is_file():
            return True
        if (root / f"{package}.py").is_file():
            return True
    return False


class _PinnedPackageFinder:
    """Resolve one package name to one directory, ignoring sys.path order.

    The name still has to be importable. A folder that is not on
    ``sys.path``, and has no other copy there, is left alone so the
    import raises ``ModuleNotFoundError`` the way a normal import does.
    """

    def __init__(self, package: str, root: Path) -> None:
        self.package = package
        self.root = root.resolve()

    def find_spec(self, fullname: str, path: object = None, target: object = None):
        # Every thread, not only the builder. A cached module skips find_spec,
        # so another thread must not be able to load a different folder under
        # this name while the pin is installed.
        if fullname != self.package and not fullname.startswith(self.package + "."):
            return None
        if not _package_name_on_sys_path(self.package):
            return None
        rel = fullname[len(self.package) :].lstrip(".")
        base = self.root.joinpath(*rel.split(".")) if rel else self.root
        init = base / "__init__.py"
        module = base.with_suffix(".py")
        if init.is_file():
            return importlib.util.spec_from_file_location(
                fullname,
                init,
                submodule_search_locations=[str(base)],
            )
        if module.is_file():
            return importlib.util.spec_from_file_location(fullname, module)
        return None


def pin_package_finder(package_dir: Path) -> _PinnedPackageFinder:
    finder = _PinnedPackageFinder(package_dir.name, Path(package_dir))
    with package_import_lock:
        sys.meta_path.insert(0, finder)
    return finder


def unpin_package_finder(finder: _PinnedPackageFinder) -> None:
    with package_import_lock:
        try:
            sys.meta_path.remove(finder)
        except ValueError:
            pass


def snapshot_package_modules(package_dir: str | Path) -> dict[str, int]:
    """Identity of ``sys.modules`` entries for this folder name, before import."""
    name = Path(package_dir).resolve().name
    with package_import_lock:
        return {
            key: id(mod)
            for key, mod in sys.modules.items()
            if mod is not None and (key == name or key.startswith(name + "."))
        }


def _is_route_file(path: Path, root: Path) -> bool:
    if path.name == "__init__.py" or not path.is_relative_to(root):
        return False
    rel = path.relative_to(root)
    if not rel.parts or rel.parts[0] != "routes":
        return False
    return not any(part.startswith("_") for part in rel.parts)


def _is_this_folder_route(mod: Any, root: Path) -> bool:
    """True when every origin of ``mod`` is a route file inside ``root``."""
    origins = _resolved_origins(mod)
    if not origins:
        return False
    return all(_is_route_file(path, root) for path in origins)


def _is_package_shell(path: Path, root: Path) -> bool:
    """The app ``__init__.py`` and route-package ``__init__.py`` files.

    ``models/__init__.py`` is a helper package, not a shell.
    """
    if path.name != "__init__.py" or not path.is_relative_to(root):
        return False
    rel = path.relative_to(root)
    if rel == Path("__init__.py"):
        return True
    return bool(rel.parts) and rel.parts[0] == "routes"


def _keep_helper(mod: Any, root: Path) -> bool:
    """Helpers stay for the next rebuild. Route files and package shells do not."""
    origins = _resolved_origins(mod)
    if not origins:
        return True
    for path in origins:
        if not path.is_relative_to(root):
            return False
        if _is_package_shell(path, root) or _is_route_file(path, root):
            return False
    return True


def release_build_package_modules(
    package_dir: str | Path, before: dict[str, int]
) -> None:
    """Drop another folder's modules. Keep this folder's routes and helpers.

    A route module that lives in ``package_dir`` stays in ``sys.modules``,
    so ``import pkg.routes.a`` is the module that served the page and
    ``typing.get_type_hints`` can still see its globals. The file runs
    again only when its bytes change. Eviction of that name happens when
    a different directory is isolated, not at the end of every build.
    Helpers and modules that were already imported stay. Package shells
    stay when a kept child or the pre-build snapshot anchors them.
    """
    root = Path(package_dir).resolve()
    name = root.name
    with package_import_lock:
        keep: set[str] = set()
        drop: list[str] = []
        for key in list(sys.modules):
            if key != name and not key.startswith(name + "."):
                continue
            mod = sys.modules.get(key)
            if mod is None:
                continue
            if (
                before.get(key) == id(mod)
                or _is_on_stack(mod)
                or _is_installed_module(mod)
            ):
                keep.add(key)
                continue
            if _is_this_folder_route(mod, root) or _keep_helper(mod, root):
                keep.add(key)
                continue
            drop.append(key)
        anchored = set(keep)
        for key in keep:
            parent, _, _ = key.rpartition(".")
            while parent:
                anchored.add(parent)
                parent, _, _ = parent.rpartition(".")
        for key in sorted(drop, key=lambda item: item.count("."), reverse=True):
            if key in anchored:
                continue
            mod = sys.modules.get(key)
            if mod is None or _is_on_stack(mod) or _is_installed_module(mod):
                continue
            _forget_module(key)


_source_tokens: weakref.WeakKeyDictionary[Any, bytes] = weakref.WeakKeyDictionary()
_installed_roots: tuple[Path, ...] | None = None
_build_notes = threading.local()


def _installed_roots_resolved() -> tuple[Path, ...]:
    global _installed_roots
    if _installed_roots is None:
        _installed_roots = _path_roots("stdlib", "platstdlib", "purelib", "platlib")
    return _installed_roots


def _resolved_origins(mod: Any) -> list[Path]:
    """File locations for ``mod``. Skips names and parent-folder guesses."""
    found: list[Path] = []
    seen: set[Path] = set()

    def add(value: object) -> None:
        if not isinstance(value, str) or not value:
            return
        if value in {"built-in", "frozen", "namespace"}:
            return
        resolved = _resolved(Path(value))
        if resolved is None or resolved in seen:
            return
        seen.add(resolved)
        found.append(resolved)

    add(getattr(mod, "__file__", None))
    spec = getattr(mod, "__spec__", None)
    add(getattr(spec, "origin", None) if spec is not None else None)
    pkg_paths = getattr(mod, "__path__", None)
    if pkg_paths is None:
        return found
    try:
        entries = list(pkg_paths)
    except KeyError:
        return found
    for entry in entries:
        add(entry)
    return found


def _is_installed_path(path: Path) -> bool:
    return any(path.is_relative_to(root) for root in _installed_roots_resolved())


def _is_installed_module(mod: Any) -> bool:
    origins = _resolved_origins(mod)
    return bool(origins) and any(_is_installed_path(path) for path in origins)


def _is_on_stack(mod: Any) -> bool:
    """True when ``mod`` is executing, or is a package of a module that is.

    Evicting the package out from under the module that is importing raises
    KeyError inside importlib. The frame walk is the import stack, not a
    directory-name match.
    """
    mod_dict = getattr(mod, "__dict__", None)
    name = getattr(mod, "__name__", None)
    frame: Any = sys._getframe(1)
    while frame is not None:
        globs = frame.f_globals
        if mod_dict is not None and globs is mod_dict:
            return True
        child = globs.get("__name__")
        if (
            isinstance(name, str)
            and isinstance(child, str)
            and child.startswith(name + ".")
        ):
            child_mod = sys.modules.get(child)
            if child_mod is not None and getattr(child_mod, "__dict__", None) is globs:
                return True
        frame = frame.f_back
    return False


def _should_replace(mod: Any, root: Path) -> bool:
    """Replace only a module whose file resolves to a different directory."""
    if _is_on_stack(mod) or _is_installed_module(mod):
        return False
    origins = _resolved_origins(mod)
    if not origins:
        return False
    return not all(path.is_relative_to(root) for path in origins)


def _foreign_import_owners(names: list[str]) -> set[int]:
    """Other threads holding an import lock for ``names`` or a child."""
    locks = getattr(_import_bootstrap, "_module_locks", None)
    if not isinstance(locks, dict):
        return set()
    me = threading.get_ident()
    owners: set[int] = set()
    for name in names:
        prefix = name + "."
        for key, ref in list(locks.items()):
            if key != name and not (isinstance(key, str) and key.startswith(prefix)):
                continue
            lock = ref() if callable(ref) else None
            owner = getattr(lock, "owner", None) if lock is not None else None
            if isinstance(owner, int) and owner != me:
                owners.add(owner)
    return owners


def _importers_need_name_lock(lock: _PackageBuildLock, names: list[str]) -> bool:
    """True when an importer is waiting on ``lock`` or already holds it."""
    owners = _foreign_import_owners(names)
    if not owners:
        return False
    holder = lock.owner()
    if holder in owners:
        return True
    return bool(owners & lock.waiters())


def _lift_package_pins(package: str, root: Path) -> list[_PinnedPackageFinder]:
    """Take this build's finder off ``sys.meta_path`` for the wait."""
    lifted: list[_PinnedPackageFinder] = []
    with package_import_lock:
        for finder in list(sys.meta_path):
            if (
                isinstance(finder, _PinnedPackageFinder)
                and finder.package == package
                and finder.root == root
            ):
                try:
                    sys.meta_path.remove(finder)
                except ValueError:
                    continue
                lifted.append(finder)
    return lifted


def _restore_package_pins(finders: list[_PinnedPackageFinder]) -> None:
    with package_import_lock:
        for finder in reversed(finders):
            if finder not in sys.meta_path:
                sys.meta_path.insert(0, finder)


def _loaded_from_other_folder(name: str, root: Path, keys: list[str]) -> Path | None:
    """Directory of a module under ``name`` that is not inside ``root``."""
    with package_import_lock:
        for key in (name, *keys):
            mod = sys.modules.get(key)
            if mod is None or not _should_replace(mod, root):
                continue
            loaded = _top_package_dir(mod, key)
            if loaded is not None:
                return loaded
    return None


def _reacquire_name_lock(
    lock: _PackageBuildLock, depth: int, timeout: float | None
) -> bool:
    """Take ``lock`` ``depth`` times. The first wait uses ``timeout``."""
    if depth <= 0:
        return True
    if timeout is None:
        acquired = lock.acquire()
    else:
        acquired = lock.acquire(timeout=max(0.0, timeout))
    if not acquired:
        return False
    for _ in range(depth - 1):
        if lock.acquire(timeout=0):
            continue
        while lock.depth_of_current() > 0:
            lock.release()
        return False
    return True


def _wait_for_import_or_name_lock(
    names: list[str],
    lock: _PackageBuildLock,
    timeout: float | None,
) -> bool | None:
    """``None`` when those imports release. ``False`` when ``timeout`` elapses.

    ``timeout is None`` waits until the import ends. This does not hold
    the name lock. An importer that takes the name lock is caught when
    this build takes the lock again and the generation moved.
    """
    deadline = None if timeout is None else time.monotonic() + timeout
    pending = list(names)
    while pending:
        if deadline is not None and time.monotonic() >= deadline:
            return False
        slice_for = 0.01
        if deadline is not None:
            slice_for = min(0.01, max(0.0, deadline - time.monotonic()))
        _wait_for_other_importers(pending, slice_for)
        pending = [item for item in pending if _other_thread_importing(item)]
    return None


def isolate_package_imports(package_dir: str | Path) -> None:
    """Reuse this directory's modules. Drop an idle module from another one.

    A cached ``sys.modules`` entry under the package name stays when its
    file resolves inside ``package_dir``. An idle entry from another
    directory is dropped so this build can load its own file. An entry
    another thread is still importing is left alone until that import
    releases. The wait is bounded by the build lock timeout and does not
    hold ``package_import_lock`` or the package-name lock. Holding the
    name lock across that wait deadlocks when the import calls ``build()``
    for the same name. The lock is released, then taken again. If that
    importer is blocked on the lock, or the folder is still the other one
    after the importer's ``build()``, this raises
    :class:`PackageImportConflict`. After a plain import releases, a
    module this folder also has, still loaded from the other directory,
    is the same error. A module this folder does not ship is dropped with
    the rest. Running out of time is :class:`BuildLockTimeout`. The other
    directory is not served. Stdlib and site-packages stay.
    """
    root = Path(package_dir).resolve()
    name = root.name
    timeout = _import_wait_seconds()
    deadline = None if timeout is None else time.monotonic() + timeout
    waited_exact: set[str] = set()
    while True:
        with package_import_lock:
            foreign: list[str] = []
            in_use: list[str] = []
            for key in list(sys.modules):
                if key != name and not key.startswith(name + "."):
                    continue
                mod = sys.modules.get(key)
                if mod is None or not _should_replace(mod, root):
                    continue
                foreign.append(key)
                if _other_thread_importing(key):
                    in_use.append(key)
                    if _exact_other_owner(key):
                        waited_exact.add(key)
            if not in_use:
                for key in foreign:
                    if key not in waited_exact or not _module_file_in_tree(
                        root, name, key
                    ):
                        continue
                    mod = sys.modules.get(key)
                    if mod is None:
                        continue
                    loaded = _top_package_dir(mod, key)
                    if loaded is None:
                        continue
                    raise PackageImportConflict(key, loaded, root)
                forgotten: list[Path] = []
                for key in sorted(
                    foreign, key=lambda item: item.count("."), reverse=True
                ):
                    forgotten.extend(_forget_module(key))
                if foreign:
                    importlib.invalidate_caches()
                    _clear_linecache(forgotten)
                return
        name_lock = package_build_lock(name)
        if _importers_need_name_lock(name_lock, in_use):
            loaded = _loaded_from_other_folder(name, root, in_use)
            if loaded is not None:
                raise PackageImportConflict(name, loaded, root)
        if (
            deadline is not None
            and timeout is not None
            and time.monotonic() >= deadline
        ):
            raise BuildLockTimeout(name, timeout)
        depth = name_lock.depth_of_current()
        finders: list[_PinnedPackageFinder] = []
        gen_before = name_lock.generation()
        outcome: bool | None = None
        reacquired = True
        if depth:
            finders = _lift_package_pins(name, root)
            for _ in range(depth):
                name_lock.release()
        try:
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining < 0:
                remaining = 0.0
            if depth:
                outcome = _wait_for_import_or_name_lock(in_use, name_lock, remaining)
            elif not _wait_for_other_importers(in_use, remaining):
                if timeout is not None:
                    raise BuildLockTimeout(name, timeout)
        finally:
            if depth:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining < 0:
                    remaining = 0.0
                reacquired = _reacquire_name_lock(
                    name_lock,
                    depth,
                    None if timeout is None else remaining,
                )
                if reacquired:
                    _restore_package_pins(finders)
        if depth and reacquired and name_lock.generation() - gen_before > 1:
            outcome = True
        elif depth and not reacquired and name_lock.generation() != gen_before:
            outcome = True
        if outcome is True:
            loaded = _loaded_from_other_folder(name, root, in_use)
            if loaded is not None:
                raise PackageImportConflict(name, loaded, root)
        if not reacquired:
            if timeout is None:
                name_lock.acquire()
                reacquired = True
            elif name_lock.acquire(timeout=0):
                reacquired = True
            else:
                raise BuildLockTimeout(name, timeout)
            if reacquired:
                _restore_package_pins(finders)
        if outcome is False and timeout is not None:
            raise BuildLockTimeout(name, timeout)


def _remember_source(mod: Any, path: Path) -> None:
    try:
        _source_tokens[mod] = path.read_bytes()
    except OSError:
        return


def _reload_module(mod: Any, path: Path) -> Any:
    """Re-exec ``path`` into ``mod`` without requiring parent packages."""
    linecache.cache.pop(str(path), None)
    linecache.checkcache(str(path))
    spec = getattr(mod, "__spec__", None)
    loader = getattr(spec, "loader", None) if spec is not None else None
    if loader is None:
        code = compile(path.read_bytes(), str(path), "exec")
        exec(code, mod.__dict__)
    else:
        loader.exec_module(mod)
    _remember_source(mod, path)
    return mod


def _detached_module_name(resolved: Path) -> str:
    digest = hashlib.sha256(str(resolved).encode()).hexdigest()[:32]
    return "ux_surface_" + digest


def begin_build_module_notes() -> None:
    """Start a per-build list of sys.modules entries this build creates."""
    stack = getattr(_build_notes, "stack", None)
    if stack is None:
        stack = []
        _build_notes.stack = stack
    stack.append([])


def end_build_module_notes() -> None:
    """Drop path-unique modules this build registered.

    The dotted route module stays in ``sys.modules``. A folder that is
    not on ``sys.path`` is loaded under that name by
    ``import_route_module`` and must still be there for the next build,
    which is what keeps the file from running again. The ``ux_surface_``
    name used for the scan is build-local and is dropped here. Whether
    the package name itself can be imported is a separate check.
    """
    stack = getattr(_build_notes, "stack", None)
    if not stack:
        return
    noted: list[tuple[str, Any]] = stack.pop()
    with package_import_lock:
        for key, mod in noted:
            if sys.modules.get(key) is not mod:
                continue
            if _is_on_stack(mod):
                continue
            if not key.startswith("ux_surface_"):
                continue
            _forget_module(key)


def _note_build_module(name: str, mod: Any) -> None:
    stack = getattr(_build_notes, "stack", None)
    if not stack:
        return
    stack[-1].append((name, mod))


def _register_module(name: str, resolved: Path) -> Any:
    """Insert a new module object. Caller holds ``package_import_lock``."""
    spec = importlib.util.spec_from_file_location(name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {resolved}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    _note_build_module(name, mod)
    return mod


def _exec_registered(name: str, mod: Any, resolved: Path) -> Any:
    """Run module code without holding ``package_import_lock``."""
    try:
        spec = getattr(mod, "__spec__", None)
        loader = getattr(spec, "loader", None) if spec is not None else None
        if loader is None:
            code = compile(resolved.read_bytes(), str(resolved), "exec")
            exec(code, mod.__dict__)
        else:
            loader.exec_module(mod)
    except Exception:
        with package_import_lock:
            if sys.modules.get(name) is mod:
                sys.modules.pop(name, None)
        raise
    _remember_source(mod, resolved)
    return mod


def refresh_cached_module(mod: Any, file: str | Path) -> Any:
    """Return the same module object. Re-exec only when ``file`` changed.

    ``build()`` leaves a route module in ``sys.modules``. The next build
    of that same folder reuses it, so the file runs once until its bytes
    change. A different folder with the same package name is removed by
    ``isolate_package_imports`` before this runs. Helper modules are not
    passed here and are not reloaded. The re-exec does not hold
    ``package_import_lock``.
    """
    resolved = Path(file).resolve()
    if _is_on_stack(mod):
        return mod
    try:
        current = resolved.read_bytes()
    except OSError:
        return mod
    with package_import_lock:
        previous = _source_tokens.get(mod)
        if previous is None:
            _source_tokens[mod] = current
            return mod
        if previous == current:
            return mod
    return _reload_module(mod, resolved)


def _load_named_or_detached(module: str, resolved: Path) -> tuple[str, Any, str]:
    """Choose a module object. Caller holds ``package_import_lock``.

    Returns ``(kind, module, sys.modules key)`` where kind is
    ``refresh`` or ``exec``. An on-stack or installed module whose file
    is a different directory stays in ``sys.modules``; the other file
    is loaded under a path-unique name.
    """
    cached = sys.modules.get(module)
    if cached is not None and _is_installed_module(cached):
        if _module_matches_file(cached, resolved):
            return "refresh", cached, module
        cached = None
    if cached is not None and _module_matches_file(cached, resolved):
        return "refresh", cached, module
    if cached is not None and _is_on_stack(cached):
        cached = None
    if cached is None and sys.modules.get(module) is not None and (
        _is_on_stack(sys.modules[module]) or _is_installed_module(sys.modules[module])
    ):
        key = _detached_module_name(resolved)
        existing = sys.modules.get(key)
        if existing is not None and _module_matches_file(existing, resolved):
            return "refresh", existing, key
        if existing is not None:
            _forget_module(key)
        return "exec", _register_module(key, resolved), key
    if cached is not None:
        forgotten = _forget_module(module)
        importlib.invalidate_caches()
        _clear_linecache(forgotten)
    return "exec", _register_module(module, resolved), module


def import_route_module(module: str, file: Path) -> Any:
    resolved = Path(file).resolve()
    with package_import_lock:
        kind, chosen, key = _load_named_or_detached(module, resolved)
    if kind == "refresh":
        if _is_installed_module(chosen):
            return chosen
        return refresh_cached_module(chosen, resolved)
    return _exec_registered(key, chosen, resolved)


def load_detached_module(file: str | Path) -> Any:
    """Load ``file`` under a name unique to its resolved path."""
    resolved = Path(file).resolve()
    key = _detached_module_name(resolved)
    with package_import_lock:
        existing = sys.modules.get(key)
        if existing is not None and _module_matches_file(existing, resolved):
            kind, chosen = "refresh", existing
        else:
            if existing is not None:
                _forget_module(key)
            chosen = _register_module(key, resolved)
            kind = "exec"
    if kind == "refresh":
        return refresh_cached_module(chosen, resolved)
    return _exec_registered(key, chosen, resolved)


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
        isolate_package_imports(parent)
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
                sys.modules.pop(module, None)
                if self.fail_closed:
                    raise
                continue

            try:
                rel = file.relative_to(base).with_suffix("")
            except ValueError:
                continue
            path = http_path(*rel.parts)
            bad_param = _non_identifier_param(path)
            if bad_param is not None:
                msg = (
                    f"DirectoryRoutes path parameter {bad_param!r} in {path} "
                    f"is not a Python identifier ({file})"
                )
                if self.fail_closed:
                    raise DirectoryRoutesError(msg)
                logger.warning("%s", msg)
                continue

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
