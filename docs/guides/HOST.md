# Host recipes — HTML, JSON, stream

> **Diátaxis:** how-to · **Layer:** ux-compose
> Map: [INDEX.md](../INDEX.md). Law: [reference/host.md](../reference/host.md).

Return a value from `render()`. The host picks the HTTP container. You do not
import `HTMLResponse` / `JSONResponse` / `StreamingResponse` unless you opt in
to a stream-prepared tag tree.

Composition root stays:

```python
from pathlib import Path
from ux_compose.build import build
from document import document

app, asgi, bundle = build(
    Path(__file__).parent,
    host="auto",
    live="auto",
    document=document,
)
```

---

## HTML page (default)

`routes/hello.py` → `GET /hello`. `render()` is a fragment. The host wraps
the **author** Document (CSP, shell, stylesheet). A synthesized Document
(tests that omit `document=`) is mounted for CSP/static only — it does not
swallow the fragment.

```python
from ux_compose import Component, MorphState, action, div, span, update_with

class Hello(Component):
    id = "hello"
    n = MorphState(0)

    def render(self):
        return div(span(str(int(self.n or 0))), id=self.id)

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        return update_with(self)
```

L1 without ux-dom: return an HTML **string**. Strings stay `text/html` (they
are not JSON-encoded, they are not streamed).

Path params: `routes/shop/[sku].py` → `GET /shop/{sku}`.

```python
class Sku:
    def render(self, sku: str = ""):
        return div(sku, id="sku")
```

---

## JSON from a page unit

Return a `dict` (or a list of dicts). No `JSONResponse`. Document is not wrapped.

```python
# routes/health.py → GET /health   application/json
class Health:
    def render(self):
        return {"ok": True, "n": 1}
```

---

## JSON on the FastAPI process (extra API)

Page units stay `render()`. Extra endpoints are ordinary FastAPI routes on the
same process `build()` returned.

```python
app, asgi, bundle = build(PACKAGE, document=document)

@asgi.get("/api/health")
def health():
    return {"ok": True}

@asgi.post("/act/{name}")
def act(name: str, sku: str = ""):
    ops = app.dispatch(name, sku=sku)   # same door as tests
    return {"ops": [str(o) for o in ops]}
```

Do not put `get` / `post` on the Component. FastAPI must not inspect classmethods.

---

## Stream

Return a generator or async generator. No `StreamingResponse` wrap. No Document
wrap (chunked body has no `Content-Length`; CSP stamp cannot run after the
first byte unless you opt into ux-dom stream prepare).

```python
class Ticks:
    def render(self):
        def gen():
            yield "<div>a</div>"
            yield "<div>b</div>"
        return gen()
```

Stream a tag tree (nonce stamp, then chunks):

```python
from ux_dom.response.starlette import StreamingResponse

class Live:
    def render(self):
        tree = div("…", id="live")
        return StreamingResponse(tree)
        # or: return tree.__async_render__(pretty=False)
```

Do not set `router.route_class = StreamingRoute`. That is leftover ux-dom.

---

## Swap host without rewriting units

```python
build(PACKAGE, host="auto")      # FastAPI if installed
build(PACKAGE, host="fastapi")   # fail closed if missing
build(PACKAGE, host="asgi")      # DirectoryASGI, no Starlette
# host="batteries" → ProductBatteriesRejected
```

---

## See also

[reference/host.md](../reference/host.md) — payload table, path law, file map,
future protocol. [PATH.md](PATH.md) — full product path.
