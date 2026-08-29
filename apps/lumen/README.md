# Lumen

The product-path showcase for ux-compose. One app. First principles.

Clock A serves the document. Clock B (Channel) morphs a card. Kit chrome stays
on `ux_compose.kit`. The Host holds the catalog. There is **no app JavaScript**.

## Why the other `apps/` exist

They are not required to use the stack.

| App | What it taught | Why it is not the path |
|-----|----------------|------------------------|
| `atelier_shop` / `atelier_studio` | Early gallery | Handmade GET `HTMLResponse`, custom JS, dual HTTP |
| `pulse` | Progressive boot | Same handmade host; tests still lock isolation |
| `nook` | Room layout | Incomplete (no `app.py`); oversold README |
| `floor` | Host seams | Clock A is right; `floor.js` reimplements Channel |

Lumen keeps Floor's seam (subclass kit, pin `id`, override `on_*`) and drops
the enhancer. `bind()` already emits `data-channel-action`. Channel's client
posts to `/ux-channel/action`. XElement is the custom-element runtime. Motion
attaches through `build()`.

## Laws kept

- `build(document=)` for GET. No `@app.get` + `HTMLResponse`.
- Extra JSON is allowed on the FastAPI process (`GET /health`).
- No `POST /act`. No `apps/lumen/static/*.js`.
- Isolation: never import `ux_channel`. Document uses `ux_dom.runtime.Channel`
  (script tags only).
- Tailwind compiled (`uxcompose build`). No `cdn.tailwindcss.com`.
- Kit cards: no viewport `sm:` inside `class_card`. Overlay cards stay free of
  `relative` / `overflow`.
- Named keys on MorphState. Quantity on RefState.

## Rooms

| Path | Kit |
|------|-----|
| `/` Hall | KPI, presence, toast, breadcrumb |
| `/folio` | Lightbox, carousel, wishlist, table, typeahead, combobox, select, dropdown, chips, pagination |
| `/chase` | Rating, kanban, timeline, slider, progress, empty, skeleton, pullrefresh, accordion, tabs |
| `/stone` | Stepper, plans, calendar, dialog, sheet, actionsheet, contextmenu, command, sidebar |
| `/gate` | Login, OTP |

Host pair: `you@lumen.test` / `pressroom1`. OTP `314159`.

## Run

Python ≥ 3.14. From the repo root:

```bash
cd apps/lumen && PYTHONPATH=../..:../../src uxcompose build
make lumen
# or:
PYTHONPATH=src:. /tmp/ux314venv/bin/python -m uvicorn apps.lumen.app:asgi --host 0.0.0.0 --port 8082
```

`GET /health` is JSON. Page GET is HTML wrapped by the author Document.
