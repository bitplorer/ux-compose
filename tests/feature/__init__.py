"""CTO feature suite — automated gates only (no product-behavior fixes).

Gates:
1. create-app scaffold hello HTML fallback is a fragment.
2. Cap mint on control() when Cap Host is live; fail-closed without cap.
3. update_with / morph fragment law (nested-shell FullShellHello characterization).
4. Optional ASGI CSS/JS smoke for GET / and /hello.

Py3.13 HAS_DOM=False — this package does not claim Morph/L3 DOM trees.
DOM-tree cases skip on Python < 3.14.
"""
