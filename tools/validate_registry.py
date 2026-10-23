#!/usr/bin/env python3
"""Validate the curated guidance registry.

The registry is the skill's most trust-sensitive data file: every entry claims a
`last_verified` date, and the agent is told to cite it. This checker enforces
structure and surfaces the failure mode the file cannot detect by itself — a
bulk date bump that makes every entry look freshly verified.

Usage:
  python3 tools/validate_registry.py
  python3 tools/validate_registry.py references/guidance-registry.json --strict
  python3 tools/validate_registry.py --max-bulk-share 0.5

Exit codes:
  0  valid (warnings allowed unless --strict)
  1  errors, or warnings under --strict
  2  the file could not be read or parsed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = REPO_ROOT / "references" / "guidance-registry.json"

REQUIRED_ENTRY_KEYS = ("id", "title", "status", "issued", "topics", "url", "last_verified")
OPTIONAL_ENTRY_KEYS = ("docket", "pdf", "notes", "verified_via")

# Status vocabulary used by SKILL.md and guidance_search().
VALID_STATUSES = {
    "Final",
    "Final rule",
    "Final (international)",
    "Final (NIST)",
    "Draft",
    "Proposed rule",
    "Discussion paper (not guidance)",
    "Archived / verify",
    "Binding regulation",
    "Live database",
    "Live index",
    "Live tool",
}

ISSUED_RE = re.compile(r"^(current|\d{4}(-\d{2}(-\d{2})?)?)$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
URL_RE = re.compile(r"^https?://\S+$")

BULK_SHARE_DEFAULT = 0.8
BULK_MIN_ENTRIES = 6


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate(data: object, *, max_bulk_share: float = BULK_SHARE_DEFAULT) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Pure function so tests can call it directly."""
    errors: list[str] = []
    warnings: list[str] = []
    today = date.today()

    if not isinstance(data, dict):
        return ["registry root must be a JSON object"], []

    for key in ("schema_version", "last_updated", "entries"):
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    if "last_updated" in data:
        parsed = _parse_date(data["last_updated"])
        if parsed is None:
            errors.append("last_updated must be an ISO date (YYYY-MM-DD)")
        elif parsed > today + timedelta(days=1):
            errors.append(f"last_updated is in the future: {parsed.isoformat()}")

    entries = data.get("entries")
    if not isinstance(entries, list):
        return errors + ["entries must be a JSON array"], warnings
    if not entries:
        return errors + ["entries must not be empty"], warnings

    policy = data.get("verification_policy")
    requires_evidence = isinstance(policy, str) and bool(policy.strip())

    seen_ids: dict[str, int] = {}
    urls: dict[str, list[str]] = {}
    verified_dates: list[str] = []

    for index, entry in enumerate(entries):
        where = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} must be an object")
            continue

        entry_id = entry.get("id")
        if isinstance(entry_id, str):
            where = f"entries[{index}] ({entry_id})"
            if entry_id in seen_ids:
                errors.append(f"{where}: duplicate id (first seen at entries[{seen_ids[entry_id]}])")
            seen_ids[entry_id] = index
            if not ID_RE.match(entry_id):
                errors.append(f"{where}: id must be lowercase kebab-case")
        else:
            errors.append(f"{where}: id is required and must be a string")

        for key in REQUIRED_ENTRY_KEYS:
            if key not in entry:
                errors.append(f"{where}: missing required key: {key}")

        for key in entry:
            if key not in REQUIRED_ENTRY_KEYS and key not in OPTIONAL_ENTRY_KEYS:
                warnings.append(f"{where}: unknown key: {key}")

        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{where}: title must be a non-empty string")

        status = entry.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{where}: unknown status {status!r}")

        issued = entry.get("issued")
        if isinstance(issued, str):
            if not ISSUED_RE.match(issued):
                errors.append(f"{where}: issued must be 'current', YYYY, YYYY-MM, or YYYY-MM-DD")
        else:
            errors.append(f"{where}: issued must be a string")

        topics = entry.get("topics")
        if not isinstance(topics, list) or not topics:
            errors.append(f"{where}: topics must be a non-empty array")
        elif any(not isinstance(topic, str) or not topic.strip() for topic in topics):
            errors.append(f"{where}: topics must contain non-empty strings")

        url = entry.get("url")
        if not isinstance(url, str) or not URL_RE.match(url):
            errors.append(f"{where}: url must be an http(s) URL")
        elif url in urls:
            urls[url].append(str(entry_id))
        else:
            urls[url] = [str(entry_id)]

        pdf = entry.get("pdf")
        if pdf is not None and (not isinstance(pdf, str) or not URL_RE.match(pdf)):
            errors.append(f"{where}: pdf must be an http(s) URL when present")

        verified_via = entry.get("verified_via")
        if verified_via is not None and (not isinstance(verified_via, str) or not verified_via.strip()):
            errors.append(f"{where}: verified_via must be a non-empty string when present")
        if requires_evidence and not (isinstance(verified_via, str) and verified_via.strip()):
            warnings.append(f"{where}: missing verified_via (verification_policy is set)")

        verified = entry.get("last_verified")
        parsed = _parse_date(verified)
        if parsed is None:
            errors.append(f"{where}: last_verified must be an ISO date (YYYY-MM-DD)")
        else:
            verified_dates.append(parsed.isoformat())
            if parsed > today + timedelta(days=1):
                errors.append(f"{where}: last_verified is in the future: {parsed.isoformat()}")

    for url, ids in urls.items():
        if len(ids) > 1:
            warnings.append(f"shared url ({', '.join(ids)}): {url} — kb_get needs an exact id or source_type")

    # Bulk-bump detection: the point of a per-entry date is that entries age
    # independently. If nearly all share one date, the signal is meaningless.
    if len(verified_dates) >= BULK_MIN_ENTRIES:
        value, count = Counter(verified_dates).most_common(1)[0]
        share = count / len(verified_dates)
        if share >= max_bulk_share:
            # A shared date is only a problem when it is unsupported. Entries
            # that record what the page said (verified_via) can legitimately
            # share the day they were all re-checked.
            unevidenced = [
                str(entry.get("id"))
                for entry in entries
                if isinstance(entry, dict)
                and entry.get("last_verified") == value
                and not str(entry.get("verified_via") or "").strip()
            ]
            if unevidenced:
                warnings.append(
                    f"bulk verification: {count}/{len(verified_dates)} entries share last_verified={value} "
                    f"({share:.0%}); {len(unevidenced)} lack verified_via. Re-verify entries individually "
                    f"so staleness means something."
                )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate references/guidance-registry.json")
    parser.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument(
        "--max-bulk-share",
        type=float,
        default=BULK_SHARE_DEFAULT,
        help=f"Warn when this share of entries shares one last_verified date (default {BULK_SHARE_DEFAULT}).",
    )
    args = parser.parse_args(argv)

    path = Path(args.path)
    try:
        data = load_registry(path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate(data, max_bulk_share=args.max_bulk_share)
    entries = data.get("entries", []) if isinstance(data, dict) else []

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors or (args.strict and warnings):
        print(f"INVALID: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1

    print(f"OK: {len(entries)} entries, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
