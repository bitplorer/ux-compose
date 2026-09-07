# Testing matrix — ux-compose

> **Diátaxis:** how-to · **Canonical:** `docs/guides/TESTING.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

## Live full-featured app

**Pulse** (`apps/pulse`) is the locked product-path showcase:

- Page units under `routes/` (home, shop, lab, settings)
- `App.mount` + progressive L0–L3
- Document shell when ux-dom present
- `/api/health`, `/api/doctor`, POST `/action/{name}`

```bash
pip install -e ".[dev,serve]" fastapi uvicorn ux-dom ux-behavior

PYTHONPATH=src:. uxcompose serve dev apps.pulse.server:app --host 0.0.0.0 --port 8080
#   uxcompose serve prod apps.pulse.server:app
#   uxcompose serve dev apps.pulse.server:app --tunnel ngrok
```

Smoke:

```bash
curl -s localhost:8080/api/health
curl -s localhost:8080/api/doctor
curl -s localhost:8080/
```

Also: `apps/atelier_shop`, `apps/atelier_studio` (Makefile `shop` / `studio`).

---

## Test layers

| Layer | Path | What |
|-------|------|------|
| **Unit** | `tests/unit/` | tunnel parse, HMR client tag, deploy checklist, CLI help |
| **Integration** | `tests/integration/` | scaffold create-app, build(), Pulse build health |
| **Feature (CTO)** | `tests/feature/` | scaffold hello fragment, Cap mint / fail-closed, morph fragment law |
| **Regression** | `tests/regression/` | hard-cut ownership (no product CLI dual path) |
| **Concurrency** | `tests/concurrency/` | parallel dispatch |
| **Load / stress** | `tests/load/` | many sequential + threaded ops |
| **Property** | `tests/property/` | invariants on control/update_with |
| **Security (pen-style)** | `tests/security/` | Isolation Law, argument sanitization, path safety |
| **Legacy** | `tests/test_*.py` | existing offline / morph / doctor suites |

---

## Commands

```bash
# default (includes nested-shell fragment-law)
PYTHONPATH=src:. pytest tests/ -q

# by layer
PYTHONPATH=src:. pytest tests/unit tests/regression tests/feature -q
PYTHONPATH=src:. pytest tests/integration -q
PYTHONPATH=src:. pytest tests/concurrency tests/load -q
PYTHONPATH=src:. pytest tests/property tests/security -q

# coverage
PYTHONPATH=src:. pytest tests/ --cov=ux_compose --cov-report=term-missing -q

# markers
PYTHONPATH=src:. pytest -m "not slow" -q
PYTHONPATH=src:. pytest -m live -q   # needs fastapi / specialists
PYTHONPATH=src:. pytest -m cto_red -q --tb=short  # nested-shell fragment-law
```

Makefile:

```bash
make test
make test-matrix
make test-cto             # CTO gates (scaffold, Cap mint, fragment-law)
make test-cto-fragment-law  # nested-shell / fragment-law
make cek-repro-morph-shell  # optional sibling ../cek-auto-suite/repro_morph_shell.py
make coverage
make pulse   # live serve Pulse
```

### CTO gates (`tests/feature/`)

Automated feature suite for the product-path CTO checks. Isolation Law: no
product import of `ux_channel`. No Cap re-implementation. Py3.13
`HAS_DOM=False` — do not claim Morph/L3 DOM; DOM-tree cases skip on
Python < 3.14.

| Gate | File | Expectation |
|------|------|-------------|
| Scaffold hello HTML fallback is a fragment (`id=hello`, no document chrome) | `test_cto_scaffold_hello_fragment.py` | GREEN |
| `control()` mints Cap when Cap Host is live; official `hello.pulse` Intent/dispatch fail-closed without cap | `test_cto_cap_mint_fail_closed.py` | GREEN (live Intent skips without ux-channel) |
| Morph payload for `#X` must not embed outer shell/brand chrome | `test_cto_fragment_law.py` | GREEN (scaffold/fragment Hello + nested-shell `cto_red`) |
| GET `/` `/hello` CSS/JS presence | `test_cto_css_js_smoke.py` | GREEN source contract; ASGI GET skips without fastapi |

The nested-shell tests use an in-repo `FullShellHello` fixture that mirrors the
broken StunningCek pattern (full shell in `render()`, `update_with` targets
`#hello`). They do **not** need the stunning tree in this repo. The fixture
stays a full-shell characterization of the bad author pattern — do not rewrite
it into a fragment. Authors should still write fragment `render()`; helpers
strip the `#target` subtree as a safety net.

Optional live repro (not imported by product, not required in CI):

```bash
# clone https://github.com/bitplorer/cek-auto-suite next to ux-compose
make cek-repro-morph-shell
```

---

## Coverage policy

| Area | Target |
|------|--------|
| `cli` / `deploy` / `tunnel` / `hmr` / `serve_dev` | High (unit + integration) |
| `app` / progressive | Existing + concurrency |
| `wire/` | gated on channel install |
| Live HTTP | integration + manual / live marker |

Pen-style tests are **defensive unit checks** (sanitization, isolation), not a substitute for professional external pen-test.

---

## CI suggestion

```yaml
- run: pip install -e ".[dev]" pytest-cov
- run: PYTHONPATH=src:. pytest tests/ -q --cov=ux_compose --cov-fail-under=40
```

Raise `cov-fail-under` as specialists are pinned in CI.

See also: `docs/OWNERSHIP.md`, `docs/guides/CLI.md`, `docs/internals/hmr.md`,
`docs/reference/host.md`.

Clock A (payload law, path law, host bind) is locked in `tests/unit/test_host.py`.
Fragment live-client (document=None + Channel) is locked in
`tests/unit/test_live_client.py`. Tests speak ASGI (`tests/asgi_http.py`) —
no Starlette TestClient / httpx2.
A synthesized Document is mount-only; wrap is the author `document=`.
`App.mount` passes the same `wrap=` as `build()`.
`attach_motion()` must return instances. Do not add host behaviour that is
not covered in `test_host.py` / `test_live_client.py`.
