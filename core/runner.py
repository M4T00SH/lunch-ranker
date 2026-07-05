"""Orchestrates one run: scrape all restaurants, estimate, render, cache."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .common import Ctx, Dish, ImageMenu, StaleMenuError, DAYS_SK
from . import estimate as est
from .render import render_page

log = logging.getLogger("runner")

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
LOGS = ROOT / "logs"

DAY_LABELS = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok", "Sobota", "Nedeľa"]


def load_cache() -> dict | None:
    f = DOCS / "data.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def run(day_idx: int | None = None, force: bool = False) -> dict:
    from config import RESTAURANTS  # local import: keeps adapters swappable

    ctx = Ctx(day_idx)

    cached = load_cache()
    if not force and cached and cached.get("date") == ctx.date_iso:
        log.info("Using cached results for %s", ctx.date_iso)
        return cached

    LOGS.mkdir(exist_ok=True)
    logging.getLogger().addHandler(
        logging.FileHandler(LOGS / f"run-{ctx.date_iso}.log", encoding="utf-8")
    )

    dishes: list[Dish] = []
    warnings: list[str] = []
    token = est.github_token()

    for mod in RESTAURANTS:
        name = mod.NAME
        try:
            result = mod.scrape(ctx)
            if isinstance(result, ImageMenu):
                if not token:
                    warnings.append(f"{name}: menu is an image and no AI token is available")
                    continue
                result = est.extract_dishes_from_image(
                    name, result.image_bytes, result.media_type, ctx.day_sk, token
                )
            if not result:
                warnings.append(f"{name}: no dishes found for {DAY_LABELS[ctx.day_idx]}")
                continue
            log.info("%s: %d dishes", name, len(result))
            for d in result:
                log.info("  RAW | %s | w=%s | cat=%s | price=%s", d.name, d.weight, d.category, d.price)
            dishes.extend(result)
        except StaleMenuError as e:
            warnings.append(f"{name}: {e}")
            log.warning("%s stale: %s", name, e)
        except Exception as e:
            warnings.append(f"couldn't read {name} today ({type(e).__name__})")
            log.exception("%s failed", name)

    if dishes:
        estimates, method = est.estimate_all(dishes)
    else:
        estimates, method = [], "n/a"

    ranked = sorted(
        (
            {
                "restaurant": d.restaurant,
                "name": d.name,
                "weight": d.weight,
                "category": d.category,
                "price": d.price,
                "protein_g": e["protein_g"],
                "kcal": d.kcal or e["kcal"],
                "reason": e["reason"],
            }
            for d, e in zip(dishes, estimates)
        ),
        key=lambda x: -x["protein_g"],
    )

    data = {
        "date": ctx.date_iso,
        "day_label": f"{DAY_LABELS[ctx.day_idx]} {ctx.target_date.strftime('%d.%m.%Y')}",
        "generated_at": ctx.now.strftime("%H:%M"),
        "method": method,
        "dishes": ranked,
        "warnings": warnings,
    }

    DOCS.mkdir(exist_ok=True)
    (DOCS / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (DOCS / "index.html").write_text(render_page(data), encoding="utf-8")
    log.info("Wrote docs/index.html with %d dishes, %d warnings", len(ranked), len(warnings))
    return data
