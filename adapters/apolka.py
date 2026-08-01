"""APOLKA — 'OBEDY V APOLKE' page links a weekly PDF with sections
'UTOROK 07.07.' → POLIEVKA / HLAVNÉ JEDLO, one dish each. The PDF filename
changed 2026-08 from uploads/dennemenu_*.pdf to uploads/kcfinder/files/
Menu <dates>.pdf, so the link is found by its 'OBEDY V APOLKE' anchor text
first, old filename pattern second. Beware: the page also links
karta_obedov_menu.pdf (standing menu card) — anchor text avoids it."""
import re

from bs4 import BeautifulSoup

from core.common import (
    Dish, StaleMenuError, clean_name, day_index_in, find_weight, norm,
    pdf_text, strip_accents,
)

NAME = "APOLKA"
URL = "https://www.apolka.sk/menu2.php?id=12&lang=sk"

SUBHEADS = ("polievka", "hlavne jedlo", "hlavne jedla", "dezert", "special")


def scrape(ctx):
    page = BeautifulSoup(ctx.fetch(URL).text, "html.parser")
    link = None
    for a in page.find_all("a", href=True):
        href = a["href"].lower()
        label = strip_accents(a.get_text(" ")).lower()
        if ".pdf" in href and (
            "obedy" in label or ("dennemenu" in href and href.endswith(".pdf"))
        ):
            link = a["href"]
            break
    if not link:
        raise ValueError("lunch menu PDF link not found")
    if link.startswith("uploads"):
        link = "https://www.apolka.sk/" + link
    return parse_pdf(pdf_text(ctx.fetch(link).content), ctx)


def parse_pdf(text, ctx):
    lines = [norm(l) for l in text.splitlines() if norm(l)]
    dishes = []
    current_day, category, buf = None, "", []
    saw_any_day = False

    def flush():
        nonlocal buf
        joined = clean_name(" ".join(buf))
        if joined and current_day == ctx.day_idx and category:
            dishes.append(Dish(NAME, joined, weight=find_weight(" ".join(buf)), category=category))
        buf = []

    for line in lines:
        bare = strip_accents(line).lower()
        if re.match(r"^\d+\.\s", line):  # allergen legend at the bottom
            break
        day = day_index_in(line)
        if day is not None and len(line) <= 20:
            flush()
            current_day, category = day, ""
            saw_any_day = True
            continue
        if any(bare.startswith(s) for s in SUBHEADS) and len(line) <= 24:
            flush()
            category = line.title()
            continue
        if current_day is not None and category:
            buf.append(line)
    flush()

    if saw_any_day and not dishes:
        raise StaleMenuError("today's day is not in the menu PDF")
    return dishes
