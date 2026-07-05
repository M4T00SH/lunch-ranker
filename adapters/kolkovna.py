"""KOLKOVNA — daily menu in .op-menu-day[data-date] blocks; dish text sits
between <strong>category</strong> and <span class=price>."""
from bs4 import BeautifulSoup, NavigableString, Tag

from core.common import Dish, StaleMenuError, clean_name, find_weight, norm

NAME = "KOLKOVNA"
URL = "https://www.kolkovna.sk/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    day_div = soup.select_one(f'.op-menu-day[data-date="{ctx.target_date.isoformat()}"]')
    if not day_div:
        if soup.select_one(".op-menu-day"):
            raise StaleMenuError("today's date is not in the published week")
        raise ValueError("menu block not found")

    dishes, seen = [], set()
    for food_list in day_div.select(".food-list"):
        category, buf = "", []

        def flush():
            text = norm(" ".join(buf))
            if len(text) > 3 and text not in seen:
                seen.add(text)
                dishes.append(
                    Dish(NAME, clean_name(text), weight=find_weight(text), category=category)
                )
            buf.clear()

        for node in food_list.descendants:
            if isinstance(node, Tag) and node.name == "strong":
                flush()
                category = norm(node.get_text())
            elif isinstance(node, Tag) and "price" in (node.get("class") or []):
                flush()
            elif isinstance(node, NavigableString):
                if node.parent.name not in ("strong", "span", "script", "h3", "a"):
                    buf.append(str(node))
        flush()
    return dishes
