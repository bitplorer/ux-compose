# ux-compose documentation index

**Start:** [../START_HERE.md](../START_HERE.md) · longer: [START_HERE.md](START_HERE.md)
**Ownership SSoT:** [FLOW.md](FLOW.md)
**Docs landing:** [README.md](README.md)

This layer owns composition + product CLI (`uxcompose`).
It does **not** reimplement ux-dom / ux-behavior / ux-channel / ux-motion.

---

## Audience

| You are… | Start (≤ 2 clicks from repo root) |
|----------|-----------------------------------|
| **First time** | [../START_HERE.md](../START_HERE.md) |
| **Ownership / boundaries** | [FLOW.md](FLOW.md) |
| **CLI surface** | [CLI.md](CLI.md) |
| **DX / tests** | [DX.md](DX.md) · [TESTING.md](TESTING.md) |
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
| [START_HERE.md](START_HERE.md) | Docs copy of the new-user path |
| [../examples/README.md](../examples/README.md) | Example map |
| [../examples/page_unit_mount.py](../examples/page_unit_mount.py) | Page-unit mount proof |

### How-to

| Doc | Topic |
|-----|--------|
| [CLI.md](CLI.md) | Product vs pure-dom CLI |
| [DX.md](DX.md) | DX principles |
| [TESTING.md](TESTING.md) | Test expectations / matrix |
| [../cookbooks/PRESENCE.md](../cookbooks/PRESENCE.md) | Presence cookbook |

### Reference

| Doc | Topic |
|-----|--------|
| [CLI.md](CLI.md) | Command ownership table |
| `src/ux_compose/__init__.py` | Public names (`__all__`) |
| [resilience/MATRIX.md](resilience/MATRIX.md) | Resilience matrix |

### Explanation

| Doc | Topic |
|-----|--------|
| [FLOW.md](FLOW.md) | Ownership law (authoritative) |
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
| [ux-dom](https://github.com/bitplorer/ux-dom) | Render / Document / DirectoryRoutes |
| [ux-behavior](https://github.com/bitplorer/ux-behavior) | Offline components, actions, state planes |
| [ux-channel](https://github.com/bitplorer/ux-channel) | Intent → Cap → Result |
| [ux-motion](https://github.com/bitplorer/ux-motion) | Server-authored presence / transition plans |
