"""Back-compat path — full region-swap lesson lives in ``examples/navigation.py``."""
from __future__ import annotations

from examples.navigation import ShopView  # noqa: F401

if __name__ == "__main__":
    from examples.navigation import demo

    demo()
