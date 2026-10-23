#!/usr/bin/env python3
"""Build an OpenCode HTTP skill catalog from a staged skill directory.

Usage:
  python3 build_catalog.py <catalog_dir> <version>

The catalog layout expected by OpenCode is:

  <catalog_dir>/index.json
  <catalog_dir>/us-sleep-regulatory/SKILL.md
  <catalog_dir>/us-sleep-regulatory/references/...
  <catalog_dir>/us-sleep-regulatory/scripts/...

index.json:
  {"skills":[{"name":"us-sleep-regulatory","version":"1.0.0","files":[...]}]}
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SKIP_PARTS = {"__pycache__", ".git", ".github", "dist", ".DS_Store", ".idea", "tests"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
# Maintainer-only files: keep them in the release tarball, omit from the
# OpenCode HTTP catalog so end-user installs stay small.
SKIP_NAMES = {".gitignore", "build_catalog.py", "package.sh", "smoke_test.sh"}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: build_catalog.py <catalog_dir> [version]", file=sys.stderr)
        return 2
    catalog_dir = Path(sys.argv[1]).resolve()
    version = sys.argv[2] if len(sys.argv) > 2 else "0.0.0"
    skill_dir = catalog_dir / "us-sleep-regulatory"
    if not (skill_dir / "SKILL.md").exists():
        print(f"missing: {skill_dir / 'SKILL.md'}", file=sys.stderr)
        return 1

    files: list[str] = []
    checksums: dict[str, str] = {}
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        if path.name in SKIP_NAMES:
            continue
        rel_posix = rel.as_posix()
        if rel_posix.startswith("snapshots/") and rel_posix != "snapshots/.gitkeep":
            continue
        if rel_posix in {"index.json", "SHA256SUMS"}:
            continue
        files.append(rel_posix)
        checksums[rel_posix] = hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "skills": [
            {
                "name": "us-sleep-regulatory",
                "version": version,
                "files": files,
            }
        ]
    }
    (catalog_dir / "index.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (catalog_dir / "checksums.json").write_text(
        json.dumps({"version": version, "files": checksums}, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [f"{digest}  us-sleep-regulatory/{name}" for name, digest in checksums.items()]
    (catalog_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"catalog: {catalog_dir}")
    print(f"files:   {len(files)}")
    print(f"version: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
