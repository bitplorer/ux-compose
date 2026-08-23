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

---

## Audience

| You are… | Start (≤ 2 clicks from repo root) |
|----------|-----------------------------------|
| **First time** | [../START_HERE.md](../START_HERE.md) |
| **Ownership / boundaries** | [FLOW.md](FLOW.md) |
| **CLI surface** | [guides/CLI.md](guides/CLI.md) |
| **DX / tests** | [guides/DX.md](guides/DX.md) · [guides/TESTING.md](guides/TESTING.md) |
| **Maintainer / agent** | [../AGENTS.md](../AGENTS.md) · [../CONTRIBUTING.md](../CONTRIBUTING.md) |

```text
New user:     START_HERE → FLOW (ownership) → README quick start → examples/
Builder:      FLOW → CLI → DX → examples/README → TESTING
Maintainer:   FLOW · resilience/MATRIX · AGENTS
```

---

## By Diátaxis mode

### Tutorial

| Doc | Topic |
|-----|--------|
| [../START_HERE.md](../START_HERE.md) | Root 5-minute path |
| [START_HERE.md](START_HERE.md) | Mental model + install (not a second 5-minute path) |
| [../examples/README.md](../examples/README.md) | Example map |
| [../examples/page_unit_mount.py](../examples/page_unit_mount.py) | Page-unit mount proof |

### How-to

| Doc | Topic |
|-----|--------|
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
| [resilience/MATRIX.md](resilience/MATRIX.md) | Resilience matrix |

### Explanation

| Doc | Topic |
|-----|--------|
| [FLOW.md](FLOW.md) | Ownership law (authoritative) |
| [internals/FLOW.md](internals/FLOW.md) | Same contract in the explanation slot |
| [internals/c4.md](internals/c4.md) | C4-style context |
| [adr/README.md](adr/README.md) | ADR slot |
| [adr/0001-ownership.md](adr/0001-ownership.md) | Render vs product lifecycle |
| [examples/README.md](examples/README.md) | Example slot |
| [../CRITIC.md](../CRITIC.md) | Critic notes |

---

## What this package owns

| Owns | Does **not** own |
|------|------------------|
| Product CLI (`create-app`, `serve`, `deploy`, `doctor`) | DOM serialize / tag trees (ux-dom) |
| App composition, host strategy, delivery | Channel transport (wire/ only) |
| HMR + tunnel under `uxcompose serve` | Pure-dom tooling (`uxdom doctor` / lint / build) |
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
