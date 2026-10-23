# Changelog

## 1.3.0 — 2026-10-23

- Added a local **SQLite + FTS5 knowledge base** so prompts do not call MCP/REST
  APIs every time.
- New `reg.py kb` commands: `init`, `refresh`, `search`, `get`, `stats`,
  `stale`, `note add/list`, `export`, `ingest`.
- Bundled offline seed for key CFR sections, QVO/QMZ/LEL classifications,
  510(k) records, and Federal Register documents.
- The skill workflow is now local-first; live APIs are a refresh path for
  missing or stale entries.
- MCP server now exposes 16 tools, including `kb_search`, `kb_get`, `kb_stats`,
  `kb_note_add`, `kb_refresh`, and `kb_init`.
- `kb refresh` supports core, extended (FR/trials/PubMed), and 510(k) summary
  modes.
- Updates preserve the local KB and `snapshots/`.

## 1.2.0 — 2026-10-23

- Windows support: native `install.ps1`, PowerShell paths, and a
  `windows-latest` CI job.
- Correct trigger documentation: Codex uses `$us-sleep-regulatory`, Claude Code
  uses `/us-sleep-regulatory`, OpenCode uses `/us-sleep-regulatory` (installed
  wrapper) or `@us-sleep-regulatory`.
- Added the OpenCode `/us-sleep-regulatory` command wrapper.
- Moved the usage guide to the top of the English and Korean READMEs.
- Release workflow now gates the GitHub Release on both Linux and Windows.
- `install.ps1` preserves `snapshots/` on `-Force` and copies `README.ko.md` and
  `install.ps1` into the installed skill.

## 1.1.0 — 2026-10-23

- Added Korean README (`README.ko.md`) with install, update, and per-agent
  usage guides.
- Added an update guide for the one-liner, clone, and release-tarball flows.
- Added a post-install usage guide for Codex, Claude Code, OpenCode, MCP
  clients, and the CLI.
- Updates now preserve `snapshots/` before replacing the installed skill.
- Added a version policy and release checklist.
- The installer now also copies `README.ko.md` into the installed skill.

## 1.0.0 — 2026-10-23

- Initial public release.
- Repository layout: `skills/us-sleep-regulatory/` for the skill runtime,
  `tools/` for packaging and smoke tests, and root-level install/version/license
  files for distribution.
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
