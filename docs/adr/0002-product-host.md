# ADR 0002 — Product FastAPI host (Clock A)

> **Diátaxis:** ADR · **Layer:** ux-compose
> Map: [../INDEX.md](../INDEX.md). Spec: [../reference/host.md](../reference/host.md).

**Status:** accepted
**Date:** 2026-08-26
**Amended:** 2026-08-26 — payload type picks media type (JSON / stream / HTML).

## Context

Page HTTP was scattered: thin FastAPI adapter returned raw trees, scaffold
`Hello.get` wrapped Document, `document.mount` lived in `main()`, Channel
booted headless then no-op'd on the real ASGI app, leftover `DirectoryRouter`
defaulted to `StreamingRoute`, FastAPI `default_response_class=HTMLResponse`
would have stolen JSON author routes, and page endpoints always wrapped
`HTMLResponse` so a `dict` from `render()` became `str(dict)` HTML. Two
scanners, two path laws.

ux-dom already had the right *spirit*: `html_response` / `streaming_response`
wrap trees and pass everything else through. Compose must keep the L1 HTML
**string** path (`str` is HTML, never JSON, never a stream).

## Decision

1. FastAPI is the product process (`host="auto"|"fastapi"`). DirectoryASGI is
   the no-Starlette degrade, not a peer product.
2. `routing/fastapi.py` owns page GET. Units have no HTTP verbs. Path params
   come from the Request.
3. `routing/host.py` owns order: `open()` then `bind()` (Document.mount + pages).
4. `App.boot("auto")` is Level 1. Channel binds in `build()` after the process
   exists; `use_channel(asgi_app=)` rebinds if a headless wire landed first.
5. One path law in `http_path`: `index.py`/`route.py` → `/`, `[param]` → `{param}`.
6. **Payload type picks media type** — not `Accept`, not a route class, not
   `default_response_class`:

   | Return | Container |
   |--------|-----------|
   | tag / `str` / bytes | `HTMLResponse` + Document wrap |
   | `dict` / list-of-dicts | JSON (FastAPI encodes) |
   | generator / async generator | `StreamingResponse` |
   | Response subclass | as-is |

   Trees are **not** auto-streamed (`Content-Length` + CSP stamp before first
   byte). Leftover `StreamingRoute` is not the product path.

7. `host="batteries"` fails closed.

## Consequences

- Authors: `build(PACKAGE, document=document)` — no `HTMLResponse`, no
  `Hello.get`, no `JSONResponse` for a dict, no `StreamingResponse` for a
  generator.
- Maintainers: GET `/hello` is `routing/fastapi.py`; process order is
  `routing/host.py`; predicates are `routing/core.py`. Spec:
  [../reference/host.md](../reference/host.md).
- Extra APIs (`/api/…`, `/act/…`) are FastAPI routes on the process `build()`
  returned, not methods on the page class.
- Leftover `DirectoryRouter` stays in ux-dom for demosite only.
- New media types follow the protocol in the spec §9 (predicate + both hosts
  + test + this ADR's spec page). Conflicts get **ADR 0003**, not a second
  pipeline.

## Non-goals

- Content negotiation (`Accept: application/json` on GET /hello).
- Auto-streaming every ux-dom tree.
- HTTP verbs on Components.
- A compose-owned HTML builder when ux-dom is absent.
