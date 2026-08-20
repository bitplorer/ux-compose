# Presence continuity cookbook

Server-authored list reorder and shared-element motion. Product code stays
Level-1 Components; unlocking Motion is additive (Progressive Superpower).

Isolation: this cookbook never imports `ux_channel`. Scene Plans come from
`ux_compose` re-exports (`scene`, `rise`, `fade`) which load only if ux-motion
is installed.

## Laws in play

- **Morph-then-Play** — morph the identified nodes, then `transition.play`
- **XOR** — do not put `html=` on `scene.enter` for a target that also morphs
- Prefer `update_with(component, scene(...).share(...).enter(...))`

## List reorder

Keep stable ids on items (`id="item-{sku}"`). Morph the list region, then play
a stagger on the surviving nodes so presence is continuous — items that stay
do not remount.

```python
from ux_compose import Component, MorphState, action, update_with, notify

try:
    from ux_compose import scene, rise, fade
except Exception:
    scene = rise = fade = None


class Shelf(Component):
    id = "shelf"
    order = MorphState("alpha")  # "alpha" | "price"

    def render(self):
        items = self._items()
        lis = "".join(f'<li id="item-{s}">{s}</li>' for s in items)
        return f'<ul id="{self.id}">{lis}</ul>'

    def _items(self):
        catalog = [("linen", 48), ("oak", 72), ("wool", 96)]
        if self.order == "price":
            catalog = sorted(catalog, key=lambda x: x[1])
        else:
            catalog = sorted(catalog, key=lambda x: x[0])
        return [s for s, _ in catalog]

    @action(caps=())
    def sort_price(self):
        self.order = "price"
        plan = None
        if scene is not None:
            plan = (
                scene("shelf-reorder")
                .exit("#gone", fade.exit(ms=80) if fade else None)
                .stagger_in(
                    [f"#item-{s}" for s in self._items()],
                    rise.enter(ms=90) if rise else None,
                )
            )
        return update_with(self, plan, extra_ops=[notify("Sorted by price")])
```

`stagger_in` is a recipe on identified nodes. The morph patch from `render()`
is the source of HTML (XOR: the Plan carries no `html=`).

## Shared element

When an item moves from a list to a detail (or cart line to badge), name the
presence with `scene.share`. Leave and arrive selectors must exist after morph.

```python
plan = (
    scene("line-to-bag")
    .share("sku-linen", leave="#shelf-linen", arrive="#bag-linen", recipe=rise.enter(ms=120))
    .enter("#bag", rise.enter(ms=140))
)
return update_with(self, plan)
```

Morph `#bag` first (via `update_with(self, plan)`), then play. The shared
element key (`sku-linen`) is continuity identity — not a CSS class.

## Offline

Without ux-motion, `scene` is `None`. The same `@action` still morphs via
`update_with(self, None)`. Zero rewrite when you later `app.use_motion()`.

## See also

- `examples/list_stagger.py`
- `examples/page_transition.py`
- `apps/atelier_shop` — product cart uses the same `update_with` seat
