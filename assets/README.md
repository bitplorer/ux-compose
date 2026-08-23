# Assets — styling contract

**Do not put CSS or client JS inside Python strings.**

## Correct path (ux-dom / Tailwind)

1. Author classes in Python (`className="…"`).
2. Design tokens + component classes live in `assets/css/input.css`.
3. Tailwind scans `apps/**`, `examples/**`, `src/**` (see `tailwind.config.js`).
4. Build:

```bash
# with standalone CLI / pytailwindcss
tailwindcss -i assets/css/input.css -o assets/css/output.css
# product CSS watch lives on uxcompose serve / uxdom build (pure-dom)
#   uxdom build
#   python -m app.tailwindcss
```

5. Document/shell **links** the generated file (`/css/output.css` or `/static/css/…`). Never `style(raw(CSS))`.

## Demo hosts (atelier_*)

Until the demo hosts are full ux-dom scaffolds, they serve a static snapshot:

- `apps/atelier_studio/static/css/atelier.css`
- `apps/atelier_shop/static/css/atelier.css`

These are the same design system extracted from the old Python strings. Prefer evolving `assets/css/input.css` and regenerating.

## Client JS

Specialist scripts only (`ux-channel.js`, `ux-motion-player.js`, idiomorph).  
Host must not inject form-intercept / applyOps patches (`ENHANCE_JS` is forbidden).
