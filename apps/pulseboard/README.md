# Pulseboard

Atelier Pulse — a live SaaS command center composed from the ux-compose kit.

Dense dark-first desk: six KPI tiles, a three-lane pipeline, activity timeline,
presence, filter chips, rating, quarter progress, forecast horizon, skeleton
loading, empty saved views, and a Cap-gated quarter close.

## Run locally

Python **≥ 3.14** with the pinned specialist stack.

From the ux-compose repo:

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

PYTHONPATH=src:. uxcompose serve apps.pulseboard.server:app --host 0.0.0.0 --port 8080
```

Or the Makefile target:

```bash
make pulseboard
```

Open http://127.0.0.1:8080

| Path | Room |
|------|------|
| `/` | Overview — full desk |
| `/pipeline` | Kanban focus |
| `/signals` | Timeline + feed |
| `/api/health` | Live surfaces |
| `/api/doctor` | Doctor report |

`uxcompose serve dev apps.pulseboard.app:asgi` is the Clock A product path
(origin + ui + channel). `serve prod` is one process, clocks off.

Atelier of Patterns also hosts the same desk at `/pulseboard` (`make studio`).

## Kit used

Subclasses of `ux_compose.kit` (library stays the source of truth):

| Kit | Pulseboard id | Role |
|-----|---------------|------|
| Stats | `desk_kpis` | Six named magnitudes |
| Timeline | `desk_timeline` | Lane-filtered activity |
| Rating | `desk_rating` | CSAT stars (named keys) |
| Progress | `desk_progress` | Quarter close bar |
| Slider | `desk_horizon` | Forecast horizon |
| EmptyState | `desk_empty` | Saved views void |
| Skeleton | `desk_skeleton` | Live refresh bars |
| ThemeSwitch | `desk_theme` | Ink / paper / house |
| Badge | `desk_chips` | Region filter |
| Feed | `desk_feed` | APG feed |
| Avatar | `desk_avatar` | Operator mark |

Companions taught by `examples/` (no kit stem):

| Pattern | Id | Encoding |
|---------|----|----------|
| Kanban | `desk_kanban` | Three RefState columns + dirty |
| Presence | `desk_presence` | Self MorphState · peers RefState |
| Wishlist | `desk_watch` | Ids in RefState + dirty |
| Cap close | `desk_close` | `quarter.close` mint · `admin.reset` refuse |

## Laws kept

- Isolation: this package never imports `ux_channel`.
- Quantity stays on `RefState`. Named lanes / theme / presence are `MorphState`.
- The brand bar lives on Document wrap. Widget morph stays a fragment.
- Cap door is Channel / `submit_intent` — not a second Cap Host.
- Tailwind `className` strings. No companion CSS per card.

## Tests

```bash
PYTHONPATH=src:. python -m pytest tests/integration/test_pulseboard_live.py tests/unit/test_pulseboard_board.py -q
```
