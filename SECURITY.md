# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes (best-effort while pre-1.0) |

## Threat model

Compose’s security is the union of the levels you enabled:

| Level | Specialist | Security you get |
|-------|------------|------------------|
| 0 | ux-dom | Render + CSP stamp |
| 1 | ux-behavior | Offline Cap Law / `AuthorityError` |
| 2 | ux-channel | Live Caps, signed Intent, JTI |
| 3 | ux-motion | Plan IR (host still owns HTML escaping) |

Product code must **not** import `ux_channel` outside compose `wire/`. HMR and tunnel exist only under `uxcompose serve`.

## Reporting

GitHub Security Advisory on [bitplorer/ux-compose](https://github.com/bitplorer/ux-compose/security/advisories/new) or **bitplorer@outlook.com**. If the bug is inside a specialist, we transfer it. Do not file a public issue for unreleased details.
