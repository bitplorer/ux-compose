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
# install specialists as needed
pip install -e ".[dev]" fastapi uvicorn ux-dom ux-behavior

PYTHONPATH=src:. uxcompose serve apps.pulse.server:app --host 0.0.0.0 --port 8080
#   uxcompose serve apps.pulse.server:app --no-reload --hmr
#   uxcompose serve apps.pulse.server:app --tunnel ngrok
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
| **Regression** | `tests/regression/` | hard-cut ownership (no product CLI dual path) |
| **Concurrency** | `tests/concurrency/` | parallel dispatch |
| **Load / stress** | `tests/load/` | many sequential + threaded ops |
| **Property** | `tests/property/` | invariants on control/update_with |
| **Security (pen-style)** | `tests/security/` | Isolation Law, argument sanitization, path safety |
| **Legacy** | `tests/test_*.py` | existing offline / morph / doctor suites |

---

## Commands

```bash
# default
PYTHONPATH=src:. pytest tests/ -q

# by layer
PYTHONPATH=src:. pytest tests/unit tests/regression -q
PYTHONPATH=src:. pytest tests/integration -q
PYTHONPATH=src:. pytest tests/concurrency tests/load -q
PYTHONPATH=src:. pytest tests/property tests/security -q

# coverage
PYTHONPATH=src:. pytest tests/ --cov=ux_compose --cov-report=term-missing -q

# markers
PYTHONPATH=src:. pytest -m "not slow" -q
PYTHONPATH=src:. pytest -m live -q   # needs fastapi + running specialists
```

Makefile:

```bash
make test
make test-matrix
make coverage
make pulse   # live serve Pulse
```

---

## Coverage policy

| Area | Target |
|------|--------|
| `cli` / `deploy` / `tunnel` / `hmr` | High (unit + integration) |
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

See also: `docs/FLOW.md`, `docs/guides/CLI.md`, `docs/reference/host.md`.

Clock A (payload law, path law, host bind) is locked in `tests/unit/test_host.py`.
Do not add host behaviour that is not covered there.

