#!/usr/bin/env python3
"""Check that reference playbooks carry a recent review date.

A regulatory reference rots silently. `last_reviewed` in each reference file is
the date a human last read it against the current sources; this checker makes
that visible before the content is a year old.

Usage:
  python3 tools/check_freshness.py
  python3 tools/check_freshness.py --strict
  python3 tools/check_freshness.py --dir references --max-age-days 120 --json

Exit codes:
  0  every file is present and inside its cadence (or --strict is off)
  1  a file is missing a valid last_reviewed, or --strict and a file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / "references"
DEFAULT_CADENCE = 120


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta


def evaluate(paths: list[Path], today: date | None = None, cadence: int = DEFAULT_CADENCE) -> list[dict[str, Any]]:
    today = today or date.today()
    results: list[dict[str, Any]] = []
    for path in paths:
        meta = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        raw = meta.get("last_reviewed", "")
        try:
            limit = int(meta.get("review_cadence_days", cadence) or cadence)
        except ValueError:
            limit = cadence
        row: dict[str, Any] = {
            "file": path.name,
            "last_reviewed": raw or None,
            "cadence_days": limit,
            "age_days": None,
            "status": "missing",
        }
        try:
            reviewed = date.fromisoformat(raw)
        except ValueError:
            results.append(row)
            continue
        age = (today - reviewed).days
        row["age_days"] = age
        row["status"] = "stale" if age > limit else "ok"
        results.append(row)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check reference review dates")
    parser.add_argument("--dir", default=str(DEFAULT_DIR))
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_CADENCE)
    parser.add_argument("--strict", action="store_true", help="Fail when a file is stale, not just missing.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    directory = Path(args.dir)
    paths = sorted(directory.glob("*.md"))
    if not paths:
        print(f"ERROR: no markdown files in {directory}", file=sys.stderr)
        return 2

    results = evaluate(paths, cadence=args.max_age_days)
    problems = [row for row in results if row["status"] == "missing"]
    stale = [row for row in results if row["status"] == "stale"]

    if args.json:
        print(json.dumps({"results": results, "missing": len(problems), "stale": len(stale)}, indent=2))
    else:
        for row in results:
            age = "?" if row["age_days"] is None else str(row["age_days"])
            print(f"{row['status'].upper():<7} {row['file']:<28} {row['last_reviewed'] or '-':<12} age {age}d / {row['cadence_days']}d")
        print()
        print(f"{len(results)} files | {len(problems)} missing last_reviewed | {len(stale)} stale")

    if problems:
        print("ERROR: add `last_reviewed: YYYY-MM-DD` to the files above.", file=sys.stderr)
        return 1
    if args.strict and stale:
        print("ERROR: stale reference files (review or bump last_reviewed).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
