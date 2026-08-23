# ux-compose

**Thin pure-Python composition and delivery root** for the UX framework family.

Harnesses four specialists without re-implementing them:

| Specialist | Role |
|------------|------|
| **ux-dom** | Document SSoT, elements, runtimes (Python ≥3.14) |
| **ux-channel** | Live Caps, Intent, signed control, ASGI |
| **ux-behavior** | Offline Components, MorphState, `@action`, Cap Law |
| **ux-motion** | Scene plans, presence, Morph-then-Play |

No React. No Vue. No client SPA runtime. Server-authored, hypermedia-first, capability-secured, progressive.

> **New here?** [START_HERE.md](START_HERE.md) (5 minutes). Mental model: [docs/START_HERE.md](docs/START_HERE.md)
> **Ownership law:** [docs/FLOW.md](docs/FLOW.md)
> **Map:** [docs/INDEX.md](docs/INDEX.md)
> **Contributor / agent:** [CONTRIBUTING.md](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md)

Compose is allowed to look like “the product” to authors. It must **import** specialists, not copy them.

### Brand lines

| Layer | Name |
|-------|------|
| **PyPI / pip** | `ux-compose` |
| **Import** | `ux_compose` |
| **CLI** | **`uxcompose`** (sole product lifecycle) |
| **Version** | `0.1.0` |

### Ownership

| Owns | Does **not** own |
|------|------------------|
| Product CLI (`create-app`, `serve`, `deploy`, `doctor`) | DOM serialize / tag trees (ux-dom) |
| `App` composition, `App.mount`, delivery, HMR + tunnel under serve | Channel transport (wire/ only) |
| Page-unit mount (`routes/` + `App.mount`) | Pure-dom tooling (`uxdom`); MorphState / Cap / Plan IR implementations |

---

## Product path

```bash
uxcompose create-app myapp --level 1
cd myapp
uxcompose serve app:asgi --port 8080
uxcompose deploy --provider docker
uxcompose doctor .
```

Pure-dom tooling stays on **`uxdom`** (`doctor` · `lint` · `build` · `profile`).

---

## Audience

| You are… | Start |
|----------|--------|
| **New** | [START_HERE.md](START_HERE.md) |
| **Ownership / boundaries** | [docs/FLOW.md](docs/FLOW.md) |
| **CLI** | [docs/CLI.md](docs/CLI.md) |
| **Contributor / agent** | [CONTRIBUTING.md](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md) |
| **Need a map** | [docs/INDEX.md](docs/INDEX.md) |

---

## Quick start (Level 1)

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install "ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git"
pip install "ux-dom @ git+https://github.com/bitplorer/ux-dom.git"
```

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

app = App.boot("Shop", strict_caps=False)
app.add(Cart)
print(app.dispatch("cart.add", sku="tee"))
```

`render()` returns a **ux-dom tag tree**, not an HTML string.
Public names are `ux_compose` (`App`, `div`, `button`, …) — not a second `ux.*` namespace.

Default product layout: `routes/` page units + `App.mount` (`examples/page_unit_mount.py`).

---

## Progressive levels

| Level | What you get | Unlock |
|-------|----------------|--------|
| **0** | Static Document | `ux-dom` |
| **1** | Offline MorphState + `@action` | `+ ux-behavior` |
| **2** | Live Caps + Intent | `+ ux-channel` via `App.use_channel(asgi_app=…)` |
| **3** | Choreographed motion | `+ ux-motion` via `App.use_motion()` |

**Progressive contract:** Level 1 code remains correct at higher levels. Zero rewrite.

---

## Hard invariants

- Product lifecycle CLI is **`uxcompose` only**
- Channel attach is `App.use_channel(asgi_app=…)` — Isolation-safe
- HMR / tunnel are delivery under `uxcompose serve`, not Document APIs
- Authors do not import `ux_channel` outside compose `wire/`
- Do not reimplement specialists in this repo

Full law: [`docs/FLOW.md`](docs/FLOW.md). Examples: [`examples/README.md`](examples/README.md). Tests: `make test314`.

**Notes:** ux-dom requires Python ≥3.14 (L1 offline can run 3.11+). Optional CEK: `app.use_cek(mode="adapt")`. Headless `use_channel()` boots Channel without HTTP for mint/submit tests.

## License

MIT
