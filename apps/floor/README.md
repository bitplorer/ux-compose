# Floor

A house that **feeds the kit from a Host**. Polish stays on `ux_compose.kit`.
This app only owns the books (`host.py`) and the seams (`seams.py`).

The Atelier plays stand-in copy (linen, oak). The Floor plays **walnut mallet,
flax apron, merino wrap** — same Components, different books. The ledger on
every room is the proof: clicks write the Host.

## Rooms

| Path | Kit |
|------|-----|
| `/` Desk | Kpi, Presence, Toast, Breadcrumb |
| `/shelf` | Lightbox, Carousel, Wishlist, Table, Pagination, Chips, Typeahead, Combobox, Select, Dropdown |
| `/bench` | Rating, Kanban, Timeline, Slider, Progress, Empty, Skeleton, PullRefresh, Accordion, Tabs |
| `/visit` | Stepper, Plans, Calendar, Dialog, Sheet, ActionSheet, ContextMenu, Command, Sidebar |
| `/door` | Login, OTP |

Door: `you@floor.test` / `housewood1`. OTP `246810`.

## Laws kept

- Clock A: `build(document=)`. No handmade `@app.get` + `HTMLResponse`.
- Host seam: override `_slides` / `_items` / `on_*`. No `render(attrs=)`.
- Named MorphState. Magnitudes on RefState + the House.
- No `ux_channel` import. No `sm:` inside kit cards.
- Kit files are not rewritten. Nothing is lost when the floor changes.

## Run

```bash
PYTHONPATH=src:. /tmp/ux314venv/bin/python -m uvicorn apps.floor.app:asgi --host 127.0.0.1 --port 8081
# or
make floor
```
