"""Fragment Cap live-client — public URL refs when an author opts in.

Cap Host stays on cek-runtime via Channel. This module does **not** import
``ux_channel``, mint Caps, or copy the channel client. It emits the same
public URLs Channel already serves:

    /ux-channel/static/ux-channel.js
    /ux-channel/static/ux-bridge.js   (optional)
    body data-channel-endpoint="/ux-channel/action"

Product path is ``Document.use(XElement(), Csp.auto(), Channel.optional())``
(the ``ux_dom.runtime`` alias). This helper is **not** the Document-absent
primary: ``build()`` does not auto-attach it when ``document=None``.

Never wrap HTML-string fragments with a synthesized ux-dom Document (a
positional ``str`` becomes script ``src``).
"""
from __future__ import annotations

import re
from typing import Any

CHANNEL_JS_URL = "/ux-channel/static/ux-channel.js"
CHANNEL_BRIDGE_URL = "/ux-channel/static/ux-bridge.js"
CHANNEL_ENDPOINT = "/ux-channel/action"
LIVE_CLIENT_ATTR = b"data-uxcompose-live-client"
CHANNEL_ENDPOINT_ATTR = b"data-channel-endpoint"
BODY_CLOSE = b"</body>"
HTML_CLOSE = b"</html>"
_BODY_OPEN = re.compile(br"(?i)<body(\s[^>]*)?>")
_ATTACH_FLAG = "_uxcompose_live_client"


def is_html_content_type(value: bytes) -> bool:
    return b"text/html" in value.lower()


def live_client_script_tags(*, bridge: bool = True) -> str:
    """Script tags that load the Channel client. Pin public URLs only."""
    tags = [
        f'<script src="{CHANNEL_JS_URL}" defer data-uxcompose-live-client></script>',
    ]
    if bridge:
        tags.append(f'<script src="{CHANNEL_BRIDGE_URL}" defer></script>')
    return "".join(tags)


def _already_wired(page: bytes) -> bool:
    return LIVE_CLIENT_ATTR in page or CHANNEL_JS_URL.encode("ascii") in page


def _is_complete_html(page: bytes) -> bool:
    low = page.lstrip().lower()
    return (
        low.startswith(b"<!doctype")
        or low.startswith(b"<html")
        or b"<body" in low
        or BODY_CLOSE in low
    )


def _stamp_endpoint(page: bytes) -> bytes:
    if CHANNEL_ENDPOINT_ATTR in page:
        return page
    match = _BODY_OPEN.search(page)
    if not match:
        return page
    attrs = match.group(1) or b""
    repl = b'<body data-channel-endpoint="' + CHANNEL_ENDPOINT.encode("ascii") + b'"'
    if attrs:
        repl += attrs
    repl += b">"
    return page[: match.start()] + repl + page[match.end() :]


def insert_live_client(page: bytes, markup: bytes | None = None) -> bytes:
    """Put Channel client tags into HTML, once.

    Complete documents (``<html>`` / ``</body>``) get an insert before
    ``</body>`` — never a second shell. Fragments without a body get a
    **string** HTML shell (not a ux-dom ``Document``). Idempotent if the
    live-client marker or ``ux-channel.js`` is already present.
    """
    if _already_wired(page):
        return page
    script = markup if markup is not None else live_client_script_tags().encode("utf-8")
    if _is_complete_html(page):
        stamped = _stamp_endpoint(page)
        idx = stamped.lower().rfind(BODY_CLOSE)
        if idx >= 0:
            return stamped[:idx] + script + stamped[idx:]
        idx = stamped.lower().rfind(HTML_CLOSE)
        if idx >= 0:
            return stamped[:idx] + script + stamped[idx:]
        return stamped + script
    return (
        b'<!DOCTYPE html><html><body data-channel-endpoint="'
        + CHANNEL_ENDPOINT.encode("ascii")
        + b'">'
        + page
        + script
        + b"</body></html>"
    )


class LiveClientMiddleware:
    """Insert Channel live-client tags into HTML. Fragment GET, not Document.use."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.script = live_client_script_tags().encode("utf-8")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state: dict[str, Any] = {"html": False, "buf": []}

        async def send_wrapper(message):
            kind = message["type"]
            if kind == "http.response.start":
                headers = list(message.get("headers", []))
                html = any(
                    key.lower() == b"content-type" and is_html_content_type(value)
                    for key, value in headers
                )
                if html:
                    headers = [
                        (key, value)
                        for key, value in headers
                        if key.lower() != b"content-length"
                    ]
                state["html"] = html
                message = {**message, "headers": headers}
            elif kind == "http.response.body" and state["html"]:
                state["buf"].append(message.get("body", b""))
                if message.get("more_body"):
                    return
                body = insert_live_client(b"".join(state["buf"]), self.script)
                message = {**message, "body": body, "more_body": False}
            await send(message)

        await self.app(scope, receive, send_wrapper)


def attach_live_client(asgi_app: Any) -> Any:
    """Wrap HTML responses with the Channel live client. Idempotent.

    FastAPI/Starlette: ``add_middleware`` so ``.mount`` / routes stay on the
    process object (CSS mount happens after ``build()``). DirectoryASGI: wrap
    the ASGI callable.
    """
    if asgi_app is None:
        return asgi_app
    if getattr(asgi_app, _ATTACH_FLAG, False):
        return asgi_app
    if hasattr(asgi_app, "add_middleware"):
        asgi_app.add_middleware(LiveClientMiddleware)
        setattr(asgi_app, _ATTACH_FLAG, True)
        return asgi_app
    wrapped = LiveClientMiddleware(asgi_app)
    setattr(wrapped, _ATTACH_FLAG, True)
    return wrapped


__all__ = [
    "CHANNEL_JS_URL",
    "CHANNEL_BRIDGE_URL",
    "CHANNEL_ENDPOINT",
    "live_client_script_tags",
    "insert_live_client",
    "LiveClientMiddleware",
    "attach_live_client",
]
