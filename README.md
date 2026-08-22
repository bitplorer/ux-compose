# ux-compose

**Thin pure-Python composition root** for the UX framework family.

Harnesses four specialists without re-implementing them:

| Specialist | Role |
|------------|------|
| **ux-dom** | Document SSoT, elements, runtimes (Python ≥3.14) |
| **ux-behavior** | Offline Components, MorphState, @action, Cap Law |
| **ux-channel** | Live Caps, Intent, signed control, ASGI |
| **ux-motion** | Scene Plans, presence, Morph-then-Play |

No React. No Vue. No client runtime. Server-authored, hypermedia-first, capability-secured, progressive.

## Progressive levels

| Level | What you get | Unlock |
|-------|----------------|--------|
| **0** | Static Document | `pip install ux-dom` (Py≥3.14) |
| **1** | Offline interactive + MorphState + @action | `pip install ux-behavior` |
| **2** | Live Caps + Intent | `+ ux-channel` + `App.use_channel(asgi_app=…)` |
| **3** | Choreographed motion | `+ ux-motion` + `App.use_motion()` |

**Progressive Superpower Contract:** code written at Level 1 remains correct and unchanged at higher levels. Zero rewrite.

## Default product path

Filesystem page units under `routes/` + `App.mount` (DirectoryRouter via RouterHooks):

```text
myapp/
  app.py
  routes/
    hello.py          # page unit: class Hello (stem match)
```

```python
from pathlib import Path
from ux_compose import App

app = App.boot("Shop", level=1)
bundle = app.mount(Path(__file__).parent, asgi_app=api, base="routes")
# offline still works:
app.dispatch("hello.inc")
# doctor can read the sealed bundle:
from ux_compose import doctor
doctor([], fail=False, bundle=bundle)
```

Scaffold emits this layout:

```bash
python -m ux_compose.cli create-app ./myapp --level 1
```

Runnable proof: `PYTHONPATH=src:. python examples/page_unit_mount.py`

## Quick start

```bash
# Full stack (recommended): Python ≥3.14
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install "ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git"
pip install "ux-motion @ git+https://github.com/bitplorer/ux-motion.git"
pip install "ux-channel @ git+https://github.com/bitplorer/ux-channel.git#subdirectory=python"
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

    @action(caps=("orders.place",))
    def checkout(self):
        return [notify("Placed")]

app = App.boot("Shop", strict_caps=False)
app.add(Cart)
print(app.dispatch("cart.add", sku="tee"))
```

`render()` returns a **ux-dom tag tree**, not an HTML string. Compose Component is a Behavior unit (MorphState, `@action`) that *produces* trees; it does not subclass ux-dom Component. Freeze on that class is fixable; a shared MRO with tree verbs (`add`/`remove`/`get`/`clear`) is not. HTML strings still work at L1 without ux-dom.
Live Caps (Level 2) — checkout succeeds **only** with a real Channel-minted Cap:

```python
from fastapi import FastAPI
asgi = FastAPI()
app = App.boot("Shop", strict_caps=True)
app.add(Cart)
app.use_channel(asgi_app=asgi)   # Isolation door; never pass Channel as asgi
refused = app.submit_intent("cart.checkout")          # missing Cap → not ok
placed  = app.submit_intent("cart.checkout", mint=True)  # Host mints Cap
```

`App.use_channel(asgi_app=fastapi)` lets **Behavior.attach** own `Channel.boot`, so
`include_router` lands on FastAPI (not on Channel). Product code never imports
`ux_channel`.

## Hard invariants (never broken)

- **Isolation Law** — product code never imports `ux_channel` / CEK; only `wire/` may
- **Document SSoT** — exactly one Document owns the HTML shell
- **XOR Law** — morph vs `scene.enter(html=)` are exclusive
- **Cap Law** — protected actions require Caps (fail-closed offline under `strict_caps`)
- **Ops-as-data** — inspectable Op / Motion Plan
- **Morph-then-Play** — morph Op precedes `transition.play`
- **Cold import** — `import ux_compose` never pulls channel/CEK

## CLI

```bash
python -m ux_compose.cli doctor --no-fail
python -m ux_compose.cli create-app ./myapp --level 1
```

## Product apps

`apps/pulse` — **full-featured live showcase** of the locked product path:
page units (`routes/`), App.mount, MorphState/RefState, Cap-gated checkout,
interactive lab, doctor evidence, progressive channel/motion.

```bash
PYTHONPATH=src:. uvicorn apps.pulse.server:app --host 0.0.0.0 --port 8080
# offline smoke: PYTHONPATH=src:. python apps.pulse.server.py
```

`apps/atelier_shop` — linen & object shop: cart, confirm modal, Document shell,
live Cap checkout. Same Cart class at L1 and L3.

```bash
PYTHONPATH=src:. python -m uvicorn apps.atelier_shop.server:app --host 0.0.0.0 --port 8080
```

## Examples

Full-length, commented modules covering **99% of product UI**. Map: [`examples/README.md`](examples/README.md).

Playable host: `apps/atelier_studio` (Atelier of Patterns). Product shop at `/shop`.

| Group | File |
|-------|------|
| Foundation | `examples/foundation.py` — counter, toggle, Morph vs Ref, return algebra |
| Chrome | `examples/chrome.py`, `examples/modal.py`, `examples/shell.py` |
| Overlays | `examples/overlays.py` — toasts, confirm, lightbox, palette, banner |
| Forms | `examples/forms.py`, `examples/fields.py` — validation, wizard, typeahead, every remaining input |
| Collections | `examples/lists.py`, `examples/table_board.py`, `examples/feeds.py` |
| Navigation | `examples/navigation.py` |
| Commerce | `examples/cart.py`, `examples/commerce_more.py`, stepper/rating in `examples/systems.py` |
| Live Caps | `examples/live_caps.py` |
| Motion | `examples/motion_xor.py` — XOR, Morph-then-Play, share |
| Systems | `examples/systems.py`, `examples/ops.py` — chat, calendar, KPI, settings, presence |
| Host | `examples/document_boot.py`, `examples/live_asgi.py`, `examples/cart_document.py` |
| Page-unit mount | `examples/page_unit_mount.py` — locked product path + doctor bundle evidence |

```bash
PYTHONPATH=src:. python examples/foundation.py
PYTHONPATH=src:. python examples/page_unit_mount.py
PYTHONPATH=src:. uvicorn apps.pulse.server:app --host 0.0.0.0 --port 8080
PYTHONPATH=src:. uvicorn apps.atelier_studio.server:app --app-dir . --host 0.0.0.0 --port 8080
```

## Cookbooks

- `cookbooks/PRESENCE.md` — list reorder + shared-element via `scene.share`

## Tests

```bash
# Full stack on Python 3.14
/tmp/ux314venv/bin/python -m pytest tests/ -q
# or: make test314
```

## Known notes

- **ux-dom** requires Python ≥3.14. Level 1 offline works on 3.11+ with pure shims or `ux-behavior` alone.
- **Channel FastAPI host**: `App.use_channel(asgi_app=fastapi)` is the Isolation-safe attach. Do not pass a Channel instance as `asgi`. Headless `use_channel()` boots Channel without HTTP for mint/submit tests.
- Optional CEK: `app.use_cek(mode="adapt")` — degrades if `cek_host` is absent; `require` fails closed.

## License

MIT
