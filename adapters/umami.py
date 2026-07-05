"""UMAMI — Restaumatic site; each weekday has its own section URL
(umami.sk/section:pondelok). Validates 'Ponuka pre DD.MM.YYYY'."""
from core.common import StaleMenuError

from . import _restaumatic as rm

NAME = "UMAMI"
URL = "https://umami.sk/"


def scrape(ctx):
    html = ctx.fetch(f"{URL}section:{ctx.day_sk}/").text
    return parse(html, ctx)


def parse(html, ctx):
    app = rm.app_data(html)
    info = app.get("menuInfo") or ""
    expected = ctx.target_date.strftime("%d.%m.%Y")
    if info and expected not in info:
        raise StaleMenuError(f"site says '{info}', expected {expected}")
    # Keep the lunch categories, drop drinks if any appear
    return rm.dishes_from_app(
        app, NAME, category_filter=lambda c: "napoj" not in c.lower()
    )
