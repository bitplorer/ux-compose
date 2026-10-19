# Contributing

**First-time:** [START_HERE.md](START_HERE.md). **Map:** [docs/INDEX.md](docs/INDEX.md). **Agent contract:** [AGENTS.md](AGENTS.md).

## Setup

Python **≥ 3.14**. Hard-deps: pinned ux-dom / ux-channel / ux-behavior /
ux-motion. Layout: `src/ux_compose`. Missing specialists fail loud — there
is no optional-package unlock ladder.

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# Specialists are hard dependencies (no per-specialist extras).
```

## Quality gate

```bash
make test314
# or:
PYTHONPATH=src:. pytest tests/ -q
PYTHONPATH=src:. pytest tests/regression -q   # hard-cut ownership
```

See [docs/guides/TESTING.md](docs/guides/TESTING.md) for the full matrix (unit, integration,
regression, concurrency, load, security).

## Dependency cooldown

A PyPI release may enter CI only after it has been on PyPI for 14 days.
`.github/workflows/ci.yml` computes a UTC timestamp 14 days before the run
and passes it to every `uv pip install --exclude-newer`. That is the pip,
setuptools, and wheel install, and `uv pip install -e ".[dev]"`. Git SHA
siblings (ux-dom, ux-channel, ux-behavior, ux-motion) stay pinned by commit.
Their PyPI dependencies use the same cutoff.

`ci/check_dependency_cooldown.py` runs after the install. It checks each
installed distribution that came from PyPI and skips local, editable, and
git-SHA installs. For each remaining distribution it reads
`upload_time_iso_8601` from `https://pypi.org/pypi/<name>/<version>/json`
and fails the job if the earliest file upload is less than 14 days before
the run. The failure names the package, version, and upload time. A network
or payload failure fails closed. The checker is standard library only.

There is no override. A newer dependency waits out the 14 days, or it gets
an explicit pin in a reviewed pull request. The cutoff is CI-only. The
Makefile's local `pip install` targets (`venv314`, `specialists`) are not
under it.

Live showcase: `apps/pulse` via `uxcompose serve dev apps.pulse.server:app`.

## Ownership (do not regress)

Authoritative: [docs/OWNERSHIP.md](docs/OWNERSHIP.md). Agent contract: [AGENTS.md](AGENTS.md).

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
| `START_HERE.md` | 5-minute first success | Exhaustive OWNERSHIP restatement |
| `docs/OWNERSHIP.md` | Ownership law | Tutorial steps as primary form |
| `docs/guides/` | Goal-oriented recipes (CLI, serve/HMR/tunnel, DX, tests) | Conceptual essays as primary form |
| `docs/reference/` | Facts | Learning narrative as primary form |
| `docs/internals/` | Why / architecture / C4 | Step lists as primary form |
| `docs/examples/` | Worked recipes / pointers | Law |
| `docs/adr/` | Architecture decisions | Mixed how-to |
| `docs/INDEX.md` | Audience + Diátaxis routing | Empty folder trees |

Map: [docs/INDEX.md](docs/INDEX.md). Root 5-minute path: [START_HERE.md](START_HERE.md).
Mental model: [docs/START_HERE.md](docs/START_HERE.md) (not a second CLI recipe).

## Pull requests

- Feature branches. Never commit directly to `main`. Never force-push `main`.
- Hard-cut regressions belong in `tests/regression/`.
- Docs links from README / START_HERE / INDEX must resolve.
