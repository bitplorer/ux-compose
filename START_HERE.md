# Start here — ux-compose

**Audience:** first-time users of this package (or the UX stack).
**Promise:** a running product path in minutes, then the ownership map.
**Time:** ~5 minutes to scaffold + serve; ~15 minutes for levels 0–2.

Mental model + install (not a second 5-minute path): [docs/START_HERE.md](docs/START_HERE.md).
Ownership law: [docs/FLOW.md](docs/FLOW.md). **Map:** [docs/INDEX.md](docs/INDEX.md).
**Cookbook:** [docs/guides/SNIPPETS.md](docs/guides/SNIPPETS.md) — App, Cart, levels, bind, surfaces, build(), XOR.
**Product path:** [docs/guides/PATH.md](docs/guides/PATH.md) — scaffold → serve → HMR → Tailwind → composition → control flow → motion → live.
**UI kit:** [docs/guides/UI.md](docs/guides/UI.md) — pick-and-use Components.

---

## 1. What you are installing

`ux-compose` is the **product composition and delivery** layer. It does not
re-implement DOM, behavior, channel, or motion — it harnesses them.

```text
ux-dom       → render (trees, Document, DirectoryRoutes)
ux-behavior  → offline units (MorphState, @action)
ux-channel   → live Caps (behind wire/ only)
ux-motion    → presence / transition plans
ux-compose   → create-app · serve · deploy · App.mount · HMR
```

Public imports are from `ux_compose` (`App`, `Component`, `div`, `button`, …).
There is no second `ux.*` namespace on this package.

---

## 2. Five minutes — product CLI

Python **≥ 3.14** recommended for the full stack (ux-dom requirement).

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e .    # from this repo
pip install "ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git"
pip install "ux-dom @ git+https://github.com/bitplorer/ux-dom.git"

uxcompose create-app myapp --level 1
cd myapp
uxcompose serve app:asgi --port 8080
```

Never: `uxdom create-app`, `uxdom serve`, or product HMR as a Document API.

---

## 3. First product shape

Filesystem page units under `routes/` + `App.mount`:

```text
myapp/
  app.py
  routes/
    hello.py     # page unit (stem match)
```

```python
from pathlib import Path
from ux_compose import App

app = App.boot("Shop", level=1)
bundle = app.mount(Path(__file__).parent, asgi_app=api, base="routes")
app.dispatch("hello.inc")
```

Runnable proof:

```bash
PYTHONPATH=src:. python examples/page_unit_mount.py
```

Level-1 offline (no HTTP):

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

---

## 4. Where next

| Goal | Doc |
|------|-----|
| End-to-end product path | [docs/guides/PATH.md](docs/guides/PATH.md) |
| Pick-and-use UI | [docs/guides/UI.md](docs/guides/UI.md) |
| Public-API cookbook | [docs/guides/SNIPPETS.md](docs/guides/SNIPPETS.md) |
| Ownership law (authoritative) | [docs/FLOW.md](docs/FLOW.md) |
| Mental model + install | [docs/START_HERE.md](docs/START_HERE.md) |
| CLI reference | [docs/CLI.md](docs/CLI.md) |
| DX principles | [docs/DX.md](docs/DX.md) |
| Full example map | [examples/README.md](examples/README.md) |
| Test expectations | [docs/TESTING.md](docs/TESTING.md) |
| Contributor / agent | [CONTRIBUTING.md](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md) |
| Full map | [docs/INDEX.md](docs/INDEX.md) |
