"""Product SSoT — named pieces, never a quantity MorphState."""

from __future__ import annotations

PIECES = (
    ("linen", "Cloth", "Linen work shirt", "Cut to the shoulder. One wash, then air.", "48", "cut"),
    ("oak", "Wood", "Oak serving board", "Wax, then rest. The grain keeps the day.", "72", "make"),
    ("wool", "Cloth", "Wool throw", "Winter weight. Fold once, never hang.", "96", "keep"),
    ("clay", "Earth", "Clay pourer", "Brush, never soak. The lip is the work.", "38", "cut"),
)

NAMES = tuple(row[2] for row in PIECES)

SLIDES = tuple((key, kind, title, body) for key, kind, title, body, _price, _stage in PIECES)

PAGES = (
    ("p1", ("Linen work shirt", "Oak serving board")),
    ("p2", ("Wool throw", "Clay pourer")),
    ("p3", ("Oak stool", "Wool cap")),
    ("p4", ("Clay lamp", "Stone bowl")),
)

TABLE_ROWS = tuple(
    (key, {"name": title, "stage": stage, "price": price})
    for key, _kind, title, _body, price, stage in PIECES
)

MATERIALS = (
    ("linen", "Linen"),
    ("oak", "Oak"),
    ("wool", "Wool"),
    ("clay", "Clay"),
)
