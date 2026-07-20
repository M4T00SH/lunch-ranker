"""LUCA — Restaumatic-style site (__NEXT_DATA__ JSON, same layout as
UMAMI/Mestiansky). section:obedove-menu shows ONLY the current day: one
category 'Obedové menu - <Deň>' with items '<Deň>: Obedové menu A..D'.
The real food is in the description; the day's shared soup (included in
the price) is appended to every description after ' + ' and is stripped
when all items share the same tail (ranking is mains-only). No date is
published (menuInfo is None), so staleness is detected by the day name
in the category — e.g. the page still said 'Utorok' on a Sunday."""
import re

from core.common import Dish, StaleMenuError, clean_name, day_index_in, norm

from . import _restaumatic as rm

NAME = "LUCA"
URL = "https://luca-restaurant.sk/section:obedove-menu"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    app = rm.app_data(html)
    lunch = {
        c["_id"]: norm(c.get("name", ""))
        for c in app.get("categories", [])
        if "obed" in c.get("name", "").lower()
    }
    if not lunch:
        raise StaleMenuError("no 'Obedové menu' category on the page")
    if {day_index_in(n) for n in lunch.values()} != {ctx.day_idx}:
        shown = ", ".join(lunch.values())
        raise StaleMenuError(f"site shows '{shown}', expected {ctx.day_sk}")

    items = [i for i in app.get("menu", []) if i.get("category") in lunch]
    descs = [norm(i.get("description", "")) for i in items]
    tails = {d.rsplit(" + ", 1)[-1] for d in descs}
    shared_soup = len(items) > 1 and len(tails) == 1 and " + " in descs[0]

    out = []
    for item, desc in zip(items, descs):
        label = clean_name(re.sub(r"^\S+:\s*", "", norm(item.get("name", ""))))
        if shared_soup:
            desc = desc.rsplit(" + ", 1)[0]
        desc = clean_name(desc)
        price = item.get("price") or 0
        out.append(
            Dish(
                NAME,
                f"{label} ({desc})" if desc else label,
                category=lunch[item["category"]],
                price=f"{price / 100:.2f} €" if price else "",
            )
        )
    return out
