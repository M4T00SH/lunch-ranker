"""Protein Lunch Ranker — one command: python run.py

Scrapes today's lunch menus, ranks dishes by estimated protein and writes
docs/index.html (+ data.json). Opens the page in the browser unless --no-open.

Options:
  --force        re-scrape even if today's results are already cached
  --day NAME     pretend it is another weekday (pondelok..piatok) for debugging
  --no-open      don't open the browser (used by GitHub Actions)
"""
import argparse
import logging
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.common import DAYS_SK
from core.runner import run, DOCS


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--day", choices=DAYS_SK[:5])
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    day_idx = DAYS_SK.index(args.day) if args.day else None
    data = run(day_idx=day_idx, force=args.force or args.day is not None)

    print(f"\n{len(data['dishes'])} dishes ranked, {len(data['warnings'])} warnings")
    for w in data["warnings"]:
        print(f"  ! {w}")

    if not args.no_open:
        webbrowser.open((DOCS / "index.html").as_uri())


if __name__ == "__main__":
    main()
