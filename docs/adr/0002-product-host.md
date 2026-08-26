# ADR 0002 — Product FastAPI host (Clock A)

> **Diátaxis:** ADR · **Layer:** ux-compose
> Map: [../INDEX.md](../INDEX.md).

**Status:** accepted
**Date:** 2026-08-26

## Context

Page HTTP was scattered: thin FastAPI adapter returned raw trees, scaffold
`Hello.get` wrapped Document, `document.mount` lived in `main()`, Channel
booted headless then no-op'd on the real ASGI app, and leftover
`DirectoryRouter` defaulted to `StreamingRoute`. Two scanners, two path laws.

## Decision

1. FastAPI is the product process (`host="auto"|"fastapi"`). DirectoryASGI is
   the no-Starlette degrade, not a peer product.
2. `routing/fastapi.py` owns page GET: resolve → render → document() →
   `html_response`. Units have no HTTP verbs.
3. `routing/host.py` owns order: `open()` then `bind()` (Document.mount + pages).
4. `App.boot("auto")` is Level 1. Channel binds in `build()` after the process
   exists; `use_channel(asgi_app=)` rebinds if a headless wire landed first.
5. One path law in `http_path`: `index.py`/`route.py` → `/`, `[param]` → `{param}`.
6. Streaming is a return value (`StreamingResponse(tree)`), not a route class.
7. Media type is the payload, not `Accept`. `dict` / list-of-dicts → JSON
   (FastAPI encodes). Tree / `str` / bytes → HTML + Document wrap. Response
   subclass → pass through. Same spirit as ux-dom `html_response`.

## Consequences

- Authors: `build(PACKAGE, document=document)` — no `HTMLResponse`, no `Hello.get`.
- Maintainers: GET `/hello` is `routing/fastapi.py`; process order is `routing/host.py`.
- Leftover `DirectoryRouter` stays in ux-dom for demosite only.
