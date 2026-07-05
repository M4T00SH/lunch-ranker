# Protein Lunch Ranker

Personal app: ranks today's lunch dishes from 14 Bratislava restaurants by
estimated protein. Static page on GitHub Pages, refreshed by a GitHub Action
on weekday mornings. User checks it from iPhone at work — the PC is never
involved in production.

## Key facts

- Python 3.12; deps: requests, beautifulsoup4, pdfplumber (`requirements.txt`)
- Run: `python run.py` (flags: `--force`, `--day pondelok..piatok`, `--no-open`)
- AI: GitHub Models free tier (`openai/gpt-4o`), token from `gh auth token`
  locally / `GITHUB_TOKEN` in Actions. NO Anthropic API key — user explicitly
  wants zero API costs. Keyword-table fallback in `core/estimate.py`.
- One adapter file per restaurant in `adapters/`; registry in `config.py`.
- Adapter contract: `NAME`, `URL`, `scrape(ctx) -> list[Dish] | ImageMenu`.
  Raise `StaleMenuError("...")` when the site still shows an old week — the
  runner turns any adapter exception into a page warning, never a crash.
- Site quirks are documented in each adapter's docstring. Notable: UMAMI and
  MESTIANSKY share `adapters/_restaumatic.py` (menu JSON in `__NEXT_DATA__`);
  MINT/DOCK7/APOLKA parse weekly PDFs (text layer, no OCR needed); FAJNE
  JEDLO is an image → vision model.
- Debug bad parses: `logs/run-YYYY-MM-DD.log` has the raw dish list per
  restaurant.

## Verify changes

`python run.py --day pondelok --no-open` then inspect `docs/index.html` /
`docs/data.json`. Offline adapter tests against saved pages exist only in the
dev session scratchpad, not in the repo.
