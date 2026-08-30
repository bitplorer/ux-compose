"""Product app asset layout — this package owns it.

Disk convention (locked with create-app / build / ``/css`` mount)::

    assets/css/input.css                 # author source
    assets/static/file/css/output.css    # compiler output
    URL: /css/output.css

Does **not** mkdir database / upload / cache / templates — those are not
the CSS/JS product tree. Does **not** emit ``<link>`` tags (Document does).
Does **not** serve library JS (``/ux-dom/static/x_element.js`` stays on ux-dom).

``WebAssets.static.css`` keeps the historical nested folder so existing
trees and the compiler write the same place. Flatten later as one cut,
not a second SSoT.
"""
from __future__ import annotations

from dataclasses import dataclass
from email.utils import formatdate
from pathlib import Path
from typing import Any, Optional, Sequence, Union

__all__ = [
    "CSS_URL_PREFIX",
    "OUTPUT_CSS_NAME",
    "WebAssets",
]

CSS_URL_PREFIX = "/css"
OUTPUT_CSS_NAME = "output.css"
_INPUT_REL = Path("css") / "input.css"
_STATIC_CSS_REL = Path("static") / "file" / "css"
_STATIC_JS_REL = Path("static") / "file" / "js"


@dataclass(frozen=True)
class _Static:
    css: Path
    js: Path


class _StaticDirASGI:
    """Serve files under ``prefix`` from a directory. No FastAPI required.

    Used when the host is ``DirectoryASGI`` (no ``.mount``). Path traversal
    is rejected. Unknown paths fall through to ``inner``.
    """

    def __init__(self, inner: Any, directory: Path, prefix: str) -> None:
        self.inner = inner
        self.directory = Path(directory).resolve()
        self.prefix = prefix.rstrip("/") or CSS_URL_PREFIX

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") == "http":
            path = scope.get("path") or "/"
            if path == self.prefix or path.startswith(self.prefix + "/"):
                rel = path[len(self.prefix) :].lstrip("/")
                if not rel or ".." in Path(rel).parts:
                    await _http_send(send, 404, b"Not Found")
                    return
                target = (self.directory / rel).resolve()
                try:
                    target.relative_to(self.directory)
                except ValueError:
                    await _http_send(send, 404, b"Not Found")
                    return
                if not target.is_file():
                    await _http_send(send, 404, b"Not Found")
                    return
                stat = target.stat()
                last_mod = formatdate(stat.st_mtime, usegmt=True).encode()
                # ns + size: a rewrite that changes either moves the
                # validator the client HEAD-polls. Not a content hash.
                etag = f'W/"{stat.st_mtime_ns}-{stat.st_size}"'.encode()
                extra = [(b"last-modified", last_mod), (b"etag", etag)]
                method = (scope.get("method") or "GET").upper()
                ctype = (
                    b"text/css; charset=utf-8"
                    if target.suffix == ".css"
                    else b"application/octet-stream"
                )
                if method == "HEAD":
                    await _http_send(
                        send, 200, b"", ctype, extra_headers=extra, length=stat.st_size
                    )
                    return
                data = target.read_bytes()
                await _http_send(send, 200, data, ctype, extra_headers=extra)
                return
        if self.inner is None:
            await _http_send(send, 404, b"Not Found")
            return
        await self.inner(scope, receive, send)


async def _http_send(
    send: Any,
    status: int,
    body: bytes,
    content_type: bytes = b"text/plain; charset=utf-8",
    extra_headers: Optional[Sequence[tuple[bytes, bytes]]] = None,
    length: Optional[int] = None,
) -> None:
    headers = [
        (b"content-type", content_type),
        (b"content-length", str(len(body) if length is None else length).encode()),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": headers,
        }
    )
    await send({"type": "http.response.body", "body": body, "more_body": False})


class WebAssets:
    """App-local CSS/JS folders. Author API matches the old constructor.

    ::

        from ux_compose import WebAssets
        webassets = WebAssets(base_dir=ASSETS_DIR, dry_run=False)
        webassets.static.css   # assets/static/file/css
        webassets.output_css   # .../output.css
        webassets.css_href     # /css/output.css
    """

    def __init__(
        self,
        base_dir: Union[str, Path],
        sub_dir: Union[str, Path] = "",
        *,
        dry_run: bool = True,
    ) -> None:
        base = Path(base_dir)
        if base.is_file():
            base = base.parent
        if sub_dir:
            base = base / Path(sub_dir)
        self.dir = base.resolve()
        self.static = _Static(
            css=self.dir / _STATIC_CSS_REL,
            js=self.dir / _STATIC_JS_REL,
        )
        self.input_css = self.dir / _INPUT_REL
        self.output_css = self.static.css / OUTPUT_CSS_NAME
        self.css_href = f"{CSS_URL_PREFIX}/{OUTPUT_CSS_NAME}"
        if not dry_run:
            self.ensure()

    def ensure(self) -> "WebAssets":
        self.static.css.mkdir(parents=True, exist_ok=True)
        self.static.js.mkdir(parents=True, exist_ok=True)
        self.input_css.parent.mkdir(parents=True, exist_ok=True)
        return self

    def mount_css(self, asgi: Any, *, url: str = CSS_URL_PREFIX) -> Any:
        """Attach compiler output at ``/css``.

        FastAPI/Starlette (``asgi.mount``): mutates in place, returns ``asgi``.
        Pure ASGI (``DirectoryASGI``): returns a wrapper that serves the
        directory then falls through. ``asgi is None`` raises — silent skip
        was the leftover that 404'd stylesheets.
        """
        if asgi is None:
            raise TypeError(
                "WebAssets.mount_css requires an ASGI app. "
                "host=asgi builds DirectoryASGI; host=fastapi builds FastAPI."
            )
        self.ensure()
        if hasattr(asgi, "mount"):
            try:
                from starlette.staticfiles import StaticFiles
            except Exception as e:
                raise RuntimeError(
                    "WebAssets.mount_css needs starlette/fastapi StaticFiles "
                    "to mount on this host."
                ) from e
            asgi.mount(
                url,
                StaticFiles(directory=str(self.static.css), check_dir=False),
                name="css",
            )
            return asgi
        if not callable(asgi):
            raise TypeError(
                f"WebAssets.mount_css: {type(asgi).__name__} is not a "
                "FastAPI app and not a callable ASGI app"
            )
        return _StaticDirASGI(asgi, self.static.css, url)

    @classmethod
    def from_app_root(
        cls, root: Union[str, Path], *, dry_run: bool = True
    ) -> "WebAssets":
        """Layout under ``<root>/assets`` (create-app tree)."""
        return cls(base_dir=Path(root) / "assets", dry_run=dry_run)
