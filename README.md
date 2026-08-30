# ux-compose

[![CI](https://github.com/bitplorer/ux-compose/actions/workflows/ci.yml/badge.svg)](https://github.com/bitplorer/ux-compose/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Thin pure-Python composition and delivery root for the UX framework family.

Harnesses four specialists without re-implementing them. No React. No Vue. No client SPA runtime. Server-authored, hypermedia-first, capability-secured, progressive.

Compose is allowed to look like “the product” to authors. It must **import** specialists, not copy them.

| Specialist | Role |
|------------|------|
| **[ux-dom](https://github.com/bitplorer/ux-dom)** | Document SSoT, elements, runtimes (Python ≥3.14) |
| **[ux-channel](https://github.com/bitplorer/ux-channel)** | Live Caps, Intent, signed control, ASGI |
| **[ux-behavior](https://github.com/bitplorer/ux-behavior)** | Offline Components, MorphState, `@action`, Cap Law |
| **[ux-motion](https://github.com/bitplorer/ux-motion)** | Scene plans, presence, Morph-then-Play |

| Layer | Name |
|-------|------|
| **PyPI / pip** | `ux-compose` |
| **Import** | `ux_compose` |
| **CLI** | **`uxcompose`** (sole product lifecycle) |
| **Version** | `0.1.0` |
| **Python** | ≥ 3.11 (ux-dom full stack needs ≥3.14) |
| **License** | [MIT](LICENSE) |

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Ownership](#ownership)
- [Audience](#audience)
- [Progressive levels](#progressive-levels)
- [Hard invariants](#hard-invariants)
- [Documentation](#documentation)
- [API](#api)
- [Tests](#tests)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Install

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install "ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git"
pip install "ux-dom @ git+https://github.com/bitplorer/ux-dom.git"
```

Extras (specialists you actually use):

```bash
pip install "ux-compose[dom]"
pip install "ux-compose[behavior]"
pip install "ux-compose[motion]"
pip install "ux-compose[channel]"
pip install "ux-compose[full]"
```

Product path:

```bash
uxcompose create-app myapp --level 1
cd myapp
uxcompose serve dev
uxcompose build
uxcompose deploy --provider docker
uxcompose doctor .
```

Pure-dom tooling stays on **`uxdom`** (`doctor` · `lint` · `profile` · `add`).
Product CSS is **`uxcompose build`** (`ux_compose.tailwind` finds / ensures the CLI).

## Usage

```python
from ux_compose import (
    App, Component, MorphState, action, update_with, notify, control,
    div, h1, button,
)

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return div(
            h1(f"Items: {self.count}"),
            button("+ tee", **control("add", sku="tee")),
            id=self.id,
        )

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return update_with(self, extra_ops=[notify(f"Added {sku}")])

app = App.boot("Shop", strict_caps=False)
app.add(Cart)
print(app.dispatch("cart.add", sku="tee"))
```

`render()` returns a **ux-dom tag tree**, not an HTML string.
Public names are `ux_compose` (`App`, `div`, `button`, …) — not a second `ux.*` namespace.

Default product layout: `uxcompose create-app` + `build()` (`routes/` page units).

```python
from ux_compose.build import build
from document import document
app, asgi, bundle = build(PACKAGE, host="auto", live="auto", document=document)
```

`App.mount` remains a secondary door (tests, surfaces).

Five-minute path: [START_HERE.md](START_HERE.md). Product path: [docs/guides/PATH.md](docs/guides/PATH.md). UI kit: [docs/guides/UI.md](docs/guides/UI.md). Mental model: [docs/START_HERE.md](docs/START_HERE.md).

## Ownership

| Owns | Does **not** own |
|------|------------------|
| Product CLI (`create-app`, `build`, `serve`, `deploy`, `doctor`) + Tailwind CLI finder + app asset layout | DOM serialize / tag trees / package static (ux-dom) |
| `App` composition, `App.mount`, delivery, HMR + tunnel under serve | Channel transport (wire/ only) |
| Page-unit mount (`routes/` + `build()`); CSS minify via `ux_compose.tailwind` | MorphState / Cap / Plan IR implementations |

## Audience

| You are… | Start |
|----------|--------|
| **New** | [START_HERE.md](START_HERE.md) · [docs/guides/PATH.md](docs/guides/PATH.md) |
| **Pick-and-use UI** | [docs/guides/UI.md](docs/guides/UI.md) |
| **Ownership / boundaries** | [docs/FLOW.md](docs/FLOW.md) |
| **CLI** | [docs/guides/CLI.md](docs/guides/CLI.md) |
| **Contributor / agent** | [CONTRIBUTING.md](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md) |
| **Need a map** | [docs/INDEX.md](docs/INDEX.md) |
| **Security reviewer** | [SECURITY.md](SECURITY.md) |
| **Questions** | [SUPPORT.md](SUPPORT.md) |

## Progressive levels

| Level | What you get | Unlock |
|-------|----------------|--------|
| **0** | Static Document | `ux-dom` |
| **1** | Offline MorphState + `@action` | `+ ux-behavior` |
| **2** | Live Caps + Intent | `+ ux-channel` via `App.use_channel(asgi_app=…)` |
| **3** | Choreographed motion | `+ ux-motion` via `App.use_motion()` |

**Progressive contract:** Level 1 code remains correct at higher levels. Zero rewrite.

## Hard invariants

- Product lifecycle CLI is **`uxcompose` only**
- Channel attach is `App.use_channel(asgi_app=…)` — Isolation-safe
- HMR / tunnel are delivery under `uxcompose serve dev`, not Document APIs
- Authors do not import `ux_channel` outside compose `wire/`
- Do not reimplement specialists in this repo

Full law: [docs/FLOW.md](docs/FLOW.md). Examples: [examples/README.md](examples/README.md).

**Notes:** ux-dom requires Python ≥3.14 (L1 offline can run 3.11+). Optional CEK: `app.use_cek(mode="adapt")`. Headless `use_channel()` boots Channel without HTTP for mint/submit tests.

## Documentation

Family contract: [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md). Map: [docs/INDEX.md](docs/INDEX.md).

Canonical CLI / DX / testing pages live under `docs/guides/`. Root files such as `docs/CLI.md` are **Moved stubs** — do not cite them.

| Diátaxis | Canonical |
|----------|-----------|
| Tutorial | [START_HERE.md](START_HERE.md) · [docs/START_HERE.md](docs/START_HERE.md) · [docs/guides/PATH.md](docs/guides/PATH.md) |
| How-to | [docs/guides/UI.md](docs/guides/UI.md) · [docs/guides/SNIPPETS.md](docs/guides/SNIPPETS.md) · [docs/guides/CLI.md](docs/guides/CLI.md) · [docs/guides/serve-hmr-tunnel.md](docs/guides/serve-hmr-tunnel.md) · [docs/guides/TESTING.md](docs/guides/TESTING.md) |
| Reference | [docs/reference/README.md](docs/reference/README.md) |
| Explanation | [docs/FLOW.md](docs/FLOW.md) · [docs/internals/hmr.md](docs/internals/hmr.md) · [docs/adr/0005-serve-dev-split.md](docs/adr/0005-serve-dev-split.md) |

## API

Public names are `ux_compose.__all__` (re-exported specialists + compose’s own):

| Export | Role |
|--------|------|
| `App` | Composition root: `boot`, `add`, `mount`, `use_channel`, `use_motion`, `dispatch` |
| `Component`, `MorphState`, `RefState`, `action`, `bind`, `control`, `notify`, `update_with` | Behavior surface (via ux-behavior) |
| `div`, `h1`, `button`, … | Tag constructors (via ux-dom, when installed) |
| `scene`, `fade`, `rise`, `morph_play` | Motion surface (via ux-motion, when installed) |
| `Surface`, `mount_surfaces`, `scan_surfaces` | Surface bundles |
| `doctor`, `DoctorResult`, `Level` | DX |
| CLI `uxcompose` | `ux_compose.cli:main` |

## Tests

```bash
make test314
```

## Security

Compose’s security is the union of the levels you enabled. Do not import `ux_channel` from product code. Reporting: [SECURITY.md](SECURITY.md).

## Contributing

PRs are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Questions: [SUPPORT.md](SUPPORT.md). Governance: [GOVERNANCE.md](GOVERNANCE.md). History: [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).
