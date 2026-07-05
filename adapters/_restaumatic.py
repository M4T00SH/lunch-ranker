"""Shared parser for Restaumatic-powered sites (UMAMI, Mestiansky pivovar):
dish data sits in the __NEXT_DATA__ JSON under props.app.{menu,categories}."""
import json
import re

from core.common import Dish, clean_name, norm

NEXT_DATA_RE = re.compile(
    r'__NEXT_DATA__"\s+type="application/json">(.*?)</script>', re.S
)


def app_data(html: str) -> dict:
    m = NEXT_DATA_RE.search(html)
    if not m:
        raise ValueError("__NEXT_DATA__ not found")
    return json.loads(m.group(1))["props"]["app"]


def dishes_from_app(app: dict, restaurant: str, category_filter=None) -> list[Dish]:
    """category_filter(name) -> bool decides which categories to keep."""
    cats = {c["_id"]: norm(c.get("name", "")) for c in app.get("categories", [])}
    out, seen = [], set()
    for item in app.get("menu", []):
        cat_name = cats.get(item.get("category"), "")
        if category_filter and not category_filter(cat_name):
            continue
        name = norm(item.get("name", ""))
        key = clean_name(name).lower()  # dedupe on the bare dish name: the same
        if len(key) < 4 or key in seen:  # dish repeats across categories with
            continue                     # slightly different descriptions
        seen.add(key)
        desc = norm(item.get("description", ""))
        if desc and not desc.lower().startswith("pôvod"):
            name = f"{name} ({desc})"
        weight = norm(str(item.get("weight") or ""))
        unit = norm(str(item.get("weightType") or ""))
        if weight and unit:
            weight = f"{weight} {unit}"
        price = item.get("price") or 0
        kcal = item.get("kcal")
        out.append(
            Dish(
                restaurant,
                clean_name(name),
                weight=weight,
                category=cat_name,
                price=f"{price / 100:.2f} €" if price else "",
                kcal=int(kcal) if kcal else None,
            )
        )
    return out
