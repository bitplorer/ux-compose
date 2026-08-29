"""House books — the Host. Kit cards read and write here.

This is the stand-in for a database. Catalogs and magnitudes live on the
House. Kit MorphState stays a name. Isolation: no ux_channel import.
"""

from __future__ import annotations

from typing import Any


_WASH = {
    "flax": "bg-gradient-to-br from-[#e8dcc8] via-[#c9b89a] to-[#8a7354]",
    "walnut": "bg-gradient-to-br from-[#c4a574] via-[#8b6914] to-[#3d2914]",
    "merino": "bg-gradient-to-br from-[#d4c4b0] via-[#9a8470] to-[#5c4033]",
    "river": "bg-gradient-to-br from-[#c9a882] via-[#a67c52] to-[#6b4423]",
    "brass": "bg-gradient-to-br from-[#e6d28a] via-[#c4a035] to-[#6b5420]",
}

_INK = {
    "flax": "text-[#3d2914]",
    "walnut": "text-[#faf6f0]",
    "merino": "text-[#faf6f0]",
    "river": "text-[#faf6f0]",
    "brass": "text-[#3d2914]",
}

_SWATCH = {
    "flax": "bg-gradient-to-br from-[#e8dcc8] to-[#c9b89a]",
    "walnut": "bg-gradient-to-br from-[#c4a574] to-[#8b6914]",
    "merino": "bg-gradient-to-br from-[#d4c4b0] to-[#9a8470]",
    "river": "bg-gradient-to-br from-[#c9a882] to-[#a67c52]",
    "brass": "bg-gradient-to-br from-[#e6d28a] to-[#c4a035]",
}


def _seed_pieces() -> tuple[tuple[str, ...], ...]:
    # sku, kind, title, body, price, stage
    return (
        ("flax", "Cloth", "Flax apron", "Tied at the hip. One wash, then air.", "42", "cut"),
        ("walnut", "Wood", "Walnut mallet", "Oiled twice. The head is the work.", "86", "make"),
        ("merino", "Cloth", "Merino wrap", "Undyed. Fold once, never hang.", "120", "keep"),
        ("river", "Earth", "River bowl", "Thrown wet. Never trimmed.", "54", "cut"),
        ("brass", "Metal", "Brass pin", "Soft jaw. Hold, do not pinch.", "28", "keep"),
    )


class House:
    """In-memory Host. Tests call ``reset()``. The live app holds one."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.pieces = _seed_pieces()
        self.saved: list[str] = ["flax", "merino"]
        self.lanes: dict[str, list[str]] = {
            "cut": ["flax-01", "river-04"],
            "make": ["walnut-02"],
            "keep": ["merino-03"],
        }
        self.bag = 4
        self.held = 36
        self.placed = 1
        self.pour = 50
        self.rating = "three"
        self.presence = "here"
        self.peers = (("Noor", "here"), ("Atelier", "away"), ("House", "focus"))
        self.tags = ["flax", "quiet"]
        self.shelf = "The books are on the shelf. Five objects from the floor."
        self.otp = "246810"
        self.users = {
            "you@floor.test": {"password": "housewood1", "name": "Noor"},
        }
        self.ledger: list[dict[str, Any]] = []
        self.day = ""
        self.plan = ""
        self.note("boot", detail="House books opened")

    def note(self, kind: str, **extra: Any) -> None:
        row = {"kind": kind, **extra}
        self.ledger.append(row)
        if len(self.ledger) > 40:
            self.ledger = self.ledger[-40:]

    def wash(self, key: str) -> str:
        return _WASH.get(key, "bg-stone-800")

    def ink(self, key: str) -> str:
        return _INK.get(key, "text-stone-50")

    def swatch(self, key: str) -> str:
        return _SWATCH.get(key, "bg-stone-200")

    def slides(self) -> tuple[tuple[str, str, str, str], ...]:
        return tuple((k, kind, title, body) for k, kind, title, body, _p, _s in self.pieces[:4])

    def catalog_items(self) -> tuple[tuple[str, str, str, str], ...]:
        return tuple((k, kind, title, price) for k, kind, title, _b, price, _s in self.pieces)

    def names(self) -> tuple[str, ...]:
        return tuple(row[2] for row in self.pieces)

    def materials(self) -> tuple[tuple[str, str], ...]:
        return (
            ("flax", "Flax"),
            ("walnut", "Walnut"),
            ("merino", "Merino"),
            ("river", "River"),
            ("quiet", "Quiet"),
            ("winter", "Winter"),
        )

    def table_rows(self) -> tuple[tuple[str, dict[str, str]], ...]:
        return tuple(
            (f"{k}-0{i}", {"name": title, "stage": stage, "price": price})
            for i, (k, _kind, title, _b, price, stage) in enumerate(self.pieces, start=1)
        )

    def table_columns(self) -> tuple[tuple[str, str], ...]:
        return (("name", "Piece"), ("stage", "Stage"), ("price", "Price"))

    def pages(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        names = self.names()
        pairs = []
        for i in range(0, 12):
            a = names[i % len(names)]
            b = names[(i + 1) % len(names)]
            pairs.append((f"p{i + 1}", (a, b)))
        return tuple(pairs)

    def kanban_cards(self) -> tuple[tuple[str, str, str], ...]:
        return tuple(
            (f"{k}-0{i}", title, body)
            for i, (k, _kind, title, body, _p, _s) in enumerate(self.pieces[:4], start=1)
        )

    def kanban_lanes(self) -> tuple[tuple[str, str, str], ...]:
        return (
            ("cut", "Cut", "Marked"),
            ("make", "Make", "On the bench"),
            ("keep", "Keep", "Held"),
        )

    def lane(self, name: str) -> tuple[str, ...]:
        return tuple(self.lanes.get(name, ()))

    def move_piece(self, sku: str, to: str) -> None:
        for key, rows in self.lanes.items():
            self.lanes[key] = [x for x in rows if x != sku]
        self.lanes.setdefault(to, []).append(sku)
        self.note("move", sku=sku, to=to)

    def archive_piece(self, sku: str) -> None:
        for key, rows in self.lanes.items():
            self.lanes[key] = [x for x in rows if x != sku]
        self.note("archive", sku=sku)

    def events(self) -> tuple[tuple[str, str, str, str], ...]:
        return (
            ("cut", "Apron marked", "The tie is the work.", "Morning"),
            ("make", "Mallet oiled", "Twice, then rest.", "Midday"),
            ("keep", "Wrap folded", "Once, never hung.", "Dusk"),
            ("cut", "Bowl thrown", "Wet. Never trimmed.", "Night"),
        )

    def tabs(self) -> tuple[tuple[str, str, str, str], ...]:
        return (
            ("floor", "Floor", "The books", "Five objects. The Host holds the list."),
            ("bench", "Bench", "What is open", "Pour, rate, move. Magnitudes stay silent."),
            ("door", "Door", "Who may enter", "Login and OTP spend Caps. Chrome does not."),
        )

    def sections(self) -> tuple[tuple[str, str, str], ...]:
        return (
            ("fit", "Fit", "The apron ties at the hip. One Component owns the open set."),
            ("finish", "Finish", "Oil the mallet twice. Morph this unit; never put html= on enter."),
            ("care", "Care", "The bowl is thrown wet. Reading a section is public."),
        )

    def trail(self) -> tuple[tuple[str, str], ...]:
        return (("desk", "Desk"), ("shelf", "Shelf"), ("walnut", "Walnut mallet"))

    def sidebar(self) -> tuple[tuple[str, str, str, str], ...]:
        return (
            ("desk", "Desk", "The floor", "KPI, presence, the ledger."),
            ("shelf", "Shelf", "The books", "Slides, hearts, the table."),
            ("bench", "Bench", "The work", "Stars, lanes, the pour."),
        )

    def options(self) -> tuple[tuple[str, str], ...]:
        return tuple((k, title) for k, _kind, title, _b, _p, _s in self.pieces)

    def groups(self) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
        cloth = tuple((k, t) for k, kind, t, *_ in self.pieces if kind == "Cloth")
        other = tuple((k, t) for k, kind, t, *_ in self.pieces if kind != "Cloth")
        return (("Cloth", cloth), ("Held", other))

    def commands(self) -> tuple[tuple[str, str, str], ...]:
        return (
            ("go-desk", "Open the desk", "Session"),
            ("go-shelf", "Walk the shelf", "Nav"),
            ("push-notice", "Push a notice", "Ops"),
            ("sign-out", "Sign out", "Session"),
        )

    def menu(self) -> tuple[tuple[str, str], ...]:
        return (("rename", "Rename"), ("inspect", "Inspect"), ("pin", "Pin to the desk"))

    def actions(self) -> tuple[tuple[str, str, bool], ...]:
        return (
            ("share", "Share this piece", False),
            ("pin", "Pin to the desk", False),
            ("archive", "Archive (Cap)", True),
        )

    def plans(self) -> tuple:
        return (
            (
                "guest",
                "Guest",
                "0",
                "Walk the floor.",
                ("Look", "Do not take", "No Cap"),
            ),
            (
                "maker",
                "Maker",
                "48",
                "Use the bench.",
                ("Pour", "Rate", "Move"),
            ),
            (
                "keeper",
                "Keeper",
                "96",
                "Hold the books.",
                ("Ledger", "Reset Cap", "The house"),
            ),
        )

    def steps(self) -> tuple[tuple[str, str, str], ...]:
        return (
            ("mark", "Mark", "Name the piece."),
            ("oil", "Oil", "Twice, then rest."),
            ("keep", "Keep", "Fold once."),
        )

    def seed(self) -> tuple[str, ...]:
        return (
            "Reserved the merino wrap.",
            "Oiled the walnut mallet.",
            "Marked the flax apron.",
        )

    def more(self) -> tuple[str, ...]:
        return (
            "Folded the merino.",
            "Filed the brass pin.",
            "Threw the river bowl.",
            "Tied the flax apron.",
        )

    def toggle_saved(self, sku: str, on: bool) -> None:
        if on and sku not in self.saved:
            self.saved.append(sku)
        if not on:
            self.saved = [x for x in self.saved if x != sku]
        self.note("wish", sku=sku, on=on)

    def set_rating(self, key: str) -> None:
        self.rating = key
        self.note("rate", value=key)

    def set_pour(self, n: int) -> None:
        self.pour = n
        self.note("pour", n=n)

    def sale(self) -> None:
        self.bag = max(0, self.bag - 1)
        self.placed += 1
        self.held += 12
        self.note("sale", placed=self.placed)

    def zero(self) -> None:
        self.bag = 0
        self.held = 0
        self.placed = 0
        self.note("zero")

    def kpi_tuple(self) -> tuple[int, int, int]:
        return (self.bag, self.held, self.placed)

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)
        self.note("tag-add", tag=tag)

    def remove_tag(self, tag: str) -> None:
        self.tags = [t for t in self.tags if t != tag]
        self.note("tag-remove", tag=tag)

    def set_self(self, key: str) -> None:
        self.presence = key
        self.note("presence", value=key)

    def authenticate(self, *, email: str, password: str, name: str, signup: bool):
        from ux_compose.kit.login import AuthDecision

        email = (email or "").strip().lower()
        row = self.users.get(email)
        if signup:
            if row:
                return AuthDecision(False, "That account is already on the books.")
            self.users[email] = {"password": password, "name": name or email}
            self.note("signup", email=email)
            return AuthDecision(True, "Account created")
        if not row or row["password"] != password:
            return AuthDecision(False, "The door does not know this pair.")
        self.note("login", email=email)
        return AuthDecision(True, f"Signed in as {row['name']}")

    def verify_otp(self, code: str) -> str | None:
        if code != self.otp:
            self.note("otp-fail", code=code)
            return "This code is not on the books."
        self.note("otp-ok")
        return None


HOUSE = House()
