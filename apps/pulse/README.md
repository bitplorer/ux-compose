# Pulse

The locked live showcase for the ux-compose product path. Page units under `routes/`, `build(document=)`, additive L0–L3 attach, Isolation Law.

Python **≥ 3.14** with the pinned specialist stack (ux-dom, ux-channel, ux-behavior, ux-motion). Missing specialists fail loud.

**Feature matrix** (every specialist happy path): [MATRIX.md](MATRIX.md). Room: `GET /matrix`.

## Rooms

| Path | What |
|------|------|
| `/` Home | Document trees, `control()`, pulse counter |
| `/shop` Shop | Commerce + Cap-gated checkout |
| `/lab` Lab | Tabs, counter, form, toast |
| `/matrix` Matrix | bind + Cap HTTP + morph-then-fade/rise/slide + extract_by_id |
| `/settings` Settings | `doctor()` capabilities |

## Run

From the ux-compose repo (Python ≥ 3.14, `pip install -e ".[dev,serve]"`):

```bash
make pulse
```

or:

```bash
PYTHONPATH=src:. uxcompose serve dev apps.pulse.server:app --host 0.0.0.0 --port 8080
#   uxcompose serve prod apps.pulse.server:app
```

uvicorn target (same ASGI):

```bash
PYTHONPATH=src:. python -m uvicorn apps.pulse.server:app --host 0.0.0.0 --port 8080
```

Smoke:

```bash
curl -s localhost:8080/api/health
curl -s localhost:8080/api/doctor
curl -s localhost:8080/matrix
curl -s localhost:8080/ux-channel/health
```

## Locks

```bash
PYTHONPATH=src:. python -m pytest tests/integration/test_pulse_feature_matrix.py -q
# or:
make test-pulse-matrix
```

HTTP (httpx ASGITransport) is the merge bar. See [MATRIX.md](MATRIX.md) for trigger → evidence per row.
