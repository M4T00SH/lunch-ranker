"""DOCK7 — weekly PDF linked from the menu page (uploads/DOCK7_Denne_menu_*.pdf).
Bilingual layout: Slovak dish line carries weight+price, then a Slovak
description line, then the English title/description (no weight/price) — so
only lines containing a weight count as dishes. Weekly soup sits before the
PONDELOK section; a '22.06. - 26.06.' header line gives the covered week."""
import re
from datetime import date

from bs4 import BeautifulSoup

from core.common import (
    Dish, StaleMenuError, WEIGHT_RE, clean_name, day_index_in, find_weight,
    norm, pdf_text,
)

NAME = "DOCK7"
URL = "https://www.dock7.sk/en/menu/"

PRICE_RE = re.compile(r"\d+[.,]\d{2}\s*€")
RANGE_RE = re.compile(r"(\d{2})\.(\d{2})\.\s*-\s*(\d{2})\.(\d{2})\.")


def scrape(ctx):
    page = BeautifulSoup(ctx.fetch(URL).text, "html.parser")
    link = None
    for a in page.find_all("a", href=True):
        href = a["href"].lower()
        if "denne_menu" in href and href.endswith(".pdf"):
            link = a["href"]
            break
    if not link:
        raise ValueError("denne_menu PDF link not found")
    r = ctx.fetch(link, headers={"Referer": URL})
    return parse_pdf(pdf_text(r.content), ctx)


def parse_pdf(text, ctx):
    lines = [norm(l) for l in text.splitlines() if norm(l)]

    m = next((RANGE_RE.search(l) for l in lines[:12] if RANGE_RE.search(l)), None)
    if m:
        d1, m1, d2, m2 = (int(x) for x in m.groups())
        year = ctx.target_date.year
        if not (date(year, m1, d1) <= ctx.target_date <= date(year, m2, d2)):
            raise StaleMenuError(f"menu PDF covers {d1:02}.{m1:02}.–{d2:02}.{m2:02}.")

    dishes = []
    current_day = None  # None = weekly soup section before PONDELOK
    dish = None

    def flush():
        nonlocal dish
        if dish and (current_day is None or current_day == ctx.day_idx):
            dishes.append(dish)
        dish = None

    for line in lines:
        day = day_index_in(line)
        if day is not None and len(line) <= 26:
            flush()
            current_day = day
            continue
        if WEIGHT_RE.search(line) and not line.lower().startswith(("samostatne", "s denným")):
            flush()
            price = PRICE_RE.search(line)
            name = PRICE_RE.sub("", line)
            dish = Dish(
                NAME,
                clean_name(name),
                weight=find_weight(line),
                category="Polievka týždňa" if current_day is None else "",
                price=norm(price.group(0)) if price else "",
            )
        elif dish and not PRICE_RE.search(line):
            # first following line = Slovak description; English lines come
            # after and are dropped when the next weight line flushes
            if not dish.name.endswith(")"):
                dish.name = f"{dish.name} ({line[:100]})"
    flush()
    return dishes
