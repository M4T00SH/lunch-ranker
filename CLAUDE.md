# Protein Lunch Ranker

Personal app: ranks today's lunch dishes from 15 Bratislava restaurants by
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
- Ranking is mains-only: soups are filtered in `core/runner.py` using
  `is_soup()` in `core/common.py` — category is trusted first ('hlavné'
  beats a soup mention; NOSTALGIA mains end with '+ polievka'), dish-name
  start is the fallback for unlabeled menus. Dropped soups are logged as
  `SOUP dropped`.

- Schedule: the ONLY trigger is cron-job.org (user's account, jobs 8031253
  + 8031261) calling the workflow_dispatch API at 10:45 + 11:30
  Europe/Bratislava Mon-Fri with the fine-grained PAT "lunch-ranker-cron".
  GitHub's own cron was removed 2026-07-10: it was dead for weeks, then
  revived 2026-07-09 firing hours late (~13:30+) and overwriting the page
  in the afternoon after restaurants had swapped menus. If cron-job.org
  ever dies the page just goes stale (date is printed on it) — re-add
  crons or dispatch manually. The crons also fire on weekends (seen Sun
  2026-07-20) — user accepts this, it's harmless (stale-warning page).
  (PAT: Actions read+write, this repo only, no
  expiration. During the dead-scheduler debugging we ruled out
  fork/default-branch/workflow-state, unlinked commit email, platform
  incident; re-push, disable/enable and file rename didn't help either.)
- WERK markup change 2026-07: dish rows are .smartlunch-wrap (no longer
  .smartlunch-days) and ALL carry smartlunch-monday regardless of real day —
  adapter assigns days by header-row order, never by weekday class.

## Verify changes

`python run.py --day pondelok --no-open` then inspect `docs/index.html` /
`docs/data.json`. Offline adapter tests against saved pages exist only in the
dev session scratchpad, not in the repo.
