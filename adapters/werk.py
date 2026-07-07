"""WERK — day header rows ('Pondelok 06.07.2026', class .smartlunch-days)
are followed by dish rows (class .smartlunch-wrap, <b>dish</b> + span sides,
gramáž). The weekly soup row (both classes) precedes all headers and applies
to every day. Since 2026-07 every dish row carries smartlunch-monday
regardless of its real day — day must come from header order, NOT from the
smartlunch-<weekday> class."""
from bs4 import BeautifulSoup

from core.common import Dish, clean_name, day_index_in, norm

NAME = "WERK"
URL = "https://www.werkbratislava.sk/werk-daily/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".smartlunch-days, .smartlunch-wrap")
    if not rows:
        raise ValueError("smartlunch rows not found")

    dishes, seen = [], set()
    current_day = None  # set by "Pondelok 06.07.2026" header rows
    for row in rows:
        titles = row.select(".smartlunch-title")
        if not titles:
            day = day_index_in(row.get_text())
            if day is not None:
                current_day = day
            continue
        if current_day is not None and current_day != ctx.day_idx:
            continue
        label_el = row.select_one('[class*="smartlunch-soup"], [class*="smartlunch-label"]')
        category = norm(label_el.get_text()) if label_el else ""
        grams = row.select(".smartlunch-gramaz")
        for i, t in enumerate(titles):
            b = t.find("b")
            name = norm(b.get_text()) if b else norm(t.get_text())
            side = t.find("span")
            if side and norm(side.get_text()):
                name = f"{name}, {norm(side.get_text())}"
            name = clean_name(name)
            if len(name) < 4 or name.lower() in seen:
                continue
            seen.add(name.lower())
            weight = norm(grams[i].get_text()) if i < len(grams) else ""
            dishes.append(Dish(NAME, name, weight=weight, category=category))
    return dishes
