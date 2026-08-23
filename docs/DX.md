# ux-compose DX

Compose owns **product lifecycle**. Specialist DX stays on the specialist.

## Mental model

```text
uxcompose create-app / serve / deploy / doctor
        │
        ├─ probe specialists (find_spec + CLI on PATH)
        ├─ boot via build() / App.mount (DirectoryRoutes + thin adapter)
        └─ Isolation + Progressive Superpower
```

| Level | Unlock | Package |
|-------|--------|---------|
| L0 | Static Document / tags + page-unit routing | ux-dom (optional, Py≥3.14) |
| L1 | Offline Components + MorphState + `@action` | ux-behavior |
| L2 | Live Caps + Intent | + ux-channel |
| L3 | Scene Plans + Morph-then-Play | + ux-motion |

**Progressive Superpower Contract:** code written at Level 1 remains correct
when Channel or Motion unlock. Zero rewrite.

**Isolation Law:** product modules never import `ux_channel` or CEK. The only
door is `ux_compose.wire/` via `App.use_channel` / `App.use_motion`.

**Ownership:** `uxdom` is pure Document tooling (`doctor`, `lint`, `build`,
`profile`, `add`). It is not a product CLI. There is no `uxdom create-app` /
`serve` / `deploy`.

## Commands

```bash
uxcompose doctor [path ...] [--no-fail]
uxcompose create-app <dir> [--name NAME] [--level auto|0-3] [--host auto|fastapi|asgi]
uxcompose serve [app:asgi] [--port 8080] [--reload|--no-reload] [--hmr] [--tunnel ngrok|cloudflare]
uxcompose deploy [--provider docker|fly|render|railway|vps|checklist]
```

### create-app

Emits the locked product path:

```text
myapp/
├── app.py                    # build(host=, live=, level=) composition root
├── routes/hello.py           # page unit (stem == class name)
└── README.md
```

Host is set **only** at the composition root. Page units never change.

## doctor

Reports:

1. Progressive level available (from installed packages via `dx.probe`)
2. Capability matrix (ux-dom / behavior / motion / channel + DirectoryRoutes)
3. Unlock teaching for the next level
4. Isolation AST scan + dual-Document heuristic (fail-closed unless `--no-fail`)

Page-unit teaching names **DirectoryRoutes + App.mount**, not DirectoryRouter.
DirectoryRouter is last-resort `host="batteries"` only.

## Probe API (library)

```python
from ux_compose.dx import probe

pr = probe()
pr.specialists          # {"ux_dom": bool, ...}
pr.level_available      # 0–3
pr.has_dom_cli          # uxdom binary present (pure-dom tooling)
pr.unlock_messages(requested_level=3)
```

## What compose deliberately does not own

- Tag serialize / Document shell → ux-dom
- Tailwind CLI resolver / `uxdom build` → ux-dom
- `uxdom add component|xelement|ui` → ux-dom (pure-dom)
- Channel wire protocol / CEK → ux-channel (behind `wire/` only)
- Scene IR / player scripts → ux-motion

## Golden path

```bash
pip install "ux-compose[full]"
uxcompose create-app myapp --host auto --level auto
cd myapp
uxcompose doctor . --no-fail
uxcompose serve app:asgi --port 8080
```
