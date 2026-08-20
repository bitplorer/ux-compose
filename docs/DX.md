# ux-compose DX

Compose is a **progressive composition root**. Its CLI is a **shim** over specialist
DX (ux-dom, ux-behavior, ux-motion, ux-channel) — it does not re-implement
DirectoryRouting, Tailwind resolution, or `add` generators.

## Mental model

```text
uxcompose create-app / serve / doctor
        │
        ├─ probe specialists (find_spec + CLI on PATH)
        ├─ prefer specialist ceremony when present (uxdom create-app / serve / add)
        └─ always keep Isolation + Progressive Superpower
```

| Level | Unlock | Package |
|-------|--------|---------|
| L0 | Static Document / tags | ux-dom (optional) |
| L1 | Offline Components + MorphState + `@action` | ux-behavior |
| L2 | Live Caps + Intent | + ux-channel |
| L3 | Scene Plans + Morph-then-Play | + ux-motion |

**Progressive Superpower Contract:** code written at Level 1 remains correct
and unchanged when Channel or Motion unlock. Zero rewrite.

**Isolation Law:** product modules never import `ux_channel` or CEK. The only
door is `ux_compose.wire/` via `App.use_channel` / `App.use_motion`.

## Commands

```bash
uxcompose doctor [path ...] [--no-fail]
uxcompose create-app <dir> [--name NAME] [--level 0|1|2|3] [--template minimal|host|dom] [--force]
uxcompose serve|dev|start|build|add ...   # shim → uxdom when installed
```

### create-app templates

| Template | What you get | When to use |
|----------|--------------|-------------|
| **minimal** | `app.py` + README + `.ux_compose.json` | Offline Component experiments |
| **host** | FastAPI host + components + `static/css` + `assets/css/input.css` | Product hosts (atelier-style); always available |
| **dom** | Prefer `uxdom create-app`, inject `app/compose_boot.py` + Counter; **falls back to host** if uxdom CLI absent | Full DirectoryRouting tree when ux-dom is installed |

Scaffold never hard-fails because a specialist is missing. Doctor later teaches unlocks.

### host tree

```text
myapp/
├── server.py                 # App.boot + use_channel/use_motion via wire/
├── components.py             # Progressive Component (Isolation-safe)
├── static/css/app.css        # design-token snapshot (FileResponse only)
├── assets/css/input.css      # Tailwind authoring path
├── README.md
└── .ux_compose.json          # name, level, template, specialists_at_create
```

### dom tree (when uxdom CLI present)

Standard ux-dom layout (`app/main.py`, `app/document.py`, `app/routes/`, …) plus:

- `app/compose_boot.py` — `boot_compose(asgi_app=app, level=N)`
- `app/components/counter.py` — progressive Counter stub

## doctor

Reports:

1. Progressive level available (from installed packages)
2. Capability matrix (ux-dom / behavior / motion / channel + CLI paths)
3. Unlock teaching for the next level
4. Isolation AST scan + dual-Document heuristic (fail-closed unless `--no-fail`)

## serve shim

1. If `uxdom` is on PATH → `os.execvp` into `uxdom serve|dev|start|…`
2. Else if `server.py` in cwd → suggest / run `uvicorn server:app`
3. Else teaching message to install ux-dom or scaffold a host

## Probe API (library)

```python
from ux_compose.dx import probe

pr = probe()
pr.specialists          # {"ux_dom": bool, ...}
pr.level_available      # 0–3
pr.has_dom_cli          # uxdom binary present
pr.unlock_messages(requested_level=3)
```

## What compose deliberately does not own

- DirectoryRouting / file-based routes → ux-dom
- Tailwind CLI resolver / `uxdom build` → ux-dom
- `uxdom add component|route|xelement|ui` → ux-dom
- Channel wire protocol / CEK → ux-channel (behind `wire/` only)
- Scene IR / player scripts → ux-motion

## Golden path

```bash
pip install "ux-compose[full]"   # or progressive extras
uxcompose create-app myapp --template host --level 2
cd myapp
uxcompose doctor . --no-fail
uvicorn server:app --reload --port 8080
# when ux-dom is installed:
#   uxcompose create-app shop --template dom --level 3
#   cd shop && uxcompose serve
```
