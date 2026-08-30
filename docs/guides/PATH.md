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
7. HMR is `uxcompose serve dev`, not `Document.use`.
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

CLI is the lifecycle. Page units never know which phase they are in.

```text
create-app → author routes/ → serve dev → dispatch / doctor
         → build → unlock L2/L3 → deploy → doctor
```

| Phase | Command | You do not |
|-------|---------|------------|
| Scaffold | `uxcompose create-app` | hand-write `get()` / `HTMLResponse` |
| Prove | `app.dispatch` + `uxcompose doctor` | stand up HTTP to test Clock B |
| CSS | `uxcompose build` | compile in `serve` / `deploy` |
| Dev | `uxcompose serve dev` | `Document.use` for HMR |
| Ship | `uxcompose deploy --provider docker` | a second ASGI process |

---

## 1. Scaffold

`uxcompose` is the **only** product lifecycle CLI. `uxdom` stays pure-dom (`doctor` / `lint` / `profile` / `add`).
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
  document.py         # Document SSoT + .use(XElement, Csp); host wraps GET
  app.py              # composition root: build(host=, live=, level=, document=)
  README.md
  requirements.txt
  assets/css/input.css
  routes/
    __init__.py
    hello.py          # page unit: stem == class name; render() is a fragment
```

`--level auto` unlocks specialists that import. Pin `--level 1` until Channel is
intentional. `--host auto` prefers FastAPI if installed, else a pure ASGI adapter.

Next:

```bash
uxcompose serve dev
uxcompose doctor . --no-fail
uxcompose build
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
            f'<div id="hello"><span>{n}</span>'
            f"<button {attr_str}>+1</button></div>"
        )

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        return update_with(self, extra_ops=[notify("incremented")])
```

Page-unit law: `routes/hello.py` exports class `Hello`. The stem matches the
class. `render()` is a fragment; the host wraps Document. Host adapters are
chosen in `build(host=)`, not here. HTML / JSON / stream from `render()`:
[HOST.md](HOST.md).

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
uxcompose serve dev
# origin + ui + channel on --host 0.0.0.0 --port 8080
```

Process reload is the ui worker. Browser HMR is the live-reload client.
Channel stays in its own process. See [serve-hmr-tunnel.md](serve-hmr-tunnel.md).

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

```bash
uxcompose serve dev
# origin + ui (reload *.py) + channel (stable)
# WebSocket /__uxcompose/hmr — ui death → page reload
# sibling Tailwind --watch + HEAD /css/output.css

uxcompose serve dev --reload-dir routes
uxcompose serve prod
```

Clocks live on `serve dev`. There is no `--hmr` / `--no-reload` / `--css-watch`.
`attach_hmr` runs inside the ui worker via `asgi_factory`.

Optional client tag for shells that skip `attach_hmr`:

```python
from ux_compose.hmr import client_script_tag, HMR_PATH

# html = "... " + client_script_tag()
print(HMR_PATH)   # /__uxcompose/hmr
```

Public URL after health is green:

```bash
uxcompose serve dev --tunnel ngrok
uxcompose serve dev --tunnel cloudflare --tunnel-token "$TOKEN"
```

---

## 5. Tailwind

**Do not put CSS or client JS inside Python strings.**

1. Author utilities on the tree: `className="rounded-2xl border …"`.
2. Tokens + `@layer components` live in `assets/css/input.css`.
3. Tailwind scans **this app** (`app.py`, `routes/**/*.py`) via `@source` in
   `assets/css/input.css`. `create-app` does not emit `tailwind.config.js`.
4. Build CSS; the Document **links** the file.

```bash
uxcompose build
# writes assets/static/file/css/output.css (minified)
# live CSS watch lives on serve dev, not build --watch
```

---

## 6. Composition root

`build()` is one place to set **host** and **live**. Authors never implement
adapters.

```python
from pathlib import Path
from ux_compose import build

app, asgi, bundle = build(
    Path(__file__).parent,
    name="Shop",
    host="auto",
    live="auto",
    level="auto",
    base="routes",
)
```

| Level | You get |
|-------|---------|
| 0 | Document + static Components + DirectoryRoutes |
| 1 | + Behavior + MorphState + `@action` |
| 2 | + Channel + Caps + `control()` |
| 3 | + Motion / Scenes |

Isolation Law: product modules never `import ux_channel`.

```bash
uxcompose doctor . --no-fail
```

---

## 7. Control flow

A click posts an action name + args. The server runs `@action` and returns Ops.

Prefer `update_with(self, plan, extra_ops=[notify(...)])`.
Prefer `bind(self.add, sku="tee")` over stringly `control`.

`App.submit_intent(action, cap=..., mint=False)` is the live door. Tests stay
on `dispatch`.

---

## 8. Motion XOR

- **XOR** — `morph(target)` XOR `scene.enter(target, html=...)`. Never both.
- **Morph-then-Play** — morph Op first; `transition.play` follows.
- Plan comes from `ux_compose.scene`, never `ux_channel`.

---

## 9. Go live

Channel attaches only through compose `wire/`. Prefer `build(live="auto")`.

```bash
uxcompose serve dev
uxcompose deploy --provider docker
```

---

## Where next

| Goal | Go |
|------|----|
| Serve / HMR | [serve-hmr-tunnel.md](serve-hmr-tunnel.md) · [../internals/hmr.md](../internals/hmr.md) |
| CLI | [CLI.md](CLI.md) |
| Production CSS | [TAILWIND.md](TAILWIND.md) |
| Pick-and-use widgets | [UI.md](UI.md) |
| Ownership law | [../FLOW.md](../FLOW.md) |
| 5-minute door | [../../START_HERE.md](../../START_HERE.md) |
