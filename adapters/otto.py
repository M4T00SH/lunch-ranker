"""OTTO — Squarespace; one .menu-section per weekday with .menu-item-title
dishes. Sections used to live inside an 'Obedový špeciál' tabpanel (still
preferred when present); since 2026-08 they sit directly on the page."""
from bs4 import BeautifulSoup

from core.common import Dish, clean_name, day_index_in, find_weight, norm, strip_accents

NAME = "OTTO"
URL = "https://www.ottobratislava.sk/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    panel = None
    for el in soup.find_all(attrs={"aria-label": True}):
        if "obedov" in strip_accents(el["aria-label"]).lower() and el.get("role") == "tabpanel":
            panel = el
            break
    if panel is None:
        # 2026-08: Squarespace tabs removed — weekday .menu-sections now sit
        # directly on the page, one per day, so parse the whole document.
        panel = soup

    sections = panel.select(".menu-section")
    if not sections:
        raise ValueError("menu sections not found")

    dishes = []
    for section in sections:
        title = section.select_one(".menu-section-title")
        if not title or day_index_in(title.get_text()) != ctx.day_idx:
            continue
        for item in section.select(".menu-item-title"):
            raw = norm(item.get_text())
            if len(raw) < 4:
                continue
            low = strip_accents(raw).lower()
            category = "Polievka" if ("vyvar" in low or "polievka" in low or low.endswith("zeleninou")) else ""
            dishes.append(
                Dish(NAME, clean_name(raw), weight=find_weight(raw), category=category)
            )
    return dishes
