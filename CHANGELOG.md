# Changelog

## 1.0.0 — 2026-10-23

- Initial public release.
- Repository layout: skill runtime at the repo root, `tools/` for packaging
  and smoke tests, and root-level install/version/license files for distribution.
- Codex, Claude Code, and OpenCode install support:
  - shared `~/.agents/skills` install
  - `~/.claude/skills` and `~/.config/opencode/skills` symlinks
  - project-local `.opencode` / `.agents` / `.claude` layout
- Codex UI metadata in `agents/openai.yaml`.
- `reg.py` CLI for openFDA, eCFR, Federal Register, ClinicalTrials.gov, PubMed,
  and the local guidance registry.
- Optional stdio MCP server with 10 tools.
- Curated 2026-10-23 guidance registry (29 entries).
- Sleep-specific playbooks for QVO/QMZ/LEL, Somryst/Sleepio, CBT-I evidence,
  QMSR, AI/PCCP, HIPAA, FTC HBNR, and state privacy law.
- Dated JSON + Markdown regulatory snapshots.
- Release packaging (`.tar.gz`, `.zip`, checksums) and OpenCode HTTP catalog.
- GitHub Actions release and Pages catalog workflows.

## Unreleased

- Add a live status checker for the guidance registry.
- Add optional `pypdf`-based 510(k) summary extraction to the release image.
- Add more sleep-adjacent predicates and AI device examples.
