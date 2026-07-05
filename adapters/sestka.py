"""ŠESTKA — shows only the current day: h3 'STREDA 1. 7. 2026' + .promotion-item rows."""
from bs4 import BeautifulSoup

from core.common import Dish, StaleMenuError, clean_name, day_index_in, norm

NAME = "SESTKA"
URL = "https://www.sestka.xyz/"

NOTICE_WORDS = ("zákazníc", "dovolenk", "prevádzk", "zatvoren", "otvoren")


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    section = None
    for h2 in soup.find_all("h2"):
        if "DENNÉ MENU" in h2.get_text().upper():
            section = h2.find_parent("section") or h2.parent
            break
    if section is None:
        raise ValueError("DENNÉ MENU section not found")

    h3 = section.find("h3")
    shown_day = day_index_in(h3.get_text()) if h3 else None
    if shown_day is not None and shown_day != ctx.day_idx:
        raise StaleMenuError(f"still shows {norm(h3.get_text())}")

    dishes = []
    for item in section.select(".promotion-item"):
        parts = [norm(p.get_text()) for p in item.select(".promotion-title p")]
        name = " ".join(dict.fromkeys(p for p in parts if p and p != "|"))
        low = name.lower()
        if len(name) < 6 or any(w in low for w in NOTICE_WORDS):
            continue
        weight_el = item.select_one(".promotion-price")
        price_el = item.select_one(".promotion-discount")
        dishes.append(
            Dish(
                NAME,
                clean_name(name),
                weight=norm(weight_el.get_text()) if weight_el else "",
                price=norm(price_el.get_text()) if price_el else "",
            )
        )
    return dishes
