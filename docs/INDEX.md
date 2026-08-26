# ux-compose documentation index

**Start:** [../START_HERE.md](../START_HERE.md) · mental model: [START_HERE.md](START_HERE.md)
**Ownership SSoT:** [FLOW.md](FLOW.md)
**Docs landing:** [README.md](README.md)

This layer owns composition + product CLI (`uxcompose`).

## Folder contract (Phase 2)

| Folder | Diátaxis mode | May contain | Must not contain |
|--------|---------------|-------------|------------------|
| `docs/guides/` | how-to | Goal-oriented recipes | Conceptual essays as primary form |
| `docs/reference/` | reference | Facts, signatures, tables | Learning narrative as primary form |
| `docs/internals/` | explanation | Why, architecture, C4 | Step lists as primary form |
| `docs/examples/` | examples | Worked recipes / pointers | Law |
| `docs/adr/` | ADR | Decisions (or an index of them) | Mixed how-to |

Specialized folders (`security/`, `ship/`, `design/`, `tutorial/`, `patterns/`, `archive/`) stay.
`docs/INDEX.md` is the map. Do not add a second competing map.

It does **not** reimplement ux-dom / ux-channel / ux-behavior / ux-motion.

## Smallest example

Compose imports specialists. Pin `level=1` until you attach Channel.

```python
from ux_compose import App, Component, MorphState, action, notify, div

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return div(str(self.count), id=self.id)

    @action(caps=())
    def add(self):
        self.count = int(self.count) + 1
        return [notify("Added")]

app = App.boot("Shop", level=1)
app.add(Cart)
print(app.dispatch("cart.add"))
```

Full cookbook: [guides/SNIPPETS.md](guides/SNIPPETS.md) · product path: [guides/PATH.md](guides/PATH.md) · UI kit: [guides/UI.md](guides/UI.md).

---

## Audience

| You are… | Start (≤ 2 clicks from repo root) |
|----------|-----------------------------------|
| **First time** | [../START_HERE.md](../START_HERE.md) · [guides/PATH.md](guides/PATH.md) |
| **Ownership / boundaries** | [FLOW.md](FLOW.md) |
| **CLI surface** | [guides/CLI.md](guides/CLI.md) |
| **Pick-and-use UI** | [guides/UI.md](guides/UI.md) |
| **DX / tests** | [guides/DX.md](guides/DX.md) · [guides/TESTING.md](guides/TESTING.md) |
| **Maintainer / agent** | [../AGENTS.md](../AGENTS.md) · [reference/host.md](reference/host.md) · [../CONTRIBUTING.md](../CONTRIBUTING.md) |

```text
New user:     START_HERE → FLOW (ownership) → README quick start → examples/
Builder:      FLOW → CLI → DX → examples/README → TESTING
Maintainer:   FLOW · reference/host · resilience/MATRIX · AGENTS
```

---

## By Diátaxis mode

### Tutorial

| Doc | Topic |
|-----|--------|
| [../START_HERE.md](../START_HERE.md) | Root 5-minute path |
| [START_HERE.md](START_HERE.md) | Mental model + install (not a second 5-minute path) |
| [guides/PATH.md](guides/PATH.md) | Scaffold → build → serve → HMR → Tailwind → composition → control flow → motion → live |
| [guides/TAILWIND.md](guides/TAILWIND.md) | Production CSS how-to |
| [../examples/README.md](../examples/README.md) | Example map |
| [../examples/page_unit_mount.py](../examples/page_unit_mount.py) | Page-unit mount proof |

### How-to

| Doc | Topic |
|-----|--------|
| [guides/PATH.md](guides/PATH.md) | End-to-end product path (also tutorial) |
| [guides/HOST.md](guides/HOST.md) | HTML / JSON / stream recipes |
| [guides/TAILWIND.md](guides/TAILWIND.md) | Production Tailwind: minify, link, mount, deploy |
| [guides/UI.md](guides/UI.md) | Pick-and-use Components |
| [guides/SNIPPETS.md](guides/SNIPPETS.md) | Copy-paste App / Cart / levels / XOR / path / UI |
| [guides/README.md](guides/README.md) | How-to slot |
| [guides/CLI.md](guides/CLI.md) | Product vs pure-dom CLI |
| [guides/serve-hmr-tunnel.md](guides/serve-hmr-tunnel.md) | serve / HMR / tunnel |
| [guides/DX.md](guides/DX.md) | DX principles |
| [guides/TESTING.md](guides/TESTING.md) | Test expectations / matrix |
| [../cookbooks/PRESENCE.md](../cookbooks/PRESENCE.md) | Presence cookbook |

### Reference

| Doc | Topic |
|-----|--------|
| [guides/CLI.md](guides/CLI.md) | Command ownership table |
| `src/ux_compose/__init__.py` | Public names (`__all__`) |
| [reference/host.md](reference/host.md) | Clock A: payload law, path law, file map, future protocol |
| [resilience/MATRIX.md](resilience/MATRIX.md) | Resilience matrix |

### Explanation

| Doc | Topic |
|-----|--------|
| [FLOW.md](FLOW.md) | Ownership law (authoritative) |
| [internals/FLOW.md](internals/FLOW.md) | Same contract in the explanation slot |
| [internals/c4.md](internals/c4.md) | C4-style context |
| [adr/README.md](adr/README.md) | ADR slot |
| [adr/0001-ownership.md](adr/0001-ownership.md) | Render vs product lifecycle |
| [adr/0002-product-host.md](adr/0002-product-host.md) | Product FastAPI host (Clock A) |
| [examples/README.md](examples/README.md) | Example slot |
| [../CRITIC.md](../CRITIC.md) | Critic notes |

---

## What this package owns

| Owns | Does **not** own |
|------|------------------|
| Product CLI (`create-app`, `build`, `serve`, `deploy`, `doctor`) + Tailwind CLI finder + app asset layout (`WebAssets`) | DOM serialize / tag trees / package static (ux-dom) |
| App composition, host strategy, delivery | Channel transport (wire/ only) |
| HMR + tunnel under `uxcompose serve` | Pure-dom tooling (`uxdom doctor` / lint / profile / add) |
| Page-unit mount (`App.mount` + `routes/`) | Behavior units (ux-behavior) |

**Author rule:** Render? → **ux-dom**. Product lifecycle? → **ux-compose** only.

---

## Progressive levels

| Level | Unlock |
|-------|--------|
| **0** | Static Document — `ux-dom` |
| **1** | Offline MorphState + `@action` — `+ ux-behavior` |
| **2** | Live Caps + Intent — `+ ux-channel` via `App.use_channel(asgi_app=…)` |
| **3** | Motion — `+ ux-motion` via `App.use_motion()` |

Level 1 code remains correct at higher levels. Zero rewrite.

---

## Sister layers

| Package | Role |
|---------|------|
| [ux-dom](https://github.com/bitplorer/ux-dom) | Render / Document |
| [ux-channel](https://github.com/bitplorer/ux-channel) | Intent → Cap → Result |
| [ux-behavior](https://github.com/bitplorer/ux-behavior) | Product behavior → Ops |
| [ux-motion](https://github.com/bitplorer/ux-motion) | Presence / transition plans |

Do not flatten these layers into this repo.

## Community health

| File | Audience |
|------|----------|
| [../README.md](../README.md) | Everyone — Standard Readme door |
| [../START_HERE.md](../START_HERE.md) | First-time user |
| [../SUPPORT.md](../SUPPORT.md) | Questions |
| [../SECURITY.md](../SECURITY.md) | Security reviewers / reporters |
| [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Everyone in the issue tracker |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Contributors |
| [../GOVERNANCE.md](../GOVERNANCE.md) | How decisions are made |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Docs authors (the family contract) |
