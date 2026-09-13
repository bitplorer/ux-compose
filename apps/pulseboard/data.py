"""Product-quality fake desk — named keys, never a quantity MorphState."""

from __future__ import annotations

# Stats kit: (key, label, display-value)
KPI_ITEMS = (
    ("mrr", "MRR", "$184.2k"),
    ("net", "Net new", "$12.8k"),
    ("churn", "Logo churn", "0.8%"),
    ("expand", "Expansion", "$9.4k"),
    ("seats", "Active seats", "1,248"),
    ("nps", "NPS", "62"),
)

KPI_DELTAS = {
    "mrr": "+4.2%",
    "net": "+$2.1k",
    "churn": "−0.2pts",
    "expand": "+11%",
    "seats": "+36",
    "nps": "+3",
}

# Timeline kit: (lane, title, body)
TIMELINE_LANES = (
    ("all", "All"),
    ("revenue", "Revenue"),
    ("product", "Product"),
    ("care", "Care"),
)

TIMELINE_EVENTS = (
    ("revenue", "Harbor annual cleared legal", "Revenue"),
    ("product", "Pulse ingest shipped to staging", "Product"),
    ("care", "Northwind CSAT recovered to 4.8", "Care"),
    ("revenue", "Lumen expansion paper sent", "Revenue"),
    ("product", "Forecast v3 beat the holdout", "Product"),
    ("care", "Ada joined the dawn stand-up", "Care"),
)

FEED_SEED = (
    ("harbor", "Harbor · $48k cleared"),
    ("lumen", "Lumen · legal ping"),
    ("northwind", "Northwind · seat spike"),
)
FEED_MORE = (
    "Ren snoozed the Oslo thread",
    "Jules booked the Friday desk",
    "Noor minted the quarter Cap",
)

# Kanban columns are names. Card ids are stable presence keys.
KANBAN_META = {
    "harbor": ("Harbor Collective", "$48k · Annual", "West"),
    "lumen": ("Lumen Labs", "$22k · Seats", "North"),
    "northwind": ("Northwind", "$16k · Renew", "East"),
    "oslo": ("Oslo Atelier", "$9k · Pilot", "EU"),
    "kepler": ("Kepler Dry Goods", "$31k · Expand", "West"),
    "brine": ("Brine & Co", "$7k · Intro", "South"),
}

DEALS_QUALIFY = ("oslo", "brine")
DEALS_NEGOTIATE = ("lumen", "kepler")
DEALS_CLOSE = ("harbor", "northwind")

REGIONS = (
    ("all", "All desks"),
    ("west", "West"),
    ("north", "North"),
    ("east", "East"),
    ("eu", "EU"),
    ("south", "South"),
)

WATCHLIST = (
    ("harbor", "Harbor Collective"),
    ("kepler", "Kepler Dry Goods"),
    ("oslo", "Oslo Atelier"),
)

PEERS = (
    "Noor · here",
    "Jules · away",
    "Ada · focus",
    "Ren · here",
)

RATING_STARS = (
    ("one", "1"),
    ("two", "2"),
    ("three", "3"),
    ("four", "4"),
    ("five", "5"),
)
