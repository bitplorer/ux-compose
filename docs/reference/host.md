# Product host — Clock A (reference)

> **Diátaxis:** reference · **Canonical:** `docs/reference/host.md` · **Layer:** ux-compose
> Map: [INDEX.md](../INDEX.md). Decision: [adr/0002-product-host.md](../adr/0002-product-host.md).
> Ownership: [OWNERSHIP.md](../OWNERSHIP.md) §7. How-to: [guides/HOST.md](../guides/HOST.md).

HTTP Product host (Clock A) ≠ CEK Cap Host (cek-runtime via `wire/cek`).

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

Clock B is Channel HTTP (`/ux-channel*`), not Clock A `routes/health.py`.
Channel `GET /ux-channel/health` advertises **`formats`** (HTTP today:
`application/ux-channel+json`) vs **`codecs`** (library: json, cxb, …),
matching the Rust peer. Compose does not re-implement that body. Product
`/health` / `/api/health` remain Clock A JSON (`dict` → `application/json`).

---

## 2. Process order

```text
host.open(name, host)          # FastAPI() or DirectoryASGI
App.boot(..., level=1)         # Behavior only (strict_caps=True by default)
_attach_document(...)          # author's Document SSoT
App.use_channel(asgi_app=)     # after the process exists
DirectoryRoutes.discover()     # one path law
host.bind(...)                 # document.mount then page routes
```

`routing/host.py` owns order: `open()` then `bind(document=, wrap=)`.
`build()` passes the author Document as `wrap` (or an explicit `wrap=`) and
the (possibly synthesized) Document as `document`. Synthesized Document is
**mount-only** (CSP / static). Wrapping GET with a shell the author did not
write drops HTML-string fragments (ux-dom treats a positional `str` on
`<body>` as a script `src`).

Product path is `build(document=, wrap=document)`. The brand bar lives on the
author Document — not a string `wrap_get_chrome` / `shell.py` dual floor.
`ux_compose.brand.brand_wrap(document, brand=…)` returns `wrap(child)` that
puts nav brand outside `Component.render()` (GET brand=1, morph brand=0).
Do not put brand / `stunning-root` / `class="nav"` inside `routes/*.py`
`render()` (morph payloads stay fragments).

`App.boot("auto")` is **Level 1**. Channel never boots headless on auto —
`Behavior.attach` is idempotent on `_wire`, so a headless Channel would never
land on FastAPI. `use_channel(asgi_app=)` rebinds if a headless wire landed
first (tests / explicit `level=2`).

---

## 3. Payload law (media type)

**The return value picks the HTTP container. Not `Accept`. Not a route class.
Not FastAPI `default_response_class`.**

Same spirit as ux-dom `html_response` / `streaming_response` (wrap trees, pass
the rest through). Compose treats a `str` as HTML, never JSON.

A `str` or `bytes` body is **untrusted HTML**. Both hosts send it through
ux-dom `sanitize_html` (the one string sanitizer, ux-dom ADR 0002), with or
without a Document. A generator body goes through `sanitize_html_stream`:
its `str` / `bytes` chunks are untrusted, its tree and `Markup` chunks are
sent as written. `Markup` (anything with `__html__`) is explicit trust and
is never sanitized. A Response object is passed through as-is.

One closed type contract holds at every HTML sink (route body, stream
chunk, `render()`, morph html, motion `enter` html, `brand_wrap`):
`ux_compose.dom.html_value` / `html_text`. Trusted: `__html__` and real
ux-dom trees (ux-dom `dom_tag` / `Component`, `Document`, compose
`Component`). Sanitized: `str`, and `bytes` as strict UTF-8. `None` is
empty. Any other type (list, tuple, numbers, an object with an HTML
`__str__`) raises `TypeError` naming the sink, never `str()`; bytes that
are not UTF-8 raise `ValueError`. On a route either is a 500.

| `render()` / handler returns | HTTP | Document wrap | CSP stamp |
|------------------------------|------|---------------|-----------|
| ux-dom tag / Document / Component / HTML `str` / `bytes` | `HTMLResponse` | yes | yes (ux-dom `prepare_html_body`) |
| `dict` or list-of-dicts | JSON (`application/json`) | **no** | n/a |
| sync / async generator, or `__aiter__` that is not a tree | `StreamingResponse` (`text/html`), `sanitize_html_stream` | **no** | only if ux-dom stream prepare runs |
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
2. stream payload → `open_html_stream` (sanitized, first piece computed
   before the status line) → `StreamingResponse` (ux-dom if it accepts the
   body, else Starlette)
3. else → `apply_html_document(wrap, tree)` then `HTMLResponse`

`apply_html_document` lives in `routing/core.py`. An HTML `str` / `bytes`
becomes `sanitize_html(...)`, and inside a Document ux-dom
`raw(sanitize_html(...))` so the fragment is body markup, not a script `src`.

DirectoryASGI (`host="asgi"`) uses the same predicates. Streams go out as
chunked ASGI `more_body`. JSON is `json.dumps`. HTML is `to_html_bytes`.

A stream that holds more than ux-dom `MAX_BUFFER_CHARS` (1 MiB) characters
without a safe HTML boundary raises `HtmlStreamOverflow` and none of the
held text is sent (fail closed, logged). Before the first piece that is a
**500** `Internal Server Error` with no page bytes (as is any other error
there). After it, the status line is out: the response is aborted with no
final chunk, so the client sees a cut-off response, not a complete one.

### Why trees are not auto-streamed

A complete document wants `Content-Length` and a CSP nonce **before** the first
byte (`stamp_tree` then serialize). Auto-wrapping every tag in `StreamingResponse`
drops both. Leftover ux-dom `StreamingRoute` as `route_class` is **not** the
product path.

To stream a tag tree, opt in:

```python
return StreamingResponse(tree)               # ux-dom stream prepare + CSP
# or yield trees: a tree chunk is rendered by ux-dom and sent as written
```

`return tree.__async_render__(pretty=False)` yields plain `str` tokens,
which a generator body sanitizes like any other string.

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
├── document.py            Document SSoT (.use(XElement, Csp, Channel.optional)); host wraps GET
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
| `app.py` | `build(host=, live=, level=, document=, wrap=document)` | HTML wrap, HTTP verbs |
| `routes/*.py` | `render()` + `@action` | `get()`, `HTMLResponse`, Document.mount |

Gone: `Hello.get()`, `document.mount(asgi)` in `main()`, class HTTP verbs.

---

## 6. File map (where to edit)

| Question | File |
|----------|------|
| What happens on GET /hello? | `src/ux_compose/routing/fastapi.py` |
| Process order? | `src/ux_compose/routing/host.py` |
| Path / stem / JSON / stream / wrap? | `src/ux_compose/routing/core.py` |
| No-Starlette degrade? | `src/ux_compose/routing/asgi.py` |
| Orchestra (`wrap=` vs `document=`)? | `src/ux_compose/build.py`, `surfaces_host.py` |
| Channel attach? | `src/ux_compose/wire/boot.py` only |
| Scaffold? | `src/ux_compose/scaffold.py` |
| Fitness tests? | `tests/unit/test_host.py` |

Product imports `ux_compose.routing.asgi` / `ux_compose.routing.fastapi`.

Invisible Strategy: authors import `build()`. `App.mount` is the catalog
scan inside `build()`, not a second product path. They do not import
`routing.fastapi` / `routing.host`. Maintainers always do. Product examples
call `build()`; handmade Clock A GET (`@app.get` + `HTMLResponse`) is not
the product path.


---

## 7. Host values

| `host=` | Process | Fail |
|---------|---------|------|
| `auto` | FastAPI if importable, else DirectoryASGI | never |
| `fastapi` | FastAPI | closed if FastAPI missing |
| `asgi` | DirectoryASGI (no Starlette) | never |
| other names | — | closed (`ValueError`) |

FastAPI is **not** given `default_response_class=HTMLResponse`. Author
`@asgi.get("/api/...")` returning a dict stays JSON.

OpenAPI / Swagger is **off** by default (`docs_url=None`, `redoc_url=None`,
`openapi_url=None`) so `routes/docs.py` → GET `/docs` is a Document page
(author wrap / `brand_wrap`). Opt in: `build(openapi=True)` or
`settings.OPENAPI = True`. Doctor warns when a surface path collides with
`/docs` `/redoc` `/openapi.json` (prefer `/about`).

---

## 8. Isolation / Document / Channel

- Product modules never import `ux_channel`. Door: `App.use_channel(asgi_app=)`.
- Cap door is `Channel.boot` (wire/ only). `ActionRegistry.from_config` is
  not a frozen compose import. Boot applies the Cap adapter when
  `cek != "off"`. Do not assume classic `CapService` at `cek=require`.
- Channel prefers Redis when `REDIS_URL` is set. serve-dev will not export
  both `REDIS_URL` and `UXCOMPOSE_STATE_STORE`. Pin: ux-channel @ `c7b763b`
  (Python ≥3.14 tip; Cut C floor `985e58a`).
- Cold import never pulls `wire/`.
- Document is SSoT: one `Document` in `document.py`. `build(document=)` attaches
  it. Dual-Document is a doctor fail.
- `document.mount(asgi)` (CSP middleware, package static) runs in `host.bind`
  on FastAPI only, using the (possibly synthesized) Document. Page GET wraps
  **only** the author `document=` (`wrap=`). DirectoryASGI has no middleware;
  doctor reports CSP middleware is not attached.
- HTMX is opt-in (`build(use_htmx=True)` / `Document.use(Htmx())`, from
  `ux_compose.htmx`). With `use_htmx=True` a page GET with `HX-Request: true`
  that is not a history restore gets the fragment, not the Document shell.
  HTML page responses then send `Vary: HX-Request`.
- `Document.use(XElement(), Csp.auto(), Channel.optional())` (the
  `ux_dom` Document-plugin alias, not `ux_channel.Channel`) is the full shell.
  Product path is `build(document=, wrap=document)`. There is no
  Document-absent live-client / `wrap_get_chrome` primary. GET brand bar
  is `wrap=brand_wrap(document, brand=…)` on the Document path.
  `live="null"`
  stays offline Behavior. Complete documents and `/css` are not
  double-wrapped.
- `ux-bridge.js` is opt-in. It loads only with `Channel.optional(bridge=True)`
  on the Document, or `attach_live_client(asgi, bridge=True)` /
  `LiveClientMiddleware(app, bridge=True)` on the live-client path.

### Helper modules are not reloaded

`build()` leaves the route module in `sys.modules`. After `build()`,
`import pkg.routes.a` is the module that served the page, and
`typing.get_type_hints` can still read that module's globals, including
when the package is not on `sys.path`. A folder on `sys.path` runs the
route file once. A folder that is not runs it twice on the first build,
then not again unless the file's bytes changed. Helper modules those routes import —
`models.py`, a helper package such as `models/__init__.py`, and any other
module that is not the route file — keep the module object from the first
import. Editing a helper is not picked up on rebuild. Restart the process
to load it.

Isolation and eviction run only when a different directory with the same
package name is built. Rebuilding one folder does not add another copy of
its modules. The first build of a new folder may add that folder's modules
once. Each distinct app adds three `sys.modules` keys, and a rebuild adds
none, so the growth is bounded by the number of distinct apps.

Known limitation: during a same-name build, a shared `sys.modules['myapp']`
means a thread that isn't building can see the building folder's helpers.
Its `__path__` points at the folder being built, so the meta_path finder
isn't involved.

### Same-name builds take turns importing

Two `build()` calls whose package folders share a name import one at a
time. The wait is reentrant on the thread that already holds that name, so a
route may call `build()` for the same folder name on the same thread.
Different folder names keep running together. Nothing in that wait is held
across another package's route body.

While a name is importing, `pkg` and `pkg.*` resolve to that build's
directory even if another thread has put a different copy first on
`sys.path`. The build serves the helper from its own tree. It does not
serve another app's helper. A name that is not on `sys.path` at all is
not imported: `build()` raises `ModuleNotFoundError` for that name.

A second thread that is still waiting when the timeout elapses gets
`BuildLockTimeout` from `ux_compose.build`. The message names the package
and the setting. `lock_timeout=None` does not turn a deadlock into that
error. `build()`, `App.mount`, and `DirectoryRoutes.discover` share one
parser. `build(lock_timeout=...)` overrides the environment.
`UX_COMPOSE_BUILD_LOCK_TIMEOUT` applies when that argument is omitted,
and it is the only input `App.mount` and `DirectoryRoutes.discover` read.

| Value | Meaning |
| --- | --- |
| unset, or `''` | 60 seconds |
| `0` | no wait: one try, then `BuildLockTimeout` |
| `inf`, `none` (any case; `infinite` too) | no limit |
| `abc`, `-1`, `nan` | `ValueError` naming `UX_COMPOSE_BUILD_LOCK_TIMEOUT` |

`UX_COMPOSE_BUILD_LOCK_TIMEOUT` and `build(lock_timeout=...)` are new in
this release. A value that is not a timeout raises `ValueError`. The
message names `UX_COMPOSE_BUILD_LOCK_TIMEOUT`.

`lock_timeout=None` is the same as `none`. `inf` is not passed to the
lock, so it does not raise `OverflowError`. `-1` does not wait forever.
That build does not continue after a timeout, so it cannot bind the
other thread's modules.

The wait for another folder's import does not hold the package-name
lock. `build()` releases it, then takes it again and rechecks the
folder. An import that calls `build()` for that same name, including
when the timeout is `None`, is `PackageImportConflict`. The exception
names the folder that was loaded and the folder being built. The other
folder is not served.

---

## 9. CSP on FastAPI (two layers, one nonce)

FastAPI has no CSP of its own. The product path installs ux-dom `Csp` because
the process has `add_middleware`. DirectoryASGI does not.

| Layer | What | When | Owner |
|-------|------|------|-------|
| **Header** | `Content-Security-Policy` on `http.response.start` | every HTTP response | `CspMiddleware` via `document.mount` |
| **Stamp** | `nonce=` on `<script>` / `<style>` **before first byte** | HTML body / tree stream | `prepare_html_body` / `prepare_html_stream` |

Same nonce. Middleware creates it (`ContextVar` + `scope["ux_dom_csp_nonce"]`).
Serialize only reads it. Middleware does **not** overwrite a CSP header the
response already set.

| `render()` returns | Document wrap | Nonce stamp | CSP header (FastAPI) |
|--------------------|---------------|-------------|----------------------|
| tag / HTML `str` | yes (author wrap) | yes (`HTMLResponse.render`) | yes |
| `dict` | no | n/a | yes (process-wide) |
| generator | no | no | yes |
| ux-dom `StreamingResponse(tree)` | no | yes (stamp then chunks) | yes |

`Csp.auto()` picks `Csp.dev()` when `DEBUG` is truthy, else `Csp.prod()`.
Authors attach once in `document.py`: `.use(XElement(), Csp.auto())`. They
never set CSP headers in page units.

Trees stay buffered `HTMLResponse` so stamp + `Content-Length` happen before
the first byte. That is why leftover `StreamingRoute` is not the product path.

---

## 10. Future protocol (do not fragment)

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
| Mini HTML builder when `HAS_DOM` is false | invents a sixth product; ux-dom is a hard dep |
| Wrap GET with a synthesized Document | HTML `str` becomes script `src`; fragment vanishes |
| Scaffold `page()` as the GET wrap | host calls `document(child)`; two wrap stories |
| Document-absent `wrap_get_chrome` / `shell.py` primary | dual floor; product path is `wrap=document` |

If a future need conflicts with the payload law, write **ADR 0003**. Do not
quietly add a second pipeline.

---

## 11. Related

| Doc | Role |
|-----|------|
| [adr/0002-product-host.md](../adr/0002-product-host.md) | Why |
| [guides/HOST.md](../guides/HOST.md) | Author recipes |
| [OWNERSHIP.md](../OWNERSHIP.md) §7 | Ownership pointer |
| [guides/PATH.md](../guides/PATH.md) | Product path tutorial |
| ux-dom `response/starlette.py` | `HTMLResponse` / `StreamingResponse` adapters |
| ux-dom `response/serialize.py` | `prepare_html_body` / `prepare_html_stream` / CSP stamp |


## Cap default (0.2.0)

`App` and `build()` fail closed: `strict_caps=True` is the default. A capped
`@action` raises `AuthorityError` unless the call is inside `app.trust()`
or the wire called `dispatch_verified(name, payload)` after Channel accepted
a Cap. Pass `strict_caps=False` only for an unchecked local sandbox.

Two doors, and they are not interchangeable:

| Door | Who | What it means |
|------|-----|----------------|
| `with app.trust():` | Developer-authored server code (demos, tests, admin tools) | This task may run capped actions. Trust stays on a task started inside the block, so do not start a long-lived worker, queue consumer, or background task there. |
| `dispatch_verified(name, payload)` | `wire/caps.bridge_actions`, after Channel accepts the Cap | Trust for that one call. A task started inside it does not inherit the trust. `async_dispatch_verified` is the async twin. A bool does not grant trust (ux-behavior #20, pin `09a9a65`). |

Channel verifies the Cap at the edge. `bridge_actions` was added so product
action names mint against the author name, and the handler then host-dispatches
because that check already happened (`a82495d`). From ux-behavior 0.4.0,
attaching Channel does not skip the check by itself. `dispatch_verified`
is how the handler records the acceptance, for one call.

`App.trust` delegates to `Behavior.trust`. It is not a substitute for a Cap
on a request a client sent.

A payload key named `action` arrives when the action names that parameter.
`App.control` and `App.mint_cap` take the action name positionally, so
`control('box.open', action='x')` and `mint_cap('box.save', action='x')`
pass that key through as caller data.
The component instance is bound positionally. A posted key named `self` is
not that instance and is not passed into the action, including through
`**kwargs`. When the signature does not accept the key at all, it comes
back the same way as every other action validation error: the message
(`unexpected keyword argument 'self'`) on the result, the same HTTP status,
the same result shape, never a 500. There is no separate status for this key.

## Visitor identity

Every request has a subject, and every page Cap is minted for it
(`sub=`), so a Cap runs only for the visitor whose page it was painted on.

- **Logged in:** `scope["user"].identity` when `scope["user"].is_authenticated`
  (Starlette `AuthenticationMiddleware`, the identity port). Add it after
  `build()`, so it wraps compose's middleware and runs first.
- **Anonymous:** `anon:<random>`, minted by the server on the first page
  response in the `uxc_visitor` cookie: `HttpOnly; SameSite=Lax; Path=/`,
  plus `Secure` when the request scheme is `https`. No `Max-Age`: the
  visitor lasts for the browser session. The value is the id and an
  HMAC-SHA256 over it. The key is derived from the Channel secret for this
  one purpose, so a visitor cookie never verifies as a Cap. A missing,
  malformed, or forged cookie gets a new visitor. The client never chooses
  the id.

`use_channel(asgi_app=...)` adds `ux_compose.visitor.VisitorMiddleware` and
sets the Channel `registry.auth_resolver` to the same subject. The cookie
is not set on a WebSocket. A Cap minted outside a request (a test, a
script) names no subject, as before.

## Attach secret

Outside dev, `Behavior.attach` requires `UX_CHANNEL_SECRET` (or
`UX_BEHAVIOR_SECRET`). A secret shorter than 16 characters, and any other
error `Channel.boot` raises, is an attach failure too. `wire/boot.py`
sets `strict_attach=True` before `attach`, so the error propagates.
`use_channel` raises when that call returns no channel. A `TypeError`
from `attach` stops the boot; compose does not retry without `secret=`.
Outside `uxcompose serve dev`, compose does not invent a secret and does
not continue without Caps. `serve dev` mints one secret per session for its
two workers (see [CLI](../guides/CLI.md#channel-secret-and-debug)). `examples/live_asgi.py`, `apps/atelier_shop`, and
`apps/atelier_studio` fail the process. Dev is `DEBUG` in `1` / `true` /
`yes` / `on` (`ux_behavior.wire.debug_requests_dev`); unset is prod.
