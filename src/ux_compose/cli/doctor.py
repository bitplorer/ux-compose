"""``uxcompose doctor`` — argv for the public ``ux_compose.doctor``."""
from __future__ import annotations


def main(argv: list[str]) -> int:
    from ux_compose.doctor import main as doctor_main

    return doctor_main(argv)
