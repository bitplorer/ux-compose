# Nook

A quiet house desk. Authored in ux-compose. Every kit component sits in a real room — not a kitchen-sink gallery.

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

## Run

From the ux-compose repo (Python ≥ 3.14 for the full stack):

```bash
PYTHONPATH=src:. python -m uvicorn apps.nook.server:app --host 0.0.0.0 --port 8080
```

Or the Makefile target:

```bash
make nook
```

Create-app path (page units under `routes/`):

```bash
uxcompose serve apps.nook.app:asgi --port 8080
```

## Own the kit

Product apps copy, then edit:

```bash
uxcompose add carousel
uxcompose add table
# …
```

Nook subclasses `ux_compose.kit` so the library stays the source of truth while the house owns copy, keys, and card containment.
