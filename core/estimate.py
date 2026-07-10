"""Protein/kcal estimation.

Primary path: one batched call to GitHub Models (free tier, works in GitHub
Actions with the built-in GITHUB_TOKEN). Fallback: rough Slovak keyword table.
Also hosts the vision extractor for image-only menus (FAJNE JEDLO).
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import subprocess

import requests

from .common import Dish, strip_accents

log = logging.getLogger("estimate")

ENDPOINT = "https://models.github.ai/inference/chat/completions"
MODEL = "openai/gpt-4o"


def github_token() -> str | None:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return None


def _chat(messages: list, token: str, max_tokens: int = 10000) -> str:
    r = requests.post(
        ENDPOINT,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        },
        timeout=180,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


# ----------------------------------------------------------------------------
# Batched protein/kcal estimation
# ----------------------------------------------------------------------------

ESTIMATE_SYSTEM = (
    "You are a nutritionist who knows Slovak and Czech cuisine very well. "
    "You estimate protein and calories of restaurant lunch dishes from their "
    "Slovak menu names. Use listed portion weights when given (formats like "
    "'140 g/200 g' usually mean meat/side, '350 g' is the whole plate, "
    "'0,33 l' is soup volume). If no weight is given assume a typical "
    "Bratislava lunch portion. Reply with JSON only."
)


def estimate_with_ai(dishes: list[Dish], token: str) -> list[dict]:
    payload = [
        {
            "id": i,
            "restaurant": d.restaurant,
            "dish": d.name,
            "weight": d.weight,
            "category": d.category,
        }
        for i, d in enumerate(dishes)
    ]
    user = (
        "Estimate protein (grams) and calories (kcal) for each dish below. "
        'Return JSON: {"estimates": [{"id": <id>, "protein_g": <int>, '
        '"kcal": <int>, "reason": "<max 12 words, English>"}]} '
        "with exactly one entry per input id.\n\n" + json.dumps(payload, ensure_ascii=False)
    )
    content = _chat(
        [{"role": "system", "content": ESTIMATE_SYSTEM}, {"role": "user", "content": user}],
        token,
    )
    estimates = {e["id"]: e for e in _parse_json(content)["estimates"]}
    out = []
    for i, d in enumerate(dishes):
        e = estimates.get(i)
        if not e:
            e = _keyword_estimate(d)
            e["reason"] += " (AI skipped this dish)"
        out.append(
            {
                "protein_g": round(float(e["protein_g"])),
                "kcal": round(float(e["kcal"])),
                "reason": str(e.get("reason", ""))[:120],
            }
        )
    return out


# ----------------------------------------------------------------------------
# Keyword fallback (no AI): rough but always available
# ----------------------------------------------------------------------------

# keyword (accent-free, lowercase) -> (protein g / 100 g, kcal / 100 g)
FOOD_TABLE = [
    ("kuraci", 23, 165), ("kura", 23, 165), ("stripsy", 20, 250),
    ("morcaci", 24, 150), ("kacaci", 19, 240), ("kacic", 19, 240),
    ("hovadzi", 26, 220), ("teleci", 24, 170), ("bravcov", 22, 250),
    ("krkovick", 18, 290), ("panenk", 23, 160), ("rezen", 19, 280),
    ("gulas", 12, 130), ("burger", 14, 250), ("pastrami", 22, 150),
    ("sunka", 20, 130), ("slanin", 13, 450), ("klobas", 15, 320),
    ("parok", 12, 280), ("udenin", 15, 300), ("kotlet", 22, 240),
    ("losos", 20, 200), ("treska", 17, 90), ("pstruh", 20, 120),
    ("ryba", 18, 130), ("tuniak", 24, 130), ("kreved", 20, 100),
    ("tofu", 12, 120), ("halusky", 5, 170), ("bryndza", 15, 260),
    ("syr", 20, 300), ("mozzarell", 18, 250), ("hermelin", 20, 310),
    ("vajc", 13, 150), ("vajic", 13, 150), ("tvaroh", 12, 100),
    ("sosovic", 8, 110), ("cicer", 8, 130), ("fazul", 8, 110),
    ("hrach", 7, 100), ("quinoa", 5, 120),
    ("cestovin", 5, 150), ("penne", 5, 150), ("spagety", 5, 150),
    ("lasagne", 8, 160), ("rizoto", 4, 140), ("risotto", 4, 140),
    ("pizza", 9, 240), ("knedl", 6, 200), ("zemiak", 2, 90),
    ("ryza", 3, 130), ("salat", 2, 40), ("polievka", 3, 45),
    ("vyvar", 4, 35), ("kulajda", 3, 60), ("cibulack", 3, 50),
    ("minestrone", 3, 40), ("krem", 3, 70), ("palacink", 6, 220),
    ("livance", 7, 230), ("zemlovka", 6, 180), ("dukatove", 6, 250),
]

SOUP_HINTS = ("polievka", "vyvar", "kulajda", "cibulack", "minestrone", "soup", "krem z")


def _grams(weight: str) -> list[float]:
    vals = []
    for num, unit in re.findall(r"(\d+(?:[.,]\d+)?)\s*(g|ml|l)?", weight or ""):
        v = float(num.replace(",", "."))
        if unit == "l":
            v *= 1000
        vals.append(v)
    return vals


def _keyword_estimate(d: Dish) -> dict:
    text = strip_accents((d.name + " " + d.category).lower())
    hit = next(((k, p, c) for k, p, c in FOOD_TABLE if k in text), None)
    is_soup = any(h in text for h in SOUP_HINTS)
    grams = _grams(d.weight)

    if is_soup:
        portion = grams[0] if grams else 330.0
        p100, k100 = (hit[1], hit[2]) if hit else (3, 50)
        protein = p100 * portion / 100 * (0.5 if hit and not _is_soup_kw(hit[0]) else 1)
        kcal = k100 * portion / 100 * (0.5 if hit and not _is_soup_kw(hit[0]) else 1)
        reason = f"soup ~{portion:.0f} ml, keyword table"
    elif hit:
        # "140/200 g" style: first value is usually the protein component
        main_w = grams[0] if grams else 150.0
        main_w = min(main_w, 400.0)
        protein = hit[1] * main_w / 100 + 6  # + sides
        kcal = hit[2] * main_w / 100 + 300
        reason = f"'{hit[0]}' ~{main_w:.0f} g + sides, keyword table"
    else:
        protein, kcal, reason = 15, 550, "unknown dish, generic lunch guess"
    return {"protein_g": round(protein), "kcal": round(kcal), "reason": reason}


def _is_soup_kw(kw: str) -> bool:
    return kw in ("polievka", "vyvar", "kulajda", "cibulack", "minestrone", "krem")


def estimate_all(dishes: list[Dish]) -> tuple[list[dict], str]:
    """Returns (estimates aligned with dishes, method string)."""
    token = github_token()
    if token:
        try:
            return estimate_with_ai(dishes, token), "AI (GPT-4o via GitHub Models)"
        except Exception as e:
            log.warning("AI estimation failed (%s), using keyword fallback", e)
    return [_keyword_estimate(d) for d in dishes], "keyword table (rough fallback)"


# ----------------------------------------------------------------------------
# Vision: extract dishes from an image-only menu
# ----------------------------------------------------------------------------

def extract_dishes_from_image(
    restaurant: str, image_bytes: bytes, media_type: str, day_sk: str, token: str
) -> list[Dish]:
    b64 = base64.b64encode(image_bytes).decode()
    prompt = (
        f"The image is a Slovak weekly lunch menu of restaurant {restaurant}. "
        f"Extract ONLY the dishes offered on '{day_sk.upper()}' plus any items "
        "valid for the whole week (e.g. weekly soup or weekly special). "
        'Return JSON: {"dishes": [{"name": "<dish name in Slovak>", '
        '"weight": "<portion WITH unit, like 120g/200g or 0,33l — empty if not printed. '
        'Allergen numbers are NOT weights>", '
        '"category": "<Polievka|Hlavne jedlo|Special or empty>"}]}. '
        "If that day is not in the image, return {\"dishes\": []}."
    )
    content = _chat(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{b64}", "detail": "high"},
                    },
                ],
            }
        ],
        token,
    )
    return [
        Dish(
            restaurant=restaurant,
            name=str(d.get("name", "")).strip(),
            weight=str(d.get("weight", "") or ""),
            category=str(d.get("category", "") or ""),
        )
        for d in _parse_json(content)["dishes"]
        if str(d.get("name", "")).strip()
    ]
