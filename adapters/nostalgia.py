"""NOSTALGIA (Nivy) — menuv2 sections with id menu-denne-menu-<day>-<dd-mm-yyyy>."""
from bs4 import BeautifulSoup

from core.common import Dish, StaleMenuError, clean_name, find_weight, norm

NAME = "NOSTALGIA"
URL = "https://www.nostalgianivy.sk/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    date_slug = ctx.target_date.strftime("%d-%m-%Y")
    section = None
    for sec in soup.select("section.menuv2-section, .menuv2-section"):
        sec_id = sec.get("id", "")
        if sec_id.startswith("menu-denne-menu-") and sec_id.endswith(date_slug):
            section = sec
            break
    if section is None:
        if soup.select_one('[id^="menu-denne-menu-"]'):
            raise StaleMenuError("no section for today's date")
        raise ValueError("daily menu sections not found")

    dishes, seen = [], set()

    def add(raw, category):
        name = clean_name(raw)
        if len(name) < 4 or name.lower() in seen:
            return
        seen.add(name.lower())
        dishes.append(Dish(NAME, name, weight=find_weight(raw), category=category))

    desc = section.select_one(".m-list__description")
    if desc:
        raw = norm(desc.get_text())
        if len(raw) > 8:
            add(raw.split(":", 1)[-1], "Polievka")
    for h4 in section.select("h4.m-item__title"):
        add(norm(h4.get_text()), "Hlavné jedlo")
    return dishes
