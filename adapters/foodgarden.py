"""FOOD GARDEN (Apollo) — weekly HTML menu, one grid block per day with .recipe_item dishes."""
from bs4 import BeautifulSoup

from core.common import Dish, clean_name, day_index_in, find_weight, norm

NAME = "FOOD GARDEN"
URL = "https://apollo.foodgarden.sk/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    week = soup.select_one(".week_menu_food") or soup
    dishes = []
    for block in week.select(".grid-item"):
        h2 = block.find("h2")
        if not h2 or day_index_in(h2.get_text()) != ctx.day_idx:
            continue
        for section in block.select(".druh_menu"):
            cat_el = section.select_one(".sec_title span")
            category = norm(cat_el.get_text()) if cat_el else ""
            for item in section.select(".recipe_item"):
                h3 = item.find("h3")
                if not h3:
                    continue
                spans = " ".join(s.get_text() for s in item.select(".ri_text span"))
                price_el = item.select_one(".price")
                dishes.append(
                    Dish(
                        NAME,
                        clean_name(h3.get_text()),
                        weight=find_weight(spans),
                        category=category,
                        price=norm(price_el.get_text()) if price_el else "",
                    )
                )
    return dishes
