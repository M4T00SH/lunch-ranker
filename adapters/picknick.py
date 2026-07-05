"""PICKNICK (Bencik Culinary, Twin City) — weekly HTML menu in .day-container divs."""
import re

from bs4 import BeautifulSoup

from core.common import Dish, clean_name, day_index_in, find_weight, norm

PRICE_RE = re.compile(r"(\d+[.,]\d{2})\s*€")

NAME = "PICKNICK"
URL = "https://bencikculinary.sk/picknik/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    dishes = []
    for day_div in soup.select(".day-container"):
        date_el = day_div.select_one(".day-date")
        if not date_el or day_index_in(date_el.get_text()) != ctx.day_idx:
            continue
        for opt in day_div.select(".day-menu-option"):
            label = opt.find("b")
            category = norm(label.get_text()).rstrip(":") if label else ""
            for meal in opt.select(".day-menu-option-meal"):
                raw = norm(meal.get_text())
                if len(raw) < 3:
                    continue
                pm = PRICE_RE.search(raw)
                price = f"{pm.group(1)} €" if pm else ""
                name = PRICE_RE.sub("", raw)
                dishes.append(
                    Dish(NAME, clean_name(name), weight=find_weight(name),
                         category=category, price=price)
                )
    return dishes
