"""ST. GERMAIN — lunch menu is the one HTML table containing day headers
(PONDELOK..PIATOK, sometimes spaced like 'P O N D E L O K'); dish rows have
weight + <strong>name</strong> + price. The page continues with the whole
cafe menu (drinks, pastries) in further tables — parse ONLY the lunch table,
otherwise everything after the PIATOK header is counted as Friday lunch."""
from bs4 import BeautifulSoup

from core.common import Dish, clean_name, day_index_in, find_weight, norm

NAME = "ST.GERMAIN"
URL = "https://stgermain.sk/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def _is_day_header(tr):
    compact = norm(tr.get_text(" ")).replace(" ", "")
    return day_index_in(compact) is not None and len(compact) <= 14


def parse(html, ctx):
    soup = BeautifulSoup(html, "html.parser")
    table = next(
        (t for t in soup.find_all("table") if any(map(_is_day_header, t.find_all("tr")))),
        None,
    )
    if table is None:
        raise ValueError("lunch table with day headers not found")
    dishes = []
    current_day = None  # None = weekly items before the first day header
    for tr in table.find_all("tr"):
        text = norm(tr.get_text(" "))
        if not text:
            continue
        compact = text.replace(" ", "")
        day = day_index_in(compact)
        strong = tr.find("strong")
        # Day header row: a day name and nothing else substantial
        if day is not None and len(compact) <= 14:
            current_day = day
            continue
        if not strong:
            continue
        name = norm(strong.get_text())
        if len(name) < 4 or "OBEDY" in name.upper():
            continue
        if current_day is None or current_day == ctx.day_idx:
            cells = tr.find_all("td")
            price = norm(cells[-1].get_text()) if len(cells) > 1 else ""
            category = "Polievka týždňa" if current_day is None else ""
            dishes.append(
                Dish(NAME, clean_name(name), weight=find_weight(text),
                     category=category, price=price)
            )
    return dishes
