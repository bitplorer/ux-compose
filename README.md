# ux-compose

**Thin pure-Python composition and delivery root** for the UX framework family.

Harnesses four specialists without re-implementing them:

| Specialist | Role |
|------------|------|
| **ux-dom** | Document SSoT, elements, runtimes (Python ≥3.14) |
| **ux-behavior** | Offline Components, MorphState, `@action`, Cap Law |
| **ux-channel** | Live Caps, Intent, signed control, ASGI |
| **ux-motion** | Scene plans, presence, Morph-then-Play |

No React. No Vue. No client SPA runtime. Server-authored, hypermedia-first, capability-secured, progressive.

> **New here?** → [`docs/START_HERE.md`](docs/START_HERE.md)
> **Ownership law (authoritative):** [`docs/FLOW.md`](docs/FLOW.md)
> **Full docs index:** [`docs/README.md`](docs/README.md)

### Brand lines

| Layer | Name |
|-------|------|
| **PyPI / pip** | `ux-compose` |
| **Import** | `ux_compose` |
| **CLI** | **`uxcompose`** (sole product lifecycle) |

---

## Product path

```bash
uxcompose create-app myapp --level 1
cd myapp
uxcompose serve app:asgi --port 8080
uxcompose deploy --provider docker
uxcompose doctor .
```

Pure-dom tooling stays on **`uxdom`** (`doctor` · `lint` · `build` · `profile`) — not product scaffold/serve.

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

Default product layout: `routes/` page units + `App.mount` (see START_HERE and `examples/page_unit_mount.py`).

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

Full law: [`docs/FLOW.md`](docs/FLOW.md).

---

## Examples & apps

Full map: [`examples/README.md`](examples/README.md).

```bash
PYTHONPATH=src:. python examples/foundation.py
PYTHONPATH=src:. python examples/page_unit_mount.py
PYTHONPATH=src:. uxcompose serve apps.pulse.server:app --port 8080
PYTHONPATH=src:. uxcompose serve apps.atelier_studio.server:app --port 8080
```

| Group | Entry |
|-------|--------|
| Foundation / chrome / forms / commerce | `examples/*.py` |
| Page-unit mount (product path) | `examples/page_unit_mount.py` |
| Playable pattern host | `apps/atelier_studio` |
| Linen shop (L1→L3 same Cart) | `apps/atelier_shop` |

Cookbook: `cookbooks/PRESENCE.md`.

---

## Documentation

| Doc | Topic |
|-----|--------|
| [docs/START_HERE.md](docs/START_HERE.md) | New-user path |
| [docs/FLOW.md](docs/FLOW.md) | Ownership law (SSoT) |
| [docs/CLI.md](docs/CLI.md) | Product vs pure-dom CLI |
| [docs/DX.md](docs/DX.md) | DX principles |
| [docs/TESTING.md](docs/TESTING.md) | Test expectations |
| [docs/README.md](docs/README.md) | Full index |

---

## Tests

```bash
make test314
# or: python -m pytest tests/ -q
```

## Known notes

- **ux-dom** requires Python ≥3.14. Level 1 offline can run on 3.11+ with shims / behavior alone.
- Optional CEK: `app.use_cek(mode="adapt")` — degrades if `cek_host` is absent; `require` fails closed.
- Headless `use_channel()` boots Channel without HTTP for mint/submit tests.

## License

MIT
