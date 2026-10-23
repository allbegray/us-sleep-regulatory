#!/usr/bin/env python3
"""Retrieval regression eval for the local knowledge base.

Each case in the suite is a question the skill must be able to answer from the
local KB. The test is whether the right document appears in the top-k results —
not whether a model writes a good paragraph. It runs offline in well under a
second, so it can gate every change to the seed, the registry, or the search
ranking.

Usage:
  python3 tools/eval_retrieval.py
  python3 tools/eval_retrieval.py --json
  python3 tools/eval_retrieval.py --suite tests/evals/retrieval.json --top-k 3
  python3 tools/eval_retrieval.py --kb ~/.cache/us-sleep-regulatory/kb.sqlite

Exit code 0 when every case passes, 1 when any case misses.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import reg  # noqa: E402

DEFAULT_SUITE = ROOT / "tests" / "evals" / "retrieval.json"


def load_suite(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases") if isinstance(data, dict) else data
    if not isinstance(cases, list) or not cases:
        raise SystemExit(f"no cases in {path}")
    return cases


def evaluate(cases: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    """Run the suite against the currently configured KB (no init, no network)."""
    results: list[dict[str, Any]] = []
    for case in cases:
        limit = int(case.get("top_k", top_k))
        rows = reg.kb_search(case["query"], limit=limit)["results"]
        ids = [row["id"] for row in rows]
        expected = list(case.get("expect") or [])
        min_hits = int(case.get("min_hits", 1))
        hits = [doc_id for doc_id in expected if doc_id in ids]
        rank = next((index + 1 for index, doc_id in enumerate(ids) if doc_id in expected), None)
        results.append(
            {
                "id": case.get("id") or case["query"],
                "query": case["query"],
                "pass": len(hits) >= min_hits,
                "rank": rank,
                "hits": hits,
                "missing": [doc_id for doc_id in expected if doc_id not in ids],
                "ids": ids,
            }
        )
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for result in results if result["pass"])
    reciprocal_ranks = [1.0 / result["rank"] for result in results if result["rank"]]
    return {
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "hit_rate": round(passed / len(results), 3) if results else 0.0,
        "mrr": round(sum(reciprocal_ranks) / len(results), 3) if results else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieval regression eval for the local KB")
    parser.add_argument("--suite", default=str(DEFAULT_SUITE))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--kb", help="Use an existing KB instead of a temporary one.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable results.")
    args = parser.parse_args(argv)

    suite_path = Path(args.suite)
    if not suite_path.exists():
        print(f"ERROR: suite not found: {suite_path}", file=sys.stderr)
        return 2

    cases = load_suite(suite_path)
    temp_dir: str | None = None
    if args.kb:
        os.environ["US_REG_KB"] = args.kb
    else:
        temp_dir = tempfile.mkdtemp(prefix="us-reg-eval-")
        os.environ["US_REG_KB"] = str(Path(temp_dir) / "kb.sqlite")
        reg.kb_init(force=True)

    try:
        results = evaluate(cases, top_k=args.top_k)
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

    summary = summarize(results)
    if args.json:
        print(json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False))
    else:
        for result in results:
            status = "PASS" if result["pass"] else "FAIL"
            found = f"rank {result['rank']}" if result["rank"] else "miss"
            detail = ", ".join(result["hits"]) or f"missing {', '.join(result['missing'])}"
            print(f"{status}  {result['id']:<28} {found:<9} {detail}")
        print()
        print(
            f"{summary['passed']}/{summary['cases']} passed | "
            f"hit rate {summary['hit_rate']:.2f} | MRR {summary['mrr']:.2f}"
        )

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
