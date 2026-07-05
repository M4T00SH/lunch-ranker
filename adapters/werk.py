"""WERK — .smartlunch-days rows: the weekly soup row carries a
smartlunch-<weekday> class, then per-day header rows ('Pondelok 06.07.2026')
are followed by dish rows (<b>dish</b> + span sides, gramáž)."""
from bs4 import BeautifulSoup

from core.common import DAYS_EN, Dish, clean_name, day_index_in, norm

NAME = "WERK"
URL = "https://www.werkbratislava.sk/werk-daily/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".smartlunch-days")
    if not rows:
        raise ValueError("smartlunch rows not found")

    dishes, seen = [], set()
    current_day = None  # set by "Pondelok 06.07.2026" header rows
    for row in rows:
        classes = row.get("class") or []
        row_day = None
        for i, en in enumerate(DAYS_EN):
            if f"smartlunch-{en}" in classes:
                row_day = i
        titles = row.select(".smartlunch-title")
        if not titles:
            day = day_index_in(row.get_text())
            if day is not None:
                current_day = day
            continue
        day = row_day if row_day is not None else current_day
        if day is not None and day != ctx.day_idx:
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
