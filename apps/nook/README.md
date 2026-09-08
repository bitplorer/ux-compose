# Nook

A quiet house desk. Authored in ux-compose. Every kit component sits in a real room — not a kitchen-sink gallery.

Python **≥ 3.14** with the pinned specialist stack (ux-dom, ux-channel, ux-behavior, ux-motion). Missing specialists fail loud — there is no Document-absent floor. Cold install: `pip install -r requirements.txt` (VCS pins; packages are not on PyPI).

## Rooms

| Path | Kit used |
|------|----------|
| `/` Desk | Sidebar, Breadcrumb, Tabs, PullRefresh, Accordion, Command, Toast |
| `/house` House | Typeahead, Combobox, Select, Dropdown, Sheet, Carousel, Table, Pagination, ContextMenu, ActionSheet |
| `/visit` Visit | Stepper, Plans, Calendar, Dialog |
| `/enter` Door | Login, OTP |

## Laws kept

- Tailwind `class_*` strings only. No companion CSS per card.
- Named keys on MorphState. Quantity stays on RefState.
- No viewport `sm:` inside cards. Containment is `min-w-0` + `overflow-x-hidden` + wrap.
- Channel grammar already on the kit: `swipe.horizontal`, `click swipe.left/right`, `input delay:`.
- Isolation: this package never imports `ux_channel`.
- GET chrome lives on Document wrap (`document_wrap`); `render()` stays a fragment.

## Run

From the ux-compose repo (Python ≥ 3.14):

```bash
PYTHONPATH=src:. python -m uvicorn apps.nook.server:app --host 0.0.0.0 --port 8080
```

Or the Makefile target:

```bash
make nook
```

Create-app path (page units under `routes/`, composition root `app.py`):

```bash
uxcompose serve dev apps.nook.app:asgi
```

## Own the kit

Product apps copy, then edit:

```bash
uxcompose add carousel
uxcompose add table
# …
```

Nook subclasses `ux_compose.kit` so the library stays the source of truth while the house owns copy, keys, and card containment.
