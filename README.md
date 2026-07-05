# Protein Lunch Ranker

Scrapes today's lunch (denné/obedové) menus from 14 Bratislava restaurants,
estimates protein and calories for every dish with a free AI model, and
publishes one ranked table (highest protein first) as a static page.

**Live page:** GitHub Pages serves `docs/index.html` — open it on any phone.
A GitHub Action re-scrapes automatically on weekday mornings (~9:25, 10:40
and 11:55 Bratislava time) and commits the refreshed page.

## Run locally

```
pip install -r requirements.txt
python run.py
```

Opens `docs/index.html` in the browser. Results are cached per day in
`docs/data.json`; use `--force` to re-scrape, `--day utorok` to preview
another weekday. Raw extracted dishes per restaurant are logged to `logs/`.

AI estimation uses GitHub Models (free) — it needs a GitHub token: in Actions
this is automatic; locally it is picked up from `gh auth token` (GitHub CLI)
or a `GITHUB_TOKEN` env var. Without a token it falls back to a rough Slovak
keyword table and FAJNE JEDLO (image-only menu) is skipped with a warning.

## How it works

- `run.py` — entry point (CLI flags above)
- `config.py` — the restaurant list
- `adapters/<restaurant>.py` — one scraper per restaurant; each knows that
  site's real structure (HTML, embedded JSON, weekly PDF, or menu image)
- `core/common.py` — HTTP session, Slovak day/date helpers, `Dish` model
- `core/estimate.py` — batched protein/kcal call + keyword fallback + vision
  extraction for image menus
- `core/render.py` / `core/runner.py` — page rendering and orchestration
- `.github/workflows/update-menus.yml` — the weekday schedule

Adapters fail independently: a broken site becomes a small warning on the
page ("couldn't read X today"), never a crash. Adapters also detect stale
menus (site still shows last week) and warn instead of ranking old dishes.

## Adding a restaurant

1. Create `adapters/newplace.py` with `NAME`, `URL` and `scrape(ctx)`
   returning a list of `Dish` (or an `ImageMenu` for image-only menus).
2. Add the module to the list in `config.py`.
