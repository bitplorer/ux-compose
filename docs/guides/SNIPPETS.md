# ux-compose — snippets

> **Diátaxis:** how-to · copy-paste patterns from the public API (`__all__` / CLI).
> Map: see this package `docs/INDEX.md`.

Composition root. Imports specialists. Sole product CLI: uxcompose.

Every block is meant to run (or to be the exact fragment you drop into a running app). Names are public exports. If code and this page disagree, **code wins**.

**13 snippets** covering install, core usage, fail-closed errors, live/async, CLI, host payload, and the usage patterns that keep layers from leaking.

### Public names in this cookbook

`update_with`, `scene`, `rise`, `notify`, `doctor`, `App`, `Component`, `MorphState`, `action`, `bind`, `control`, `div`, `button`, `morph_play`, `Path`, `scan_surfaces`, `validate_surfaces`, `mount_surfaces`, `build`, `Level`

## Contents

- [Product path](#co-install)
- [Level 1 Cart (MorphState + ux-dom tree)](#co-core)
- [bind() vs control() in compose](#co-bind)
- [doctor() laws](#co-doctor)
- [uxcompose CLI surface](#co-cli-full)
- [Progressive levels 0–3](#co-levels)
- [Morph-then-Play (XOR)](#co-xor)
- [morph_play helper](#co-morph-play)
- [scan / validate / mount surfaces](#co-surfaces)
- [build() composition root](#co-build)
- [use_host / use_channel / use_motion](#co-host)
- [HTML / JSON / stream from render()](#co-payload)
- [Pattern: progressive levels 0–3](#co-pattern-levels)


## Install

### Product path

<a id="co-install"></a>

Sole product lifecycle CLI is uxcompose. uxdom stays pure-dom (doctor / lint / profile / add).

```bash
uxcompose create-app myapp --level 1
cd myapp
uxcompose serve app:asgi --port 8080
uxcompose deploy --provider docker
uxcompose doctor .
```


## Core usage

### Level 1 Cart (MorphState + ux-dom tree)

<a id="co-core"></a>

render() returns a ux-dom tag tree, not an HTML string. Level 1 code remains correct at L2/L3 — zero rewrite.

```python
from ux_compose import (
    App, Component, MorphState, action, update_with, notify, control,
    div, h1, button,
)

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return div(
            h1(f"Items: {self.count}"),
            button("+ tee", **control("add", sku="tee")),
            id=self.id,
        )

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return update_with(self, extra_ops=[notify(f"Added {sku}")])

app = App.boot("Shop", strict_caps=False, level=1)
app.add(Cart)
print(app.dispatch("cart.add", sku="tee"))
print(int(app.level), app.level.label)
```

### bind() vs control() in compose

<a id="co-bind"></a>

Prefer bind / .ui. control(str) stays for progressive HTML you do not have a method object for.

```python
from ux_compose import App, Component, MorphState, action, bind, control, notify, div, button

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return div(
            button("+ tee", **bind(self.add, sku="tee")),   # preferred
            button("+ hat", **control("add", sku="hat")),   # stringly hatch
            id=self.id,
        )

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return [notify(f"Added {sku}")]
```


## CLI

### doctor() laws

<a id="co-doctor"></a>

doctor checks Isolation Law, CLI ownership, and specialist presence. Also: uxcompose doctor .

```python
from ux_compose import doctor

result = doctor(".")
print(result.ok, result.issues)
```

### uxcompose CLI surface

<a id="co-cli-full"></a>

Sole product CLI is uxcompose. Isolation Law: product modules never import Channel at cold import.

```bash
uxcompose create-app myapp --level 1
cd myapp
uxcompose serve app:asgi --port 8080
uxcompose doctor .
uxcompose deploy --provider docker
# product lifecycle lives here. uxdom doctor / lint / profile stay pure-dom.
```


## Composition

### Progressive levels 0–3

<a id="co-levels"></a>

Authors do not import ux_channel outside compose wire/. Channel attach is App.use_channel(...).

```python
app = App.boot("Shop", level=1)          # offline MorphState + @action
# app.use_channel(asgi_app=api)          # Level 2 — live Caps, Isolation-safe
# app.use_motion()                       # Level 3 — Morph-then-Play
# app.use_cek(mode="adapt")              # optional
```

### Morph-then-Play (XOR)

<a id="co-xor"></a>

update_with combines state morph with an optional plan. Do not also pass html= on the same target.

```python
from ux_compose import update_with, scene, rise, notify

@action(caps=())
def add(self, sku: str = ""):
    self.count = int(self.count) + 1
    plan = scene("cart-pop").enter(f"#{self.id}", rise.enter(ms=160))
    return update_with(self, plan, extra_ops=[notify(f"Added {sku}")])
```

### morph_play helper

<a id="co-morph-play"></a>

morph_play emits a morph of the target, then the plan ops. Still obey XOR: do not also pass html= on the same target.

```python
from ux_compose import morph_play, scene, rise

@action(caps=())
def add(self, sku: str = ""):
    self.count = int(self.count) + 1
    plan = scene("cart-pop").enter(f"#{self.id}", rise.enter(ms=160))
    return morph_play(self.id, plan)
```

### scan / validate / mount surfaces

<a id="co-surfaces"></a>

Define-in-module only: imported classes are not auto-registered. ≤1 page owner per file. Extra renderables become fragments (no URL).

```python
from pathlib import Path
from ux_compose import App, scan_surfaces, validate_surfaces, mount_surfaces

root = Path(".")
found = scan_surfaces(root, base_directory="routes")
validate_surfaces(found)   # fail-closed id / path clashes

app = App.boot("Shop", level=1)
bundle = mount_surfaces(
    package_dir=root,
    base_directory="routes",
    compose_app=app,
    fail_closed=True,
    bind_pages=False,      # set True + asgi_app= to bind HTTP pages
)
print(list(bundle.surfaces), bundle.errors)
```

### build() composition root

<a id="co-build"></a>

One place to set host + live plane. Authors never implement adapters (Invisible Strategy).

```python
from pathlib import Path
from ux_compose import build

app, asgi, bundle = build(
    Path(__file__).parent,
    name="Shop",
    host="auto",    # auto | fastapi | asgi
    live="auto",    # auto | channel | null
    level="auto",
    base="routes",
)
print(app.name, app.level, bundle)
```

### use_host / use_channel / use_motion

<a id="co-host"></a>

L1 code remains correct at L2/L3 — zero rewrite. Authors do not import ux_channel outside compose wire/.

```python
from ux_compose import App, Level

app = App.boot("Shop", level=1)
print(int(app.level), app.level.label)   # 1 offline interactive

app.use_host("fastapi")                  # auto | fastapi | asgi
# app.use_channel(asgi_app=api)          # Level 2 — Isolation-safe wire/ import
# app.use_motion()                       # Level 3
# app.use_cek(mode="adapt")              # optional; mode="require" raises if missing

assert Level.L1.value == 1
```


### HTML / JSON / stream from render()

<a id="co-payload"></a>

Payload type picks media type. Law: [reference/host.md](../reference/host.md).
Recipes: [HOST.md](HOST.md).

```python
class Hello:
    def render(self):
        return "<div id='hello'>hi</div>"          # HTMLResponse

class Health:
    def render(self):
        return {"ok": True}                        # JSON, no JSONResponse()

class Ticks:
    def render(self):
        def gen():
            yield "<div>a</div>"
            yield "<div>b</div>"
        return gen()                               # StreamingResponse
```

Extra APIs stay on the FastAPI process, not on the class:

```python
app, asgi, bundle = build(PACKAGE, document=document)

@asgi.get("/api/health")
def health():
    return {"ok": True}
```


## Usage patterns

### Pattern: progressive levels 0–3

<a id="co-pattern-levels"></a>

If you are rewriting the Cart to 'go live', you have violated the contract. Attach Channel; do not fork the component.

```python
# L0  Document + static Components  (page units: DirectoryRoutes on compose)
# L1  + Behavior + MorphState + @action     ← write here first
# L2  + Channel + Caps + control()          ← App.use_channel
# L3  + Motion / Scenes                     ← App.use_motion + update_with
#
# Progressive Superpower Contract: L1 code stays correct when you unlock L2/L3.
# HTMX is never auto-attached; Document.use(Htmx()) is explicit.
```
