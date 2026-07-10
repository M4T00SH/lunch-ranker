"""Shared helpers for all restaurant adapters."""
from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("Europe/Bratislava")

UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)

# Accent-free Slovak day names, Monday first.
DAYS_SK = ["pondelok", "utorok", "streda", "stvrtok", "piatok", "sobota", "nedela"]
DAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class StaleMenuError(Exception):
    """The site is up but still shows an old week/day."""


@dataclass
class Dish:
    restaurant: str
    name: str
    weight: str = ""     # e.g. "350 g | 100 g", "0,33 l"
    category: str = ""   # e.g. "Polievka", "Hlavné jedlo"
    price: str = ""
    kcal: int | None = None  # only if the restaurant itself publishes it


@dataclass
class ImageMenu:
    """Menu only published as an image — needs the vision model."""
    restaurant: str
    image_bytes: bytes
    media_type: str = "image/jpeg"
    source_url: str = ""


class Ctx:
    """Per-run context: date, weekday and a shared HTTP session."""

    def __init__(self, day_idx: int | None = None):
        self.now = datetime.now(TZ)
        self.day_idx = self.now.weekday() if day_idx is None else day_idx
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": UA, "Accept-Language": "sk-SK,sk;q=0.9,en;q=0.8"}
        )

    @property
    def day_sk(self) -> str:
        return DAYS_SK[self.day_idx]

    @property
    def day_en(self) -> str:
        return DAYS_EN[self.day_idx]

    @property
    def date_iso(self) -> str:
        """Actual today — used for caching."""
        return self.now.strftime("%Y-%m-%d")

    @property
    def target_date(self):
        """Date the requested weekday falls on (today, or the next such
        weekday when debugging with --day from another day/weekend)."""
        return (self.now + timedelta(days=(self.day_idx - self.now.weekday()) % 7)).date()

    def fetch(self, url: str, **kw) -> requests.Response:
        r = self.session.get(url, timeout=25, **kw)
        r.raise_for_status()
        return r


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


SOUP_NAME_WORDS = ("polievka", "vyvar", "gazpacho", "kulajda", "cibulack", "minestrone", "bujon", "krem z")


def is_soup(d: "Dish") -> bool:
    """Mains-only ranking: trust the category first — 'hlavné' wins over a
    soup mention, because some menus label mains 'hlavné jedlá s polievkou'
    or end dish names with '+ polievka' (soup included in the price). Only
    unlabeled dishes are judged by the START of their name."""
    cat = strip_accents((d.category or "").lower())
    if "hlavn" in cat:
        return False
    if "polievk" in cat or "soup" in cat:
        return True
    head = " ".join(strip_accents(d.name.lower()).split()[:3])
    return any(w in head for w in SOUP_NAME_WORDS)


def clean_name(s: str) -> str:
    """Drop allergen codes like (1,3,7), [ * 1, 3 ], | A: 1,3 |, / A: 9 /."""
    s = norm(s)
    s = re.sub(r"[\(\[]\s*\*?\s*(?:A:?\s*)?\d{1,2}(?:\s*[,.]\s*\d{1,2})*\s*[\)\]]", " ", s)
    # "/A: 1,3,7 /" — explicit allergen marker, closing delimiter optional
    # (some menus forget it)
    s = re.sub(r"[|/]\s*A:?\s*\d{1,2}(?:\s*,\s*\d{1,2})*\s*[|/]?", " ", s)
    # "|1,3,7|", "I1,7,9I" (capital I as pipe) — bare digits need a closing
    # delimiter or end-of-text so weights like "200/200g" survive.
    s = re.sub(r"[|/I]\s*\d{1,2}(?:\s*,\s*\d{1,2})*\s*(?:[|/I]|$)", " ", s)
    s = re.sub(r"\[\s*\*[^\]]*\]", " ", s)
    return norm(s).strip(" -–|/*,")


# Matches "120 g", "0,33 l", "350 g | 100 g", "140/200g", "400 ml"
WEIGHT_RE = re.compile(
    r"(?:\d+(?:[.,]\d+)?\s*(?:g|l|ml)?\s*[|/+]\s*)*\d+(?:[.,]\d+)?\s*(?:g|l|ml)\b",
    re.I,
)


def find_weight(s: str) -> str:
    m = WEIGHT_RE.search(s or "")
    return norm(m.group(0)) if m else ""


def day_index_in(text: str) -> int | None:
    """Weekday index if the text contains a Slovak or English day name."""
    t = strip_accents(text or "").lower()
    for days in (DAYS_SK, DAYS_EN):
        for i, d in enumerate(days):
            if d in t:
                return i
    return None


def pdf_text(data: bytes) -> str:
    import pdfplumber  # deferred: slow import

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)
