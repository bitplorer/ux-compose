"""Visitor identity: who a page's Caps are minted for.

Every visitor gets a subject. A logged-in user is ``scope["user"].identity``
(Starlette ``AuthenticationMiddleware``, the identity port). Anyone else is
an anonymous visitor ``anon:<random>`` that the server mints and signs into
an HttpOnly cookie. The client never chooses it: a missing, malformed or
forged cookie means a new visitor.

``VisitorMiddleware`` binds the subject for the request so ``wire.caps``
mints each page Cap with ``sub=<subject>``, and sets the cookie on the
response when it minted a new visitor. ``wire.boot`` resolves the same
subject as the Channel principal, so the Cap runs only for that visitor.

No ``ux_channel`` import here; the signing key is derived in ``wire/``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from contextvars import ContextVar
from http.cookies import CookieError, SimpleCookie
from typing import Any, Mapping, Optional

COOKIE = "uxc_visitor"
_ANON = "anon:"

_subject: ContextVar[Optional[str]] = ContextVar("ux_compose_visitor_subject", default=None)


def current_subject() -> Optional[str]:
    """Subject bound for this request, or None outside one."""
    return _subject.get()


def _sign(key: bytes, visitor: str) -> str:
    mac = hmac.new(key, visitor.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).rstrip(b"=").decode("ascii")


def new_visitor(key: bytes) -> tuple[str, str]:
    """``(subject, cookie value)`` for a fresh anonymous visitor."""
    visitor = _ANON + secrets.token_urlsafe(18)
    return visitor, f"{visitor}.{_sign(key, visitor)}"


def verify(key: bytes, value: Optional[str]) -> Optional[str]:
    """The visitor a cookie value names, or None unless its signature holds."""
    visitor, sep, mac = (value or "").rpartition(".")
    if not sep or not visitor.startswith(_ANON) or not visitor.isascii():
        return None
    return visitor if hmac.compare_digest(mac, _sign(key, visitor)) else None


def _cookie(headers: Any) -> Optional[str]:
    raw = [v.decode("latin-1") for k, v in headers if k.lower() == b"cookie"]
    jar = SimpleCookie()
    try:
        jar.load("; ".join(raw))
    except CookieError:
        return None
    morsel = jar.get(COOKIE)
    return morsel.value if morsel is not None else None


def identity(scope: Mapping[str, Any]) -> Optional[str]:
    """Logged-in subject from the identity port, else None."""
    user = scope.get("user")
    if user is not None and getattr(user, "is_authenticated", False):
        return str(user.identity)
    return None


def resolve(key: bytes, scope: Mapping[str, Any]) -> Optional[str]:
    """Subject for a request: the logged-in user, else a verified visitor."""
    return identity(scope) or verify(key, _cookie(scope.get("headers") or ()))


class VisitorMiddleware:
    """ASGI middleware: bind the request's subject; mint a visitor when absent."""

    def __init__(self, app: Any, *, key: bytes) -> None:
        self.app = app
        self.key = key

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        subject = resolve(self.key, scope)
        set_cookie: Optional[bytes] = None
        if subject is None and scope["type"] == "http":
            subject, value = new_visitor(self.key)
            attrs = f"{COOKIE}={value}; Path=/; HttpOnly; SameSite=Lax"
            if scope.get("scheme") == "https":
                attrs += "; Secure"
            set_cookie = attrs.encode("latin-1")

        async def send_with_cookie(message: dict) -> None:
            if set_cookie is not None and message["type"] == "http.response.start":
                message = {
                    **message,
                    "headers": [*message.get("headers", []), (b"set-cookie", set_cookie)],
                }
            await send(message)

        token = _subject.set(subject)
        try:
            await self.app(scope, receive, send_with_cookie)
        finally:
            _subject.reset(token)


__all__ = [
    "COOKIE",
    "VisitorMiddleware",
    "current_subject",
    "identity",
    "new_visitor",
    "resolve",
    "verify",
]
