"""MESTIANSKY PIVOVAR (Dunajská) — Restaumatic site; section:denne-menu holds
the whole week, weekdays are categories (Pondelok..Piatok)."""
from core.common import strip_accents, DAYS_SK

from . import _restaumatic as rm

NAME = "MESTIANSKY PIVOVAR"
URL = "https://dunajska.mestianskypivovar.sk/section:denne-menu/"


def scrape(ctx):
    return parse(ctx.fetch(URL).text, ctx)


def parse(html, ctx):
    app = rm.app_data(html)
    want = DAYS_SK[ctx.day_idx]
    return rm.dishes_from_app(
        app, NAME, category_filter=lambda c: strip_accents(c).lower() == want
    )
