# Product path — ux-compose

> **Diátaxis:** tutorial · how-to · **Layer:** ux-compose
> Map: [../INDEX.md](../INDEX.md) · Ownership: [../FLOW.md](../FLOW.md)
> Widgets: [UI.md](UI.md) · Public-API index: [SNIPPETS.md](SNIPPETS.md)

This page is the executed prompt: take a first-time author from `uxcompose create-app`
to a served app with Tailwind, HMR, composition, backend control flow, Caps, and
motion — without inventing APIs.

**Rules this page obeys**

1. Public names come from `ux_compose.__all__` and the `uxcompose` CLI in `pyproject.toml`.
2. Scaffold text comes from `ux_compose.scaffold` (what `create-app` actually writes).
3. Isolation Law: product modules never import `ux_channel`. Live Caps attach through `App.use_channel` / `wire/`.
4. Ownership: compose owns create-app / build / serve / deploy / HMR / tunnel. ux-dom renders. ux-behavior owns `@action`.
5. Progressive Superpower: L1 code stays correct at L2/L3. Zero rewrite of the Component.
6. Tailwind is `className` on tag trees. CSS lives in `assets/css`, never inside Python strings.
7. HMR is `uxcompose serve --no-reload --hmr`, not `Document.use`.
8. If code and this page disagree, **code wins**.

---

## How to read this

Nine jobs, in order. Each block is meant to run (or to be the exact fragment you
drop into the app `create-app` just wrote). When you want a widget rather than a
tour, open [UI.md](UI.md).

| # | Job | You leave with |
|---|-----|----------------|
| 1 | [Scaffold](#1-scaffold) | `settings.py` + `document.py` + `app.py` + `routes/hello.py` |
| 2 | [Hello page unit](#2-hello-page-unit) | A Component that morphs |
| 3 | [Serve](#3-serve) | HTTP on the product CLI |
| 4 | [HMR + tunnel](#4-hmr-and-tunnel) | Browser reload + optional public URL |
| 5 | [Tailwind](#5-tailwind) | `className` + `assets/css/input.css` |
| 6 | [Composition](#6-composition-root) | `build()` / levels 0–3 |
| 7 | [Control flow](#7-control-flow) | `dispatch`, `bind` / `control`, Caps |
| 8 | [Motion](#8-motion-xor) | Morph-then-Play, no `html=` on the plan |
| 9 | [Live](#9-go-live) | Channel through `wire/`, Isolation held |

---

## 1. Scaffold

`uxcompose` is the **only** product lifecycle CLI. `uxdom` stays pure-dom
(`doctor` / `lint` / `profile` / `add`). Do not run `uxdom create-app`.
Product CSS is `uxcompose build` (`ux_compose.tailwind` finds the CLI).

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install ux-compose ux-dom ux-behavior
# optional later: ux-channel ux-motion fastapi uvicorn

uxcompose create-app myapp --name Shop --level 1 --host auto
cd myapp
```

What landed:

```text
myapp/
  settings.py         # BASE_DIR, DEBUG, WebAssets
  document.py         # Document SSoT + .use(XElement, Csp) + page()
  app.py              # composition root: build(host=, live=, level=, document=)
  README.md
  requirements.txt
  assets/css/input.css
  routes/
    __init__.py
    hello.py          # page unit: file stem == class name; get() wraps page()
```

`--level auto` unlocks specialists that import. Pin `--level 1` until Channel is
intentional. `--host auto` prefers FastAPI if installed, else a pure ASGI adapter.

Next:

```bash
uxcompose build
uxcompose serve app:asgi
uxcompose doctor . --no-fail
```

---

## 2. Hello page unit

`create-app` writes this class. It is the whole author contract in one file.

- `id` is the morph target (`#hello`).
- `MorphState` mutation means this unit must repaint.
- `render()` returns a **ux-dom tag tree** with Tailwind `className`.
- `@action(caps=())` is public. Non-empty caps need a live Cap (or fail closed).
- `control("hello.inc")` stamps `data-ux-action` (+ args) on the button.
- `update_with(self, extra_ops=[notify(...)])` morphs live `render()` HTML (XOR-safe).

```python
from ux_compose import Component, MorphState, action, control, notify, update_with

try:
    from ux_compose import div, span, button, HAS_DOM
except Exception:
    HAS_DOM = False
    div = span = button = None


class Hello(Component):
    id = "hello"
    n = MorphState(0)

    def render(self):
        n = int(self.n or 0)
        attrs = control("hello.inc")
        if HAS_DOM and div is not None:
            return div(
                span(str(n), className="text-2xl font-semibold tabular-nums"),
                button(
                    "+1",
                    type="button",
                    className=(
                        "rounded-full bg-stone-900 text-stone-50 "
                        "px-4 py-2 text-sm font-medium hover:bg-stone-800"
                    ),
                    **attrs,
                ),
                id=self.id,
                className=(
                    "flex items-center gap-3 rounded-2xl "
                    "border border-stone-200 bg-white p-6 shadow-sm"
                ),
            )
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return (
            f'\u003cdiv id="hello"\u003e\u003cspan\u003e{n}\u003c/span\u003e'
            f"\u003cbutton {attr_str}\u003e+1\u003c/button\u003e\u003c/div\u003e"
        )

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        return update_with(self, extra_ops=[notify("incremented")])
```

Page-unit law: `routes/hello.py` exports class `Hello`. The stem matches the
class. Host adapters (FastAPI / ASGI) are chosen in `build(host=)`, not here.

---

## 3. Serve

`app.py` is the composition root. `asgi` is the attribute uvicorn loads.

```python
from pathlib import Path
from ux_compose.build import build
from document import document

PACKAGE = Path(__file__).resolve().parent

def main(*, use_htmx: bool = False):
    app, asgi, bundle = build(
        PACKAGE,
        name="Shop",
        host="auto",      # auto | fastapi | asgi
        live="auto",      # auto | channel | null
        level=1,          # pin offline until Channel is a decision
        base="routes",
        use_htmx=use_htmx,
        document=document,
    )
    return app, asgi, bundle

_app, asgi, _bundle = main()
```

HTMX is **never** auto-attached. Pass `use_htmx=True` (or `Document.use(Htmx())`)
to opt in.

```bash
uxcompose serve app:asgi
# defaults: --host 0.0.0.0 --port 8080 --reload
```

Process reload is uvicorn. That is not browser HMR.

Prove the unit without HTTP:

```python
from ux_compose import App
from routes.hello import Hello

app = App.boot("Shop", level=1)
app.add(Hello)
print(app.dispatch("hello.inc"))
print(int(app.level), app.level.label)   # 1 offline interactive
```

---

## 4. HMR and tunnel

HMR and tunnel are **delivery features of `serve`**. They are not Document APIs.

Browser WebSocket HMR needs a concrete ASGI object, so turn process-reload off:

```bash
uxcompose serve app:asgi --no-reload --hmr
# watches . and routes
# WebSocket /__uxcompose/hmr  →  {type: reload}

uxcompose serve app:asgi --no-reload --hmr --watch assets --watch routes
```

Optional client stub (dev shells that do not go through `attach_hmr`):

```python
from ux_compose.hmr import client_script_tag, attach_hmr, HMR_PATH

# attach_hmr(asgi_app, watch_paths=[".", "routes"])
# html = "... " + client_script_tag()
print(HMR_PATH)   # /__uxcompose/hmr
```

`--reload` (uvicorn workers) and `--hmr` (browser WS) are different clocks.
`serve --hmr` without `--no-reload` prints that and uses process reload only.

Public URL after health is green:

```bash
uxcompose serve app:asgi --tunnel ngrok
uxcompose serve app:asgi --tunnel cloudflare --tunnel-token "$TOKEN"
```

---

## 5. Tailwind

**Do not put CSS or client JS inside Python strings.**

1. Author utilities on the tree: `className="rounded-2xl border …"`.
2. Tokens + `@layer components` live in `assets/css/input.css`.
3. Tailwind scans `apps/**`, `examples/**`, `src/**` (`tailwind.config.js`).
4. Build CSS; the Document **links** the file.

```bash
uxcompose build
# writes assets/static/file/css/output.css (minified)
# product CSS watch lives on uxcompose build --watch
```

Scaffold Hello already uses Tailwind utilities on `div` / `button` / `span`.
That is the product path: same classes FastAPI authors put on templates, but
the tree is Python and serializes with `__render__`.

Tokens (from `assets/css/input.css`) — evolve these, do not invent a second palette
in Python:

```css
:root {
  --bg: #f3efe6;
  --surface: #fffdf8;
  --fg: #161513;
  --accent: #2f3b38;
  --font-display: "Fraunces", Georgia, serif;
  --font-body: "Source Sans 3", system-ui, sans-serif;
}
```

Copy-in markup kit (optional, still render-only — no Ops):

```python
from ux_dom.ui import Button, Card, CardHeader, CardTitle, CardContent
from ux_compose import control

card = Card(
    CardHeader(CardTitle("Cart")),
    CardContent(
        Button("Add tee", type="button", variant="default", **control("cart.add", sku="tee")),
    ),
)
```

---

## 6. Composition root

`build()` is one place to set **host** and **live**. Authors never implement
adapters (Invisible Strategy).

```python
from pathlib import Path
from ux_compose import build

app, asgi, bundle = build(
    Path(__file__).parent,
    name="Shop",
    host="auto",    # auto | fastapi | asgi
    live="auto",    # auto | channel | null
    level="auto",   # auto | 0..3
    base="routes",
)
print(app.name, int(app.level), app.level.label)
print(list(bundle.surfaces) if bundle else None)
```

Equivalent progressive unlock, same Component:

```python
from ux_compose import App, Level

app = App.boot("Shop", level=1)     # MorphState + @action, offline
print(int(app.level), app.level.label)

app.use_host("fastapi")             # auto | fastapi | starlette | asgi | batteries
# app.use_channel(asgi_app=api)     # Level 2 — Isolation-safe (wire/ import)
# app.use_motion()                  # Level 3 — Morph-then-Play
# app.use_cek(mode="adapt")         # optional; mode="require" raises if missing

assert Level.L1.value == 1
```

| Level | You get | You still do not |
|-------|---------|------------------|
| 0 | Document + static Components + DirectoryRoutes | Dispatch |
| 1 | + Behavior + MorphState + `@action` | Caps, signed Intent |
| 2 | + Channel + Caps + `control()` | Motion IR |
| 3 | + Motion / Scenes | A second Cart class |

If you rewrite the Cart to “go live”, you have violated the contract. Attach
Channel; do not fork the component.

Isolation Law: product modules never `import ux_channel`. Cold import of
`ux_compose` does not load the wire.

```python
from ux_compose import doctor

report = doctor(".", fail=False)
print(report.ok, report.capabilities, report.level_available)
```

```bash
uxcompose doctor . --no-fail
```

---

## 7. Control flow

A click is not a client store update. The browser posts an **action name + args**.
The server runs `@action`, returns Ops, the runtime applies them.

```text
button / form  --control()/bind()--\u003e  data-ux-action + data-ux-arg-*
        |
        v
   dispatch("hello.inc")           # L1, tests, agents
   submit_intent(...)              # L2, signed Intent + Cap
        |
        v
   @action  mutates Morph/Ref  →  list[Op] | None
        |
        v
   morph #hello  ·  notify  ·  optional transition.play
```

**Return algebra (hard)**

1. `return None` — auto-morph dirty MorphState units.
2. `return list[Op]` — exact Ops; auto-morph suppressed.
3. Prefer `update_with(self, plan, extra_ops=[notify(...)])`.
   Morph HTML is live `render()`. The Plan has no `html=` (XOR).

**`bind` vs `control`**

```python
from ux_compose import bind, control

# preferred: symbol-safe, fails closed on unknown kwargs
button("+ tee", type="button", **bind(self.add, sku="tee"))
button("+ tee", type="button", **self.add.ui(sku="tee"))

# stringly escape hatch (progressive HTML you do not have a method object for)
button("+ hat", type="button", **control("cart.add", sku="hat"))
```

**Caps — the authority clock**

```python
from ux_compose import App, Component, action, notify

class Cart(Component):
    id = "cart"

    @action(caps=())                 # public
    def add(self, sku: str = ""):
        return [notify(f"Added {sku}")]

    @action(caps=("orders.place",))  # live Cap, or AuthorityError offline
    def checkout(self):
        return [notify("Checkout")]

app = App.boot("Shop", strict_caps=True, level=1)
app.add(Cart)
app.dispatch("cart.add", sku="tee")      # ok
# app.dispatch("cart.checkout")          # fail closed offline
```

Chrome (tabs, accordion, open/close) is public. Spending money, deleting, or
changing identity takes a Cap.

**Live-safe quantities.** Channel's session plane refuses *quantity* MorphState
(ints, numeric strings). Teach this form so L2 is zero rewrite:

```python
from ux_compose import MorphState, RefState

n = RefState(0)             # magnitude / list / money
stamp = MorphState("idle")  # qualitative dirty tick so the unit still morphs
```

Boolean / named-step MorphState is qualitative and legal on the session plane.

**Drive from the backend.** The browser is not the store. Tests, agents, and
HTTP handlers call the **same door** (`dispatch`). Live Caps use `submit_intent`.

```python
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from ux_compose import App
from routes.hello import Hello

api = FastAPI()
ux = App.boot("Shop", level=1)
ux.add(Hello)

@api.post("/act/{name}")
def act(name: str, sku: str = Form("")):
    ops = ux.dispatch(name, sku=sku)    # same door as tests and agents
    return JSONResponse({"ops": [str(o) for o in ops]})

# no HTTP required
print(ux.dispatch("hello.inc"))
```

`App.submit_intent(action, cap=..., mint=False)` is the live door. Tests stay
on `dispatch`. `Behavior.trust()` / compose does not grow a production bypass.

---

## 8. Motion XOR

Laws:

- **XOR** — `morph(target)` XOR `scene.enter(target, html=...)`. Never both.
- **Morph-then-Play** — morph Op first; `transition.play` follows.
- **Isolation** — Plan comes from `ux_compose.scene` (re-export), never `ux_channel`.

Do:

```python
from ux_compose import action, update_with, notify, scene, rise

@action(caps=())
def add(self, sku: str = ""):
    self.count = int(self.count) + 1
    plan = scene("cart-pop").enter(f"#{self.id}", rise.enter(ms=160))
    return update_with(self, plan, extra_ops=[notify(f"Added {sku}")])
```

Don't:

```python
# illegal — html= on the same target as the morph
return scene("pop").enter("#cart", rise.enter(ms=160), html=self.render())
```

Without ux-motion, `scene` is `None` and the same action still morphs.
That is the Progressive Superpower.

Shared-element (FLIP) uses a continuity id, still no `html=` on the plan:

```python
from ux_compose import scene

plan = (
    scene("pdp")
    .share("hero", leave="#from-linen", arrive="#to-linen")
)
```

---

## 9. Go live

Channel attaches **only** through compose `wire/`. This module does not import
`ux_channel`.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from ux_compose import App, doctor
from ux_dom import Document
from ux_dom.runtime import XElement, Csp

api = FastAPI(title="Shop")
document = Document(head=[], body=[], ensure_csrf_token=False).use(
    XElement(), Csp.auto()
)

ux = App.boot("Shop", strict_caps=False, level=1)
ux.use_dom(document)
ux.use_channel(asgi_app=api)   # Isolation door
ux.use_motion()                # no-op if ux-motion missing
ux.add(Hello)

@api.get("/", response_class=HTMLResponse)
def index():
    inst = ux.behavior.get("hello")
    return HTMLResponse(str(document(inst.render())))

print(int(ux.level), ux.level.label)
print(doctor([], fail=False).capabilities)
```

Serve the FastAPI app the same way:

```bash
uxcompose serve app:asgi --no-reload --hmr
```

`App.submit_intent(action, cap=..., mint=False)` is the live door. Tests stay on
`dispatch`. `Behavior.trust()` / compose does not grow a production bypass.

Deploy:

```bash
uxcompose deploy --provider docker
uxcompose deploy --provider fly|render|railway|vps|checklist
```

---

## Where next

| Goal | Go |
|------|----|
| Pick-and-use widgets | [UI.md](UI.md) |
| Public-API index | [SNIPPETS.md](SNIPPETS.md) |
| CLI surface | [CLI.md](CLI.md) · [serve-hmr-tunnel.md](serve-hmr-tunnel.md) |
| Ownership law | [../FLOW.md](../FLOW.md) |
| Example map (99% of product UI) | [../../examples/README.md](../../examples/README.md) |
| 5-minute door | [../../START_HERE.md](../../START_HERE.md) |
