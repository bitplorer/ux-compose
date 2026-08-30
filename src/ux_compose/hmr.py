"""Dev HMR (delivery layer — not Document.use).

Two clocks in this module, both on:

  process reload   uvicorn --reload on ``*.py`` (owned by serve)
                   new worker, cold import, new page class

  browser HMR      WebSocket at ``/__uxcompose/hmr``
                   reconnect after worker death → health → morph page units
                   location.reload() only if morph fails
                   banner if the ui worker stays down; keep polling
                   live-reload client inserted into HTML (dev middleware)

CSS is not a file watcher here. ``uxcompose serve`` may start a sibling
Tailwind ``--watch`` that writes ``output.css``. This client HEAD-polls
``/css/output.css`` and swaps the stylesheet. The Python worker does not
die for a CSS save.

A page unit is a Python class in the worker. This is live reload, not
module-graph swap. This module does not watch files and does not spawn
the compiler.
"""
from __future__ import annotations

import importlib
import os
from typing import Any, Callable

HMR_PATH = "/__uxcompose/hmr"
HMR_ATTR = b"data-uxcompose-hmr"
BODY_CLOSE = b"</body>"
APP_ENV = "UXCOMPOSE_APP"

# First open is silent. Unclean close (worker died) reconnects, waits until
# this URL is 200, then morphs page-unit ids. location.reload() is the
# fallback. close(1000) on beforeunload is a user navigation — do not bounce.
CLIENT_JS = r"""
(function () {
  if (window.__UXCOMPOSE_HMR__) return;
  window.__UXCOMPOSE_HMR__ = true;

  function wsUrl() {
    var u = new URL("__uxcompose/hmr", location.href);
    u.protocol = location.protocol === "https:" ? "wss:" : "ws:";
    return u.toString();
  }

  function hardReload() {
    location.reload();
  }

  function showFail(msg) {
    var el = document.getElementById("uxcompose-hmr-fail");
    if (!el) {
      el = document.createElement("div");
      el.id = "uxcompose-hmr-fail";
      el.setAttribute("role", "status");
      el.style.cssText = "position:fixed;z-index:2147483647;left:0;right:0;bottom:0;padding:10px 14px;background:#1c1917;color:#fafaf9;font:13px/1.4 ui-sans-serif,system-ui,sans-serif";
      document.documentElement.appendChild(el);
    }
    el.textContent = msg;
  }

  function hideFail() {
    var el = document.getElementById("uxcompose-hmr-fail");
    if (el && el.parentNode) el.parentNode.removeChild(el);
  }

  function snapshotUi() {
    var a = document.activeElement;
    return {
      id: a && a.id ? a.id : "",
      name: a && a.getAttribute ? (a.getAttribute("name") || "") : "",
      tag: a && a.tagName ? String(a.tagName).toLowerCase() : "",
      start: a && typeof a.selectionStart === "number" ? a.selectionStart : null,
      end: a && typeof a.selectionEnd === "number" ? a.selectionEnd : null,
      x: window.scrollX || 0,
      y: window.scrollY || 0
    };
  }

  function restoreUi(s) {
    try { window.scrollTo(s.x, s.y); } catch (e) {}
    var el = s.id ? document.getElementById(s.id) : null;
    if (!el && s.name && s.tag) {
      el = document.querySelector(s.tag + '[name="' + String(s.name).replace(/"/g, "") + '"]');
    }
    if (!el) return;
    try { el.focus(); } catch (e) {}
    if (s.start != null && typeof el.setSelectionRange === "function") {
      try { el.setSelectionRange(s.start, s.end); } catch (e) {}
    }
  }

  function morphLive(html) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    if (!doc || !doc.body) throw new Error("hmr-parse");
    if (doc.title) document.title = doc.title;
    if (window.Idiomorph && typeof window.Idiomorph.morph === "function") {
      window.Idiomorph.morph(document.body, doc.body);
      return;
    }
    var fresh = doc.body.querySelectorAll("[id]");
    var n = 0;
    for (var i = 0; i < fresh.length; i++) {
      var id = fresh[i].getAttribute("id");
      if (!id) continue;
      var live = document.getElementById(id);
      if (!live || live === document.body || live === document.documentElement) continue;
      if (live.getAttribute && live.getAttribute("data-uxcompose-hmr") !== null) continue;
      live.replaceWith(fresh[i].cloneNode(true));
      n += 1;
    }
    if (!n) throw new Error("hmr-no-target");
  }

  function softReload() {
    var snap = snapshotUi();
    fetch(location.href, { cache: "no-store", credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) throw new Error("hmr-http");
        var ct = r.headers.get("content-type") || "";
        if (ct.indexOf("text/html") === -1) throw new Error("hmr-type");
        return r.text();
      })
      .then(function (html) {
        morphLive(html);
        restoreUi(snap);
      })
      .catch(hardReload);
  }

  function waitUntilWorkerServes(onReady) {
    var n = 0;
    var tick = function () {
      fetch(location.href, { cache: "no-store", credentials: "same-origin" })
        .then(function (r) {
          if (r.ok) { hideFail(); onReady(); }
          else retry();
        })
        .catch(retry);
    };
    var retry = function () {
      n += 1;
      if (n === 20) showFail("uxcompose: waiting for ui worker");
      setTimeout(tick, 100);
    };
    tick();
  }

  var current;
  function connect(isReconnect) {
    var ws;
    try { ws = new WebSocket(wsUrl()); }
    catch (e) {
      setTimeout(function () { connect(true); }, 400);
      return;
    }
    current = ws;
    ws.onopen = function () {
      if (isReconnect) waitUntilWorkerServes(softReload);
    };
    ws.onclose = function (ev) {
      if (ev.code === 1000) return;
      setTimeout(function () { connect(true); }, 400);
    };
    ws.onerror = function () {
      try { ws.close(); } catch (e) {}
    };
  }

  function swapStylesheets() {
    var nodes = document.querySelectorAll('link[rel="stylesheet"]');
    for (var i = 0; i < nodes.length; i++) {
      var href = nodes[i].getAttribute("href") || "";
      if (href.indexOf("output.css") === -1) continue;
      var u = new URL(href, location.href);
      u.searchParams.set("t", String(Date.now()));
      var next = nodes[i].cloneNode(true);
      next.setAttribute("href", u.pathname + u.search);
      (function (old) {
        next.onload = function () {
          if (old && old.parentNode) old.parentNode.removeChild(old);
        };
      })(nodes[i]);
      nodes[i].parentNode.insertBefore(next, nodes[i].nextSibling);
    }
  }

  function watchCss() {
    var href = "/css/output.css";
    var last = "";
    var missing = false;
    var tick = function () {
      fetch(href, { method: "HEAD", cache: "no-store", credentials: "same-origin" })
        .then(function (r) {
          if (!r.ok) { missing = true; return; }
          var tag = r.headers.get("etag") || r.headers.get("last-modified") || "";
          if (!tag) return;
          if ((last && tag !== last) || (missing && last !== tag)) swapStylesheets();
          missing = false;
          last = tag;
        })
        .catch(function () { missing = true; });
      setTimeout(tick, 400);
    };
    tick();
  }

  window.addEventListener("beforeunload", function () {
    try { if (current) current.close(1000); } catch (e) {}
  });
  connect(false);
  watchCss();
})();
"""


def client_script_tag() -> str:
    """HTML tag that boots the live-reload client. Prefer attach_hmr."""
    return f'<script {HMR_ATTR.decode("ascii")}>\n{CLIENT_JS}\n</script>'


def is_html_content_type(value: bytes) -> bool:
    return b"text/html" in value.lower()


def insert_hmr_client(page: bytes, script: bytes) -> bytes:
    """Put the live-reload client into an HTML page, once, before </body>.

    This is not a general HTML injector. It is how the browser finds
    ``/__uxcompose/hmr``. Idempotent if ``data-uxcompose-hmr`` is already there.
    Pages without ``</body>`` are left unchanged.
    """
    if HMR_ATTR in page:
        return page
    idx = page.lower().rfind(BODY_CLOSE)
    if idx < 0:
        return page
    return page[:idx] + script + page[idx:]


def load_asgi(app_ref: str) -> Any:
    """Import ``module:attr`` (the uvicorn target)."""
    if ":" not in app_ref:
        raise ValueError(f"ASGI path must be module:attr, got {app_ref!r}")
    mod_name, attr = app_ref.split(":", 1)
    obj: Any = importlib.import_module(mod_name)
    for part in attr.split("."):
        obj = getattr(obj, part)
    return obj


def asgi_factory() -> Any:
    """uvicorn factory: attach on every worker so --reload remounts the WS."""
    spec = os.environ.get(APP_ENV, "app:asgi")
    return attach_hmr(load_asgi(spec))


def _has_route(asgi_app: Any, path: str) -> bool:
    router = getattr(asgi_app, "router", asgi_app)
    for route in getattr(router, "routes", []) or []:
        if getattr(route, "path", None) == path:
            return True
    return False


def _patch_ws_annotation(endpoint: Callable) -> None:
    annotations = dict(getattr(endpoint, "__annotations__", {}) or {})
    try:
        from fastapi import WebSocket as Ws
    except ImportError:
        try:
            from starlette.websockets import WebSocket as Ws
        except ImportError:
            return
    annotations["websocket"] = Ws
    endpoint.__annotations__ = annotations


def _bind_hmr_socket(asgi_app: Any, *, path: str = HMR_PATH) -> bool:
    if _has_route(asgi_app, path):
        return True

    async def hmr_endpoint(websocket: Any) -> None:
        await websocket.accept()
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            return

    _patch_ws_annotation(hmr_endpoint)

    if hasattr(asgi_app, "add_api_websocket_route"):
        asgi_app.add_api_websocket_route(path, hmr_endpoint, name="uxcompose_hmr")
        return True
    if hasattr(asgi_app, "add_websocket_route"):
        asgi_app.add_websocket_route(path, hmr_endpoint, name="uxcompose_hmr")
        return True
    if hasattr(asgi_app, "websocket"):
        asgi_app.websocket(path)(hmr_endpoint)
        return True
    return False


class HmrClientMiddleware:
    """Insert the live-reload client into HTML responses. Dev, not Document.use."""

    def __init__(self, app: Any, script_html: str) -> None:
        self.app = app
        self.script = script_html.encode("utf-8")

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
                body = insert_hmr_client(b"".join(state["buf"]), self.script)
                message = {**message, "body": body, "more_body": False}
            await send(message)

        await self.app(scope, receive, send_wrapper)


def attach_hmr(asgi_app: Any, *, path: str = HMR_PATH) -> Any:
    """Mount browser HMR. No file watcher. uvicorn --reload owns ``*.py``."""
    if not _bind_hmr_socket(asgi_app, path=path):
        return asgi_app
    return HmrClientMiddleware(asgi_app, client_script_tag())


__all__ = [
    "APP_ENV",
    "HMR_PATH",
    "CLIENT_JS",
    "client_script_tag",
    "insert_hmr_client",
    "load_asgi",
    "asgi_factory",
    "attach_hmr",
]
