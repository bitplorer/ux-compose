"""HTMX adapter — the one compose module that knows the htmx JS library.

Opt-in through ``build(use_htmx=True)`` or ``Document.use(Htmx())``. ux-dom
only renders ``hx-*`` attributes (ux-dom#140); the script runtime, partial
detection, middleware and route helper live here.

Scripts are pinned to exact npm versions with SRI. Each ``integrity`` is the
sha384 of that file in the npm tarball (tarball checked against the
registry's sha512). The Document's ``Csp`` runtime nonces the tags.
"""
from __future__ import annotations

import json
from functools import cached_property
from typing import Any, Mapping, Optional, Sequence
from urllib.parse import unquote

from ux_compose.dom import script

__all__ = ["Htmx", "HtmxDetails", "HtmxMiddleware", "HtmxRoutes", "is_partial"]

_CDN = "https://unpkg.com"
HTMX_JS = (
    f"{_CDN}/htmx.org@2.0.4/dist/htmx.min.js",
    "sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+",
)
IDIOMORPH_EXT_JS = (
    f"{_CDN}/idiomorph@0.7.4/dist/idiomorph-ext.min.js",
    "sha384-SsScJKzATF/w6suEEdLbgYGsYFLzeKfOA6PY+/C5ZPxOSuA+ARquqtz/BZz9JWU8",
)
SSE_EXT_JS = (
    f"{_CDN}/htmx-ext-sse@2.2.3/dist/sse.min.js",
    "sha384-Y4gc0CK6Kg+hmulDc6rZPJu0tqvk7EWlih0Oh+2OkAi1ZDlCbBDCQEE2uVk472Ky",
)


def _headers_from_scope(scope: dict) -> dict[str, str]:
    return {
        k.decode("latin-1").lower(): v.decode("latin-1")
        for k, v in scope.get("headers", [])
    }


class HtmxDetails:
    """HTMX request headers from a Request, a header mapping or an ASGI scope.

    A dict with a ``"type"`` key is read as an ASGI scope.
    """

    def __init__(self, request_or_scope: Any) -> None:
        headers: Any
        if isinstance(request_or_scope, dict) and "type" in request_or_scope:
            headers = _headers_from_scope(request_or_scope)
        elif hasattr(request_or_scope, "headers"):
            headers = request_or_scope.headers
        elif isinstance(request_or_scope, Mapping):
            headers = request_or_scope
        else:
            headers = {}
        self._headers = headers

    def _get_header_value(self, name: str) -> Optional[str]:
        headers = self._headers
        value = headers.get(name)
        if value is None:
            value = headers.get(name.lower())
        if not value:
            return None
        auto = headers.get(f"{name}-URI-AutoEncoded")
        if auto is None:
            auto = headers.get(f"{name.lower()}-uri-autoencoded")
        if auto == "true":
            value = unquote(value)
        return value

    def __bool__(self) -> bool:
        return self._get_header_value("HX-Request") == "true"

    @cached_property
    def boosted(self) -> bool:
        return self._get_header_value("HX-Boosted") == "true"

    @cached_property
    def current_url(self) -> Optional[str]:
        return self._get_header_value("HX-Current-URL")

    @cached_property
    def history_restore_request(self) -> bool:
        return self._get_header_value("HX-History-Restore-Request") == "true"

    @cached_property
    def partial(self) -> bool:
        """Fragment, not a full page. History restore needs the full page."""
        return bool(self) and not self.history_restore_request

    @cached_property
    def prompt(self) -> Optional[str]:
        return self._get_header_value("HX-Prompt")

    @cached_property
    def target(self) -> Optional[str]:
        return self._get_header_value("HX-Target")

    @cached_property
    def trigger(self) -> Optional[str]:
        return self._get_header_value("HX-Trigger")

    @cached_property
    def trigger_name(self) -> Optional[str]:
        return self._get_header_value("HX-Trigger-Name")

    @cached_property
    def triggering_event(self) -> Any:
        value = self._get_header_value("Triggering-Event") or self._get_header_value(
            "HX-Triggering-Event"
        )
        if value is not None:
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = None
        return value


def is_partial(request_or_scope: Any) -> bool:
    """True when the page GET should answer with the fragment, not the shell."""
    return HtmxDetails(request_or_scope).partial


class HtmxMiddleware:
    """Pure ASGI middleware: ``request.state.htmx`` is an :class:`HtmxDetails`."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            scope.setdefault("state", {})["htmx"] = HtmxDetails(scope)
        await self.app(scope, receive, send)


class Htmx:
    """Document runtime: pinned htmx scripts with SRI, partial policy, middleware.

    ``idiomorph`` (on by default) loads the morph swap extension; ``sse``
    loads ``htmx-ext-sse``. ``cdn=False`` emits no scripts (self-hosted).
    ``middleware=True`` mounts :class:`HtmxMiddleware`.
    """

    plugin_kind = "control"
    name = "htmx"

    def __init__(
        self,
        *,
        idiomorph: bool = True,
        sse: bool = False,
        cdn: bool = True,
        middleware: bool = False,
    ) -> None:
        self.idiomorph = idiomorph
        self.sse = sse
        self.cdn = cdn
        self.middleware = middleware

    def artifacts(self) -> Sequence[Any]:
        return ()

    def document_head(self) -> Sequence[Any]:
        return ()

    def document_body(self) -> Sequence[Any]:
        if not self.cdn:
            return []
        files = [HTMX_JS]
        if self.idiomorph:
            files.append(IDIOMORPH_EXT_JS)
        if self.sse:
            files.append(SSE_EXT_JS)
        return [
            script(src=src, integrity=sri, crossorigin="anonymous")
            for src, sri in files
        ]

    def wire(self, action: Any = None, **kwargs: Any) -> dict[str, Any]:
        """Pass-through: ``hx_*`` kwargs already render as ``hx-*`` attributes."""
        return dict(kwargs)

    def partial_policy(self, request: Any) -> str:
        # A bare header dict with a "type" key is not a scope: wrap only Requests.
        headers = getattr(request, "headers", None)
        source = request if hasattr(headers, "get") else {}
        return "partial" if is_partial(source) else "full"

    def mount(self, app: Any, **kwargs: Any) -> None:
        if self.middleware and hasattr(app, "add_middleware"):
            app.add_middleware(HtmxMiddleware)


class HtmxRoutes:
    """Mount handlers at ``{prefix}/{name}`` on a FastAPI-style router.

    ``@routes.get`` uses the function name; ``@routes.get("name")`` names it.
    """

    def __init__(self, api: Any, prefix: str = "") -> None:
        self.api = api
        self.prefix = (prefix or "").rstrip("/")

    def _route(self, verb: str, event: Any) -> Any:
        if isinstance(event, str):
            return getattr(self.api, verb)(f"{self.prefix}/{event}")
        return getattr(self.api, verb)(f"{self.prefix}/{event.__name__}")(event)

    def get(self, event: Any) -> Any:
        return self._route("get", event)

    def post(self, event: Any) -> Any:
        return self._route("post", event)

    def put(self, event: Any) -> Any:
        return self._route("put", event)

    def patch(self, event: Any) -> Any:
        return self._route("patch", event)

    def delete(self, event: Any) -> Any:
        return self._route("delete", event)
