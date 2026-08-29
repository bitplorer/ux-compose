# Testing matrix — ux-compose

> **Diátaxis:** how-to · **Canonical:** `docs/guides/TESTING.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

## Live full-featured app

**Lumen** (`apps/lumen`) is the product-path showcase:

- Clock A `build(document=)` — page units under `routes/`
- Kit seams: Host catalog, not stand-in copy
- Document `.use(XElement, Channel scripts, Csp)` — no app JavaScript
- `GET /health` JSON on the FastAPI process
- Tailwind via `uxcompose build` → `/css/output.css`

```bash
pip install -e ".[dev]" fastapi uvicorn ux-dom ux-behavior ux-channel ux-motion
cd apps/lumen && PYTHONPATH=../..:../../src uxcompose build
PYTHONPATH=src:. uxcompose serve apps.lumen.app:asgi --host 0.0.0.0 --port 8082
```

Smoke:

```bash
curl -s localhost:8082/health
curl -s localhost:8082/
```

Historical demos (`apps/pulse`, `apps/floor`, `apps/atelier_*`, `apps/nook`) stay for
existing tests. Do not add product path there. Floor still proves Host seams in
`tests/test_floor_host.py`; Lumen is `tests/test_lumen_host.py`.

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
make lumen   # live serve Lumen
make pulse   # historical Pulse demo
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
Tests speak ASGI (`tests/asgi_http.py`) — no Starlette TestClient / httpx2.
A synthesized Document is mount-only; wrap is the author `document=`.
`App.mount` passes the same `wrap=` as `build()`.
`attach_motion()` must return instances. Do not add host behaviour that is
not covered in `test_host.py`.

