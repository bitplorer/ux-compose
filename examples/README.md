# Examples — 99% of product UI

Every pattern is one `Component`. `render()` returns a **ux-dom tag tree**.
Behavior (MorphState / RefState / `@action`) is the live unit. Tags are the
return type, not the class.

The same class is valid at L1 (offline `dispatch`) and L3 (`use_channel` +
`use_motion`). Zero rewrite.

Play them: the Atelier of Patterns host (`apps/atelier_studio`) serves every
card. Product shop lives at `/shop`.

## Encoding rule

| What | Where |
|------|--------|
| Open / value / query / named step / named band | `MorphState` (qualitative) |
| Magnitude, lists, money, ISO dates, files, digits | `RefState` + `stamp = MorphState("idle")` |
| One-shot message | `notify(...)` |
| Domain stock / money source | Host DB, never the client plane |
| Protected verb | `@action(caps=("orders.place",))` + live `submit_intent` |

Channel's session plane **refuses quantity MorphState** (ints, numeric strings).
The live-safe form is what the studio uses.

## Map

| Group | File | Cases |
|-------|------|--------|
| Foundation | `foundation.py` | Counter, toggle, Morph vs Ref, return algebra, Cap reset |
| Chrome | `chrome.py` `modal.py` `shell.py` | Tabs, accordion, dropdown, drawer, modal, app shell, breadcrumbs, bottom nav, popover, overflow |
| Overlays | `overlays.py` | Toasts, confirm, lightbox, command palette, banner |
| Forms | `forms.py` `fields.py` | Validation, wizard, typeahead, radio/checkbox, combobox, date, files, slider, OTP (Cap), password, autosave, limited note |
| Collections | `lists.py` `table_board.py` `feeds.py` | Filter+sort+stagger, optimistic, pagination, undo, table bulk, kanban, carousel, comments (Cap moderate), timeline, empty/error/retry, reorder, activity |
| Navigation | `navigation.py` | Region swap, master/detail |
| Commerce | `cart.py` `systems.py` `commerce_more.py` | Cart, quantity stepper, rating, wishlist, coupon (Cap), checkout (Cap), stock band, compare |
| Live Caps | `live_caps.py` | Fail-closed offline, mint vs refuse live |
| Motion | `motion_xor.py` | XOR, Morph-then-Play, `scene.share` |
| Systems | `systems.py` `ops.py` | Chat, inbox, tree, skeleton, consent, locale, chips, inline edit, calendar (Cap), progress, copy, settings (Cap), offline, presence, KPI, shortcuts |
| Host | `document_boot.py` `live_asgi.py` `cart_document.py` | Document SSoT, FastAPI + Isolation door |

`form_validation.py`, `list_stagger.py`, `optimistic_list.py`, `page_transition.py`
re-export the full-length modules so old paths still run.

## Residual cases (same shape, not a new verb)

Tooltip = popover with less chrome. Bottom sheet = drawer CSS. Context menu =
overflow. Infinite scroll = activity/pagination. Spreadsheet cell = inline edit.
Gantt = calendar + timeline. Polls = choice group. Address form = wizard step.
Payment card = checkout pay step. Anything new still follows the encoding rule.

## Run offline

```bash
PYTHONPATH=src:. python examples/foundation.py
PYTHONPATH=src:. python examples/fields.py
PYTHONPATH=src:. python examples/live_caps.py
```

## Laws never broken

Isolation (no `ux_channel` in these files), Document SSoT, XOR, Cap Law,
Ops-as-data, Morph-then-Play, Cold import, Progressive Superpower.
