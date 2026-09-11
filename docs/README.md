# ux-compose documentation

**Composition + delivery root** for the UX stack.
**Ownership SSoT:** [OWNERSHIP.md](OWNERSHIP.md)
**Map (audience + Diátaxis):** [INDEX.md](INDEX.md)

This file is the GitHub `docs/` landing. It is not the map — [INDEX.md](INDEX.md) is.

### Brand lines

| Layer | Name |
|-------|------|
| **Install** | git clone + `pip install -e ".[serve]"` (not on PyPI) |
| **Import** | `ux_compose` |
| **CLI** | **`uxcompose`** |

---

## Learning path

```text
New user:     START_HERE → OWNERSHIP → README quick start → examples/
Builder:      OWNERSHIP → CLI → DX → examples/README → TESTING
Maintainer:   OWNERSHIP · resilience/MATRIX · AGENTS
```

| Audience | Start |
|----------|--------|
| **First time** | [../START_HERE.md](../START_HERE.md) · [START_HERE.md](START_HERE.md) |
| **Ownership / boundaries** | [OWNERSHIP.md](OWNERSHIP.md) |
| **CLI surface** | [guides/CLI.md](guides/CLI.md) |
| **DX principles** | [guides/DX.md](guides/DX.md) |
| **Tests / quality** | [guides/TESTING.md](guides/TESTING.md) |
| **Resilience matrix** | [resilience/MATRIX.md](resilience/MATRIX.md) |
| **Contributor / agent** | [../CONTRIBUTING.md](../CONTRIBUTING.md) · [../AGENTS.md](../AGENTS.md) |
| **Full map** | [INDEX.md](INDEX.md) |

---

## What this package owns

| Owns | Does **not** own |
|------|------------------|
| Product CLI (`create-app`, `build`, `serve`, `deploy`, `doctor`) + Tailwind CLI finder + app asset layout | DOM serialize / tag trees / package static (ux-dom) |
| App composition, host strategy, delivery | Channel transport (wire/ only) |
| HMR + tunnel under `uxcompose serve` (`serve_dev.py`; `cli.py` argv) | Pure-dom tooling (`uxdom doctor` / lint / profile / add) |
| Page-unit catalog scan (`App.mount` inside `build()`) + `routes/` | Behavior units (ux-behavior) |

**Author rule:** Render? → **ux-dom**. Product lifecycle? → **ux-compose** only.

---

## Progressive levels

| Level | Attach |
|-------|--------|
| **0** | Static Document — complete install (ux-dom hard dep) |
| **1** | Offline MorphState + `@action` — `App.boot` |
| **2** | Live Caps + Intent — `App.use_channel(asgi_app=…)` |
| **3** | Motion — `App.use_motion()` |

Level 1 code remains correct at higher levels. Zero rewrite. Complete
install first — not an optional-package unlock ladder.

---

## Related packages

| Package | Role |
|---------|------|
| [ux-dom](https://github.com/bitplorer/ux-dom) | Render / Document |
| [ux-behavior](https://github.com/bitplorer/ux-behavior) | Offline components, actions, state planes |
| [ux-channel](https://github.com/bitplorer/ux-channel) | Intent → Cap → Result |
| [ux-motion](https://github.com/bitplorer/ux-motion) | Server-authored presence / transition plans |
