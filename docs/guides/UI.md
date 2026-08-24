# UI catalog — pick-and-use Components

> **Diátaxis:** how-to · **Layer:** ux-compose
> Path: [PATH.md](PATH.md) · Map: [../INDEX.md](../INDEX.md)
> Source of truth for these shapes: repo `examples/` (foundation, chrome, modal, forms, overlays, cart, motion_xor).

Each widget is **one `Component`**. Copy the class into `routes/{stem}.py`
(stem == class name) or `app.add(TheClass)`. The same class is valid at L1
(offline `dispatch`) and L3 (`use_channel` + `use_motion`). Zero rewrite.

Public names only: `Component`, `MorphState`, `RefState`, `action`, `control`,
`bind`, `notify`, `update_with`, `div`, `button`, `span`, … from `ux_compose`.

**State rule used throughout**

| Kind | Field |
|------|--------|
| Open / value / query / named step / named band | `MorphState` (qualitative) |
| Magnitude, lists, money | `RefState` + `stamp = MorphState("idle")` |
| One-shot message | `notify(...)` |
| Protected verb | `@action(caps=("…",))` |

Channel's session plane **refuses quantity MorphState**. The live-safe form is
what the studio uses, so unlocking L2 does not rewrite the widget.

Register and drive from the backend:

```python
from ux_compose import App

app = App.boot("Shop", level=1)
app.add(Toggle, Tabs, ConfirmModal, Cart)
print(app.dispatch("toggle.flip"))
print(app.dispatch("tabs.select", tab="make"))
```

---

## Contents

- [Toggle](#toggle)
- [Tabs](#tabs)
- [Confirm modal](#confirm-modal)
- [Counter (live-safe)](#counter-live-safe)
- [Cart](#cart)

Accordion, signup form, toasts, motion box, and Card kit: [SNIPPETS.md](SNIPPETS.md)
and repo `examples/`.

---

## Toggle

Boolean MorphState is qualitative — legal on the session plane. No Caps:
flipping a switch is not an authority event.

```python
from ux_compose import (
    HAS_DOM, Component, MorphState, action, notify, update_with,
    div, h2, p, button, control,
)

class Toggle(Component):
    id = "toggle"
    on = MorphState(False)

    def render(self):
        on = bool(self.on)
        label = "Turn off" if on else "Turn on"
        kids = (
            h2("Quiet hours"),
            p("Notifications hush after dusk." if on else "Notifications reach the table."),
            button(
                label,
                type="button",
                className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50",
                **control("toggle.flip"),
            ),
        )
        if HAS_DOM:
            return div(
                *kids,
                id=self.id,
                className="rounded-2xl border border-stone-200 bg-white p-6",
                data_on="1" if on else "0",
                aria_pressed="true" if on else "false",
            )
        return str(getattr(self, "id", ""))

    @action(caps=())
    def flip(self):
        self.on = not bool(self.on)
        return update_with(self, extra_ops=[notify("on" if self.on else "off")])
```

---

## Tabs

One MorphState key. Panels keep stable ids (`#tab-cut`) so motion can stagger
later without rewrite. Opening a tab is public.

```python
from ux_compose import (
    HAS_DOM, Component, MorphState, action, notify, update_with,
    div, h2, p, section, button, control,
)

TABS = (
    ("cut", "Cut", "Tabs morph one region. They do not remount the page."),
    ("make", "Make", "Actions stay on the same Component. Motion is a Plan."),
    ("keep", "Keep", "Caps stay off chrome. Opening a tab is not authority."),
)


class Tabs(Component):
    id = "tabs"
    tab = MorphState("cut")

    def render(self):
        current = str(self.tab or "cut")
        panels = {k: (title, body) for k, title, body in TABS}
        title, body = panels.get(current, panels["cut"])
        segs = [
            button(
                label,
                type="button",
                className=(
                    "rounded-full px-3 py-2 text-sm "
                    + ("bg-stone-900 text-stone-50" if key == current else "bg-stone-100")
                ),
                **control("tabs.select", tab=key),
            )
            for key, label, _ in TABS
        ]
        kids = (
            h2("Tabs"),
            div(*segs, className="flex gap-2", role="tablist"),
            section(
                h2(title),
                p(body),
                id=f"tab-{current}",
                className="mt-4",
                role="tabpanel",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="rounded-2xl border border-stone-200 bg-white p-6")
        return str(getattr(self, "id", ""))

    @action(caps=())
    def select(self, tab: str = "cut"):
        if tab not in {k for k, _, _ in TABS}:
            tab = "cut"
        self.tab = tab
        return update_with(self, extra_ops=[notify(tab)])
```

---

## Confirm modal

Presence flag is MorphState. Payload is RefState (silent). Opening is public.
The destructive confirm is Cap-protected.

```python
from ux_compose import (
    HAS_DOM, Component, MorphState, RefState, action, notify, update_with,
    div, h2, p, button, control,
)


class ConfirmModal(Component):
    id = "demomodal"
    open = MorphState(False)
    title = RefState("Confirm")
    body = RefState("")

    def render(self):
        if not HAS_DOM:
            return str(getattr(self, "id", ""))
        if not self.open:
            return div(
                h2("Modal"),
                p("Closed. The unit keeps its id in the tree."),
                button(
                    "Open dialog",
                    type="button",
                    className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50",
                    **control(
                        "demomodal.open_modal",
                        title="Delete this piece?",
                        body="This cannot be undone.",
                    ),
                ),
                id=self.id,
                className="rounded-2xl border border-stone-200 bg-white p-6",
                data_open="0",
            )
        return div(
            h2(str(self.title)),
            p(str(self.body)),
            div(
                button("Cancel", type="button", **control("demomodal.close")),
                button("Confirm", type="button", **control("demomodal.confirm")),
                className="mt-4 flex gap-2",
            ),
            id=self.id,
            className="rounded-2xl border border-stone-200 bg-white p-6 shadow-md",
            role="dialog",
            data_open="1",
        )

    @action(caps=())
    def open_modal(self, title: str = "Confirm", body: str = ""):
        self.open = True
        self.title = title or "Delete this piece?"
        self.body = body or "This cannot be undone."
        return update_with(self, extra_ops=[notify(f"Opened: {self.title}")])

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=("orders.confirm",))
    def confirm(self):
        self.open = False
        return update_with(self, extra_ops=[notify("Confirmed")])
```

---

## Counter (live-safe)

Magnitude lives in `RefState`. A qualitative `stamp` is the dirty tick so the
unit still morphs. Reset is Cap-protected (Authority Clock).

```python
from ux_compose import (
    HAS_DOM, Component, MorphState, RefState, action, notify, update_with,
    div, h2, p, span, button, control,
)


class Counter(Component):
    id = "counter"
    n = RefState(0)
    last = RefState("")
    stamp = MorphState("idle")

    def _tick(self):
        self.stamp = "tock" if self.stamp == "tick" else "tick"

    def render(self):
        n = int(self.n or 0)
        kids = (
            h2("Counter"),
            p(span(str(n), className="text-2xl font-semibold tabular-nums")),
            div(
                button("−", type="button", **control("counter.dec")),
                button("+", type="button", **control("counter.inc", sku="tick")),
                button("Reset", type="button", **control("counter.reset")),
                className="flex gap-2",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="rounded-2xl border border-stone-200 bg-white p-6")
        return str(n)

    @action(caps=())
    def inc(self, sku: str = ""):
        self.n = int(self.n or 0) + 1
        self.last = sku or "inc"
        self._tick()
        return update_with(self, extra_ops=[notify(f"n={self.n}")])

    @action(caps=())
    def dec(self):
        self.n = max(0, int(self.n or 0) - 1)
        self.last = "dec"
        self._tick()
        return update_with(self, extra_ops=[notify(f"n={self.n}")])

    @action(caps=("admin.reset",))
    def reset(self):
        self.n = 0
        self.last = ""
        self._tick()
        return update_with(self, extra_ops=[notify("reset")])
```

---

## Cart

The elevated mental model. Public `add`, Cap-protected `checkout`. Motion is
additive — if `scene` is missing, the same action still morphs.

```python
from ux_compose import (
    HAS_DOM, Component, MorphState, RefState, action, notify, update_with,
    control, div, h1, span, button,
)

try:
    from ux_compose import scene, rise
except Exception:
    scene = rise = None


class Cart(Component):
    id = "cart"
    count = MorphState(0)
    last_sku = RefState("")

    def render(self):
        last = self.last_sku or ""
        if HAS_DOM:
            return div(
                h1(f"Items: {self.count}"),
                span(last, className="text-sm text-stone-500"),
                button(
                    "+ tee",
                    type="button",
                    className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50",
                    **control("cart.add", sku="tee"),
                ),
                id=self.id,
                className="rounded-2xl border border-stone-200 bg-white p-6",
            )
        return str(getattr(self, "id", ""))

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        self.last_sku = sku
        plan = None
        if scene is not None and rise is not None:
            try:
                plan = scene("cart-pop").enter(f"#{self.id}", rise.enter(ms=160))
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(f"Added {sku}")])

    @action(caps=("orders.place",))
    def checkout(self):
        return [notify("Checkout started")]
```

---

## More in the repo

The Atelier of Patterns (`examples/`) is the long form of this catalog:
chrome, overlays, forms, lists, feeds, navigation, commerce, systems.
See [../../examples/README.md](../../examples/README.md). Play them with
`apps/atelier_studio`.
