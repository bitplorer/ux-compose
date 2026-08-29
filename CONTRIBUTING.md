# Contributing

**First-time:** [START_HERE.md](START_HERE.md). **Map:** [docs/INDEX.md](docs/INDEX.md). **Agent contract:** [AGENTS.md](AGENTS.md).

## Setup

Python **≥ 3.11** (full stack **≥ 3.14** because ux-dom). Layout: `src/ux_compose`.

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# specialists as needed:
pip install -e ".[full]"   # or pin git URLs as in README
```

## Quality gate

```bash
make test314
# or:
PYTHONPATH=src:. pytest tests/ -q
PYTHONPATH=src:. pytest tests/regression -q   # hard-cut ownership
```

See [docs/guides/TESTING.md](docs/guides/TESTING.md) for the full matrix (unit, integration,
regression, concurrency, load, property, security).

Live showcase: **Lumen** (`apps/lumen`) via `make lumen` or
`uxcompose serve apps.lumen.app:asgi --port 8082`. Pulse / Floor / Atelier remain
as historical demos; do not extend them.

## Ownership (do not regress)

Authoritative: [docs/FLOW.md](docs/FLOW.md). Agent contract: [AGENTS.md](AGENTS.md).

| Do | Don't |
|----|-------|
| Put product lifecycle on `uxcompose` | Add `create-app` / product `build` / `serve` / `deploy` to `uxdom` |
| Import specialists; wrap at `App` | Reimplement Document / Cap / Plan IR here |
| Attach Channel via `App.use_channel(asgi_app=…)` | Import `ux_channel` from application modules |
| Keep HMR under `uxcompose serve` | Add HMR as `Document.use` |
| Document only names on `__all__` | Invent `ux.div` / `when` / `forall` / `Page` |

## Docs

| File | May contain | Must not contain |
|------|-------------|------------------|
| `README.md` | Gate | Full API, ADR bodies |
| `START_HERE.md` | 5-minute first success | Exhaustive FLOW restatement |
| `docs/FLOW.md` | Ownership law | Tutorial steps as primary form |
| `docs/guides/` | Goal-oriented recipes (CLI, serve/HMR/tunnel, DX, tests) | Conceptual essays as primary form |
| `docs/reference/` | Facts | Learning narrative as primary form |
| `docs/internals/` | Why / architecture / C4 | Step lists as primary form |
| `docs/examples/` | Worked recipes / pointers | Law |
| `docs/adr/` | Architecture decisions | Mixed how-to |
| `docs/INDEX.md` | Audience + Diátaxis routing | Empty folder trees |

Map: [docs/INDEX.md](docs/INDEX.md). Keep [docs/START_HERE.md](docs/START_HERE.md)
in sync with the root START_HERE.

## Pull requests

- Feature branches. Never commit directly to `main`. Never force-push `main`.
- Hard-cut regressions belong in `tests/regression/`.
- Docs links from README / START_HERE / INDEX must resolve.
