# Product host — Clock A (reference)

> **Diátaxis:** reference · **Canonical:** `docs/reference/host.md` · **Layer:** ux-compose
> Map: [INDEX.md](../INDEX.md). Decision: [adr/0002-product-host.md](../adr/0002-product-host.md).
> Ownership: [FLOW.md](../FLOW.md) §7. How-to: [guides/HOST.md](../guides/HOST.md).

This is the fitness function for page HTTP. If code and this page disagree,
**code wins** — then this page is updated in the same change.

Authors never implement this. Maintainers open this file (then the two
Python modules it names) to answer “what happens on GET /hello?”.

---

## 1. Two clocks (do not mix)

| Clock | Trigger | Pipeline | Owner |
|-------|---------|----------|-------|
| **A — page GET** | Browser / agent hits a filesystem URL | resolve → `render()` → payload dispatch | `routing/fastapi.py` |
| **B — live action** | `@action` / Channel Intent | mutate → Ops → morph | ux-behavior + `wire/` |

Clock A serves the document. Clock B patches it. A page unit has **no HTTP
verbs**. Extra JSON/POST APIs live on the FastAPI process, not on the class.

---

## 2. Process order

```text
host.open(name, host)          # FastAPI() or DirectoryASGI
App.boot(..., level=1)         # Behavior only
_attach_document(...)          # author's Document SSoT
App.use_channel(asgi_app=)     # after the process exists
DirectoryRoutes.discover()     # one path law
host.bind(...)                 # document.mount then page routes
```

Orchestra: `ux_compose.build.build`. Order owner: `routing/host.py`.

`App.boot("auto")` is **Level 1**. Channel never boots headless on auto —
`Behavior.attach` is idempotent on `_wire`, so a headless Channel would never
land on FastAPI. `use_channel(asgi_app=)` rebinds if a headless wire landed
first (tests / explicit `level=2`).

---

## 3. Payload law (media type)

**The return value picks the HTTP container. Not `Accept`. Not a route class.
Not FastAPI `default_response_class`.**

Same spirit as ux-dom `html_response` / `streaming_response` (wrap trees, pass
the rest through). Compose adds the L1 HTML-string path: a `str` is HTML, never JSON.

| `render()` / handler returns | HTTP | Document wrap | CSP stamp |
|------------------------------|------|---------------|-----------|
| ux-dom tag / Document / Component / HTML `str` / `bytes` | `HTMLResponse` | yes | yes (ux-dom `prepare_html_body`) |
| `dict` or list-of-dicts | JSON (`application/json`) | **no** | n/a |
| sync / async generator, or `__aiter__` that is not a tree | `StreamingResponse` (`text/html`) | **no** | only if ux-dom stream prepare runs |
| `HTMLResponse` / `JSONResponse` / `StreamingResponse` / `Response` | as-is | **no** | whatever that object already did |
| `None` | empty HTML | yes | — |

Predicates (host-agnostic, `routing/core.py`):

- `is_json_payload` — `dict`, or a `list`/`tuple` of dicts (including `[]`)
- `is_stream_payload` — `inspect.isgenerator` / `isasyncgen`, or `__aiter__`
  without `__render__` / `children`
- **`str` is iterable. It is not a stream.** `"<div>"` stays buffered HTML
  with `Content-Length`

Dispatch (`routing/fastapi.py` `_as_http_response`):

1. already a Response **or** JSON payload → return as-is (FastAPI JSON-encodes dicts)
2. stream payload → `StreamingResponse` (ux-dom if it accepts the body, else Starlette)
3. else → `document(tree)` then `HTMLResponse`

DirectoryASGI (`host="asgi"`) uses the same predicates. Streams go out as
chunked ASGI `more_body`. JSON is `json.dumps`. HTML is `to_html_bytes`.

### Why trees are not auto-streamed

A complete document wants `Content-Length` and a CSP nonce **before** the first
byte (`stamp_tree` then serialize). Auto-wrapping every tag in `StreamingResponse`
drops both. Leftover ux-dom `StreamingRoute` as `route_class` is **not** the
product path.

To stream a tag tree, opt in:

```python
return tree.__async_render__(pretty=False)   # async gen → stream
# or
return StreamingResponse(tree)               # ux-dom stream prepare + CSP
```

---

## 4. Path law (one scanner)

`http_path(*segments)` in `routing/core.py`. Class name is never in the URL.

| File under `routes/` | URL |
|----------------------|-----|
| `index.py` / `route.py` | folder prefix or `/` |
| `hello.py` | `/hello` |
| `shop/index.py` | `/shop` |
| `shop/[sku].py` | `/shop/{sku}` |
| `[id]/page.py` | `/{id}/page` |
| `_private.py`, `(group)/…` | skipped |

Page unit = renderable class whose name matches the file stem
(`hello.py` → `Hello`). `[sku].py` stem-key is `sku` → class `Sku`.
Extra renderables in the same file are fragments (no URL). HTTP verbs on
the class are ignored. Path params come from the Request, passed into
`render(**path_params)` when the signature accepts them.

---

## 5. Created-app layout

`uxcompose create-app shop` emits:

```text
shop/
├── app.py                 composition root — build() only
├── document.py            Document SSoT (.use(XElement, Csp) + page())
├── settings.py            BASE_DIR, DEBUG, WebAssets
├── requirements.txt
├── README.md
├── routes/
│   ├── __init__.py
│   └── hello.py           page unit — render() fragment, no get()
└── assets/
    ├── css/input.css
    └── static/file/{css,js}/
```

| File | Owns | Must not |
|------|------|----------|
| `settings.py` | env, disk folders | Channel, Document |
| `document.py` | one Document | `ux_channel`, page routes |
| `app.py` | `build(host=, live=, level=, document=)` | HTML wrap, HTTP verbs |
| `routes/*.py` | `render()` + `@action` | `get()`, `HTMLResponse`, Document.mount |

Gone: `Hello.get()`, `document.mount(asgi)` in `main()`, class HTTP verbs,
`host="batteries"` / leftover `DirectoryRouter`.

---

## 6. File map (where to edit)

| Question | File |
|----------|------|
| What happens on GET /hello? | `src/ux_compose/routing/fastapi.py` |
| Process order? | `src/ux_compose/routing/host.py` |
| Path / stem / JSON / stream predicates? | `src/ux_compose/routing/core.py` |
| No-Starlette degrade? | `src/ux_compose/routing/asgi.py` |
| Orchestra? | `src/ux_compose/build.py` |
| Channel attach? | `src/ux_compose/wire/boot.py` only |
| Scaffold? | `src/ux_compose/scaffold.py` |
| Fitness tests? | `tests/unit/test_host.py` |

`routing/adapters/` are thin re-export shims. Do not put logic there.

Invisible Strategy: authors import `build` / `App.mount`. They do not import
`routing.fastapi` / `routing.host`. Maintainers always do.

---

## 7. Host values

| `host=` | Process | Fail |
|---------|---------|------|
| `auto` | FastAPI if importable, else DirectoryASGI | never |
| `fastapi` | FastAPI | closed if FastAPI missing |
| `asgi` | DirectoryASGI (no Starlette) | never |
| `starlette` | alias of `auto` | — |
| `batteries` / `directory_router` | — | `ProductBatteriesRejected` |

FastAPI is **not** given `default_response_class=HTMLResponse`. Author
`@asgi.get("/api/...")` returning a dict stays JSON.

---

## 8. Isolation / Document / Channel

- Product modules never import `ux_channel`. Door: `App.use_channel(asgi_app=)`.
- Cold import never pulls `wire/`.
- Document is SSoT: one `Document` in `document.py`. `build(document=)` attaches
  it. Dual-Document is a doctor fail.
- `document.mount(asgi)` (CSP middleware, package static) runs in `host.bind`
  on FastAPI only. DirectoryASGI wraps `document()` on the HTML body; doctor
  reports CSP middleware is not attached.
- HTMX is opt-in (`build(use_htmx=True)` / `Document.use(Htmx())`).

---

## 9. Future protocol (do not fragment)

Adding a media type (SSE, `FileResponse`, `RedirectResponse`, …):

1. Add a **predicate** in `routing/core.py` (host-agnostic).
2. Add a **branch** in `_as_http_response` (FastAPI) and `_encode` / `__call__`
   (DirectoryASGI). Same order: Response → JSON → stream → *(new)* → HTML.
3. Document wrap **only** on the HTML branch.
4. Lock it in `tests/unit/test_host.py`.
5. Update this page in the **same change**.

Do **not**:

| Invent | Why it failed before |
|--------|----------------------|
| FastAPI `default_response_class=HTMLResponse` | JSON author routes become HTML |
| `StreamingRoute` / `route_class` | every GET chunked; CSP after first byte |
| `Accept` negotiation on page GET | second clock; caches fork |
| HTTP verbs on the Component (`get`/`post`) | FastAPI inspects classmethods; two scanners |
| Channel boot in `App.boot("auto")` | headless Channel, `attach` no-ops on real ASGI |
| `document.mount` in scaffold `main()` | host.bind already does it |
| `HTMLResponse` in page units | host wraps; Isolation of concerns |
| A second path function next to `http_path` | two scanners, two URLs |
| Logic in `routing/adapters/` | shims only |
| Mini HTML builder when `HAS_DOM` is false | invents a sixth product; L1 uses strings |
| `host="batteries"` as a product path | leftover ux-dom `DirectoryRouter` |

If a future need conflicts with the payload law, write **ADR 0003**. Do not
quietly add a second pipeline.

---

## 10. Related

| Doc | Role |
|-----|------|
| [adr/0002-product-host.md](../adr/0002-product-host.md) | Why |
| [guides/HOST.md](../guides/HOST.md) | Author recipes |
| [FLOW.md](../FLOW.md) §7 | Ownership pointer |
| [guides/PATH.md](../guides/PATH.md) | Product path tutorial |
| ux-dom `response/starlette.py` | `HTMLResponse` / `StreamingResponse` adapters |
| ux-dom `response/serialize.py` | `prepare_html_body` / `prepare_html_stream` / CSP stamp |
