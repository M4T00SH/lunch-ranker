"""MINT (Pradiareň) — the 'Denné menu' tile links to a weekly PDF.
PDF lines: '| dish name [ * allergens ] 350 g | 100 g 11.90 €' + description lines."""
import re

from bs4 import BeautifulSoup

from core.common import (
    Dish, StaleMenuError, clean_name, day_index_in, norm, pdf_text, strip_accents,
)

NAME = "MINT"
URL = "https://www.mintconcept.sk/minty/mint-pradiaren/menu/"

PRICE_RE = re.compile(r"\d+[.,]\d{2}\s*€")
WEIGHT_IN_LINE = re.compile(r"(\d+(?:[.,]\d+)?\s*(?:g|l|ml)(?:\s*\|\s*\d+(?:[.,]\d+)?\s*(?:g|l|ml))*)", re.I)


def scrape(ctx):
    page = BeautifulSoup(ctx.fetch(URL).text, "html.parser")
    link = None
    for a in page.find_all("a", href=True):
        title = (a.get("title") or "") + a.get_text()
        if "denn" in strip_accents(title).lower() and a["href"].lower().endswith(".pdf"):
            link = a["href"]
            break
    if not link:
        raise ValueError("Denné menu PDF link not found")
    pdf = ctx.fetch(link, headers={"Referer": URL, "Accept": "application/pdf,*/*"}).content
    return parse_pdf(pdf_text(pdf), ctx)


def parse_pdf(text, ctx):
    lines = [norm(l) for l in text.splitlines() if norm(l)]

    # Header like '29.06. – 03.07.2026' — check today's week
    m = re.search(r"(\d{2})\.(\d{2})\.\s*[–-]\s*(\d{2})\.(\d{2})\.(\d{4})", " ".join(lines[:3]))
    if m:
        d1, mo1, d2, mo2, yr = m.groups()
        start = f"{yr}-{mo1}-{d1}"
        end = f"{yr}-{mo2}-{d2}"
        today = ctx.target_date.isoformat()
        if not (start <= today <= end):
            raise StaleMenuError(f"menu PDF covers {d1}.{mo1}.–{d2}.{mo2}.{yr}")

    dishes = []
    current_day = None   # None until first heading; 'week' for weekly soup
    dish, desc = None, []

    def flush():
        nonlocal dish, desc
        if dish and current_day in ("week", ctx.day_idx):
            name = dish["name"]
            if desc:
                name = f"{name} ({', '.join(desc)[:110]})"
            dishes.append(
                Dish(NAME, clean_name(name), weight=dish["weight"],
                     category="Polievka týždňa" if current_day == "week" else "",
                     price=dish["price"])
            )
        dish, desc = None, []

    for line in lines:
        bare = strip_accents(line).lower()
        if "polievka tyzdna" in bare:
            flush()
            current_day = "week"
            continue
        day = day_index_in(line)
        if day is not None and len(line) <= 12:  # bare day heading
            flush()
            current_day = day
            continue
        if line.startswith("|"):
            flush()
            body = line.lstrip("| ").strip()
            wm = WEIGHT_IN_LINE.search(body)
            pm = PRICE_RE.search(body)
            cut = min(x for x in (wm.start() if wm else len(body),
                                  pm.start() if pm else len(body),
                                  body.find("[") if "[" in body else len(body)))
            dish = {
                "name": body[:cut],
                "weight": norm(wm.group(1)) if wm else "",
                "price": norm(pm.group(0)) if pm else "",
            }
        elif dish and not PRICE_RE.fullmatch(line) and "€" not in line:
            desc.append(line)
    flush()
    return dishes
