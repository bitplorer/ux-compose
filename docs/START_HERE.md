# Start here — ux-compose (mental model)

**Canonical 5-minute path (CLI + Cart):** [../START_HERE.md](../START_HERE.md).
This page is the ownership / install map, not a second golden path.
**Map:** [INDEX.md](INDEX.md).
**Cookbook:** [guides/SNIPPETS.md](guides/SNIPPETS.md) — App, Cart, levels, bind, surfaces, build(), XOR.
**Product path:** [guides/PATH.md](guides/PATH.md). **UI kit:** [guides/UI.md](guides/UI.md).

---

## 1. What you are installing

`ux-compose` is the **product composition and delivery** layer. It does not re-implement DOM, behavior, channel, or motion — it harnesses them.

```text
ux-dom       → render (trees, Document, package static)
ux-behavior  → offline units (MorphState, @action)
ux-channel   → live Caps (behind wire/ only)
ux-motion    → presence / transition plans
ux-compose   → create-app · build · serve · deploy
               DirectoryRoutes · WebAssets · Tailwind · App · HMR
```

Full map: [FLOW.md](FLOW.md).

---

## 2. Install

Python **≥ 3.14** recommended for the full stack (ux-dom requirement).

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e .    # from this repo
pip install "ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git"
pip install "ux-dom @ git+https://github.com/bitplorer/ux-dom.git"
```

Product CLI:

```bash
uxcompose create-app myapp --level 1
cd myapp
uxcompose build
uxcompose serve app:asgi --port 8080
```

---

## 3. First product shape

Filesystem page units under `routes/` + `build(document=)`:

```text
myapp/
  settings.py
  document.py
  app.py
  assets/css/input.css
  requirements.txt
  routes/
    hello.py     # page unit (stem match)
```

```python
from pathlib import Path
from ux_compose.build import build
from document import document

app, asgi, bundle = build(
    Path(__file__).parent,
    host="auto",
    live="auto",
    level=1,
    document=document,
)
app.dispatch("hello.inc")
```

Runnable proof:

```bash
PYTHONPATH=src:. python examples/page_unit_mount.py
```

---

## 4. Mental model in one table

| You want… | Use |
|-----------|-----|
| HTML / Document / CSP | **ux-dom** |
| Offline interactive component | **ux-behavior** via compose App |
| Live signed actions | `App.use_channel(asgi_app=fastapi)` |
| Motion after morph | `App.use_motion()` + ux-motion |
| Scaffold / build / serve / deploy | **`uxcompose` CLI only** |
| Page routes + CSS folders | **`ux_compose.routing` + `WebAssets`** |

HMR is `uxcompose serve`, not a Document API.

---

## 5. Progressive levels

| Level | What you get |
|-------|----------------|
| **0** | Static Document |
| **1** | MorphState + `@action` (offline) |
| **2** | Live Caps + Intent |
| **3** | Choreographed motion |

**Contract:** Level 1 code stays valid at Level 2 and 3. No rewrite.

---

## 6. Where next

| Goal | Doc |
|------|-----|
| Ownership law (authoritative) | [FLOW.md](FLOW.md) |
| CLI reference | [guides/CLI.md](guides/CLI.md) |
| DX principles | [guides/DX.md](guides/DX.md) |
| Full example map | [../examples/README.md](../examples/README.md) |
| Test expectations | [TESTING.md](TESTING.md) |
| Package gate | [../README.md](../README.md) |
| Contributor / agent | [../CONTRIBUTING.md](../CONTRIBUTING.md) · [../AGENTS.md](../AGENTS.md) |
| Full map | [INDEX.md](INDEX.md) |
