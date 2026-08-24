# ux-compose

[![CI](https://github.com/bitplorer/ux-compose/actions/workflows/ci.yml/badge.svg)](https://github.com/bitplorer/ux-compose/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Thin pure-Python composition and delivery root for the UX framework family. Imports specialists; does not copy them. No React. Server-authored, hypermedia-first, capability-secured, progressive.

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
- [Documentation](#documentation)
- [API](#api)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Install

```bash
pip install -e .
pip install "ux-compose[full]"   # ux-dom + ux-behavior + ux-motion + ux-channel
uxcompose create-app myapp --level 1
cd myapp
uxcompose serve app:asgi --port 8080
uxcompose doctor .
```

Pure-dom tooling stays on **`uxdom`**.

## Usage

```python
from ux_compose import App, Component, MorphState, action, update_with, notify, control, div, h1, button

class Cart(Component):
    id = "cart"
    count = MorphState(0)
    def render(self):
        return div(h1(f"Items: {self.count}"), button("+ tee", **control("add", sku="tee")), id=self.id)
    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return update_with(self, extra_ops=[notify(f"Added {sku}")])

app = App.boot("Shop", strict_caps=False)
app.add(Cart)
print(app.dispatch("cart.add", sku="tee"))
```

`render()` returns a **ux-dom tag tree**. Five minutes: [START_HERE.md](START_HERE.md).

## Ownership

| Owns | Does **not** own |
|------|------------------|
| Product CLI (`create-app`, `serve`, `deploy`, `doctor`) | DOM serialize (ux-dom) |
| `App` composition, HMR + tunnel under serve | Channel transport (wire/ only) |
| Page-unit mount | MorphState / Cap / Plan IR implementations |

## Audience

| You are… | Start |
|----------|--------|
| **New** | [START_HERE.md](START_HERE.md) |
| **Ownership** | [docs/FLOW.md](docs/FLOW.md) |
| **CLI** | [docs/guides/CLI.md](docs/guides/CLI.md) |
| **Map** | [docs/INDEX.md](docs/INDEX.md) |
| **Security** | [SECURITY.md](SECURITY.md) |

## Progressive levels

| Level | Unlock |
|-------|--------|
| **0** | ux-dom |
| **1** | + ux-behavior |
| **2** | + ux-channel via `App.use_channel(asgi_app=…)` |
| **3** | + ux-motion via `App.use_motion()` |

Level 1 code remains correct at higher levels. Zero rewrite.

## Documentation

Family contract: [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md). Canonical CLI is `docs/guides/CLI.md` — not the Moved stub `docs/CLI.md`.

## API

`ux_compose.__all__`: `App`, `Component`, `MorphState`, `action`, `control`, `notify`, `update_with`, tag constructors, `scene`/`fade`/`rise` when motion is installed, `doctor`, CLI `uxcompose`.

## Security

Union of the levels you enabled. Do not import `ux_channel` from product code. [SECURITY.md](SECURITY.md).

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SUPPORT.md](SUPPORT.md) · [GOVERNANCE.md](GOVERNANCE.md) · [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).
