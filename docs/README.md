# ux-compose documentation

**Composition + delivery root** for the UX stack.
**Ownership SSoT:** [FLOW.md](FLOW.md)
**Map (audience + Diátaxis):** [INDEX.md](INDEX.md)
GitHub renders this file when you open `docs/`. The Diátaxis audience+mode map is [INDEX.md](INDEX.md).

### Brand lines

| Layer | Name |
|-------|------|
| **PyPI / pip** | `ux-compose` |
| **Import** | `ux_compose` |
| **CLI** | **`uxcompose`** |

---

## Learning path

```text
New user:     START_HERE → FLOW (ownership) → README quick start → examples/
Builder:      FLOW → CLI → DX → examples/README → TESTING
Maintainer:   FLOW · resilience/MATRIX · AGENTS
```

| Audience | Start |
|----------|--------|
| **First time** | [../START_HERE.md](../START_HERE.md) · [START_HERE.md](START_HERE.md) |
| **Ownership / boundaries** | [FLOW.md](FLOW.md) |
| **CLI surface** | [CLI.md](CLI.md) |
| **DX principles** | [DX.md](DX.md) |
| **Tests / quality** | [TESTING.md](TESTING.md) |
| **Resilience matrix** | [resilience/MATRIX.md](resilience/MATRIX.md) |
| **Contributor / agent** | [../CONTRIBUTING.md](../CONTRIBUTING.md) · [../AGENTS.md](../AGENTS.md) |
| **Full map** | [INDEX.md](INDEX.md) |

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

## Related packages

| Package | Role |
|---------|------|
| [ux-dom](https://github.com/bitplorer/ux-dom) | Render / Document / DirectoryRoutes |
| [ux-behavior](https://github.com/bitplorer/ux-behavior) | Offline components, actions, state planes |
| [ux-channel](https://github.com/bitplorer/ux-channel) | Intent → Cap → Result |
| [ux-motion](https://github.com/bitplorer/ux-motion) | Server-authored presence / transition plans |
