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

- Schedule: GitHub's cron scheduler is DEAD for this repo — zero scheduled
  runs ever fired (confirmed 2026-07-07 with same-day test crons). Ruled out:
  fork/default-branch/workflow-state, unlinked commit email, platform
  incident. Tried without success: re-push, disable/enable cycle, file rename
  (update-menus.yml → daily-refresh.yml). The 4 UTC crons + dst-guard stay in
  the workflow as a free backup, but the real trigger is external:
  cron-job.org (user's account, jobs 8031253 + 8031261) calls the
  workflow_dispatch API at 10:45 + 11:30 Europe/Bratislava Mon-Fri using a
  fine-grained PAT "lunch-ranker-cron" (Actions: read+write, this repo only,
  no expiration). Set up + end-to-end verified 2026-07-07; first live proof
  expected 2026-07-08 10:45. cron-job.org handles DST (timezone-aware), so
  the dst-guard only matters for the backup GitHub crons.
- WERK markup change 2026-07: dish rows are .smartlunch-wrap (no longer
  .smartlunch-days) and ALL carry smartlunch-monday regardless of real day —
  adapter assigns days by header-row order, never by weekday class.

## Verify changes

`python run.py --day pondelok --no-open` then inspect `docs/index.html` /
`docs/data.json`. Offline adapter tests against saved pages exist only in the
dev session scratchpad, not in the repo.
