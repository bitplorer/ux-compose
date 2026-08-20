"""Back-compat path — full list lesson lives in ``examples/lists.py``."""
from __future__ import annotations

from examples.lists import Shelf as ItemList  # noqa: F401

if __name__ == "__main__":
    from examples.lists import demo

    demo()
