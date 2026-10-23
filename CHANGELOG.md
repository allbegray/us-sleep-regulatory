# Changelog

## 1.11.0 — 2026-10-23

- Added a language policy: the skill answers in the user's language. Korean
  questions get Korean memos, headings, and explanations, while official
  document titles, CFR citations, K/De Novo numbers, product codes, status
  labels, and verbatim quotes stay in English.
- Added `references/output-language.md` with a Korean heading map, a 30-term
  glossary, a worked Korean executive summary, and do/don't rules (e.g.
  "cleared" is not "approved").
- `references/memo-template.md`, `examples/README.md`, and both READMEs now
  document the language behavior.
- The CLI is now actually localized, not just the memo: `--lang ko` (or
  `US_REG_LANG=ko`) translates provenance badges (`실시간`/`캐시`/`로컬`/`혼합`)
  and table headers. JSON keys, official titles, and status labels stay English.
- The `kb` ingests `references/output-language.md` automatically, so the
  language rules are retrievable offline like the other playbooks.
- Fixed `database is locked` under concurrent KB use: journal-mode switching and
  schema creation no longer run on every connection. A regression test holds a
  write lock while opening a second connection.
- Added **beginner mode** (`references/beginner-mode.md`) for Korean developers
  new to US regulatory: a decision-first template, 30-term plain-language
  glossary, analogies (predicate = "선배 제품"), before/after example, and a
  "what you do not need to worry about yet" section. `SKILL.md` rule 11 makes
  expertise calibration explicit.
- Korean search now works. The tokenizer is Unicode-aware, strips common Korean
  particles (`규제를` → `규제`), and the LIKE fallback requires all core terms
  before relaxing to OR. `kb search "초심자"` finds the beginner guide.
  Retrieval suite grew from 25 to 28 cases.
- Added `references/query-pipeline.md`: the user's Korean question is translated
  into English retrieval terms, queried against the English sources, then
  synthesized back in Korean. Identifiers (K numbers, product codes, CFR cites)
  are never translated; the English queries are recorded in the trail. Includes
  a 45-term Korean→English map.

## 1.10.0 — 2026-10-23

- Markdown output now starts with a one-line provenance badge:
  - `live` — fetched from the network this run
  - `cache` — served from the HTTP cache (shows `cached_at`)
  - `local` — read from the local KB or the curated registry (no network)
  - `mixed` — a composite command (snapshot, predicates) combined sources
- JSON output gains `_meta.fetch` with the same value. Existing `cached` and
  `cache_fetched_at` fields are unchanged.
- Badge is printed once per command, not per row, so tables stay copy-pasteable.

## 1.9.0 — 2026-10-23

- Added ten sources (35 → 45 registry entries), each verified in a browser with
  `verified_via` evidence:
  - FDA procedural: Q-Submission Program (2025-05), De Novo Classification
    Process (2021-10), 513(g) Requests (2024-08), Medical Device Data Systems
    (2022-09), Breakthrough Devices Program (2023-09).
  - Privacy/clinical: OCR Guidance on Risk Analysis (2010-07), OCR Guidance on
    HIPAA and Cloud Computing (2016-10), FTC Health Products Compliance
    Guidance (2022-12), AASM CBT-I Clinical Practice Guideline (2021-02), and
    HHS 405(d) HICP / Cyber Gateway (2023 edition).
- Expanded the registry status vocabulary with `Business guidance`,
  `Clinical guideline`, and `Program / portal`.
- Retrieval suite grew from 15 to 25 cases (all rank 1, MRR 1.00): Q-Sub,
  De Novo, 513(g), MDDS, Breakthrough, OCR risk analysis, OCR cloud, FTC
  claims, AASM CBT-I, and 405(d).

## 1.8.0 — 2026-10-23

- Added `kb follow add|remove|list`: track extra FDA product codes beyond
  QVO/QMZ/LEL. Followed codes are refreshed with classification + 510(k)
  landscape and stored in KB metadata, so they survive `kb init --force`.
- Added `install.sh --verify` and `install.ps1 -Verify`: check the real
  directory, client links, OpenCode wrapper, and installed version.
- Added `--purge --yes` / `-Purge -Yes` to remove the local KB and HTTP cache
  (which `--uninstall` deliberately leaves behind).
- Added a weekly `source-canary` workflow: strict registry validation, strict
  reference freshness, the networked smoke test, and an issue on failure.
- Added `last_reviewed` / `review_cadence_days` frontmatter to `references/*.md`
  and `tools/check_freshness.py`. A 120-day cadence is enforced with
  `--strict` in the canary and documented in the release checklist.
- Added `pyproject.toml` (ruff: E/F/W/B), a lint CI job, and fixed the one
  unused import. Windows CI now exercises `-Sha256` and `-Verify`.

## 1.7.0 — 2026-10-23

- Added six guidance entries (29 → 35): IMDRF N10 (Key Definitions), IMDRF N23
  (QMS), Multiple Function Device Products (2020), Design Considerations for
  Interoperable Medical Devices (2017), General Principles of Software
  Validation (2002), and Postmarket Management of Cybersecurity (2016). Each
  carries `verified_via` evidence; `validate_registry.py --strict` passes.
- Added `examples/example-memo-dtc-cbti.md`: a complete worked memo (synthetic
  DTC CBT-I product, real public sources) showing claim discipline, predicate
  reasoning, QVO special controls, HIPAA posture, and a source table.
- Added a retrieval regression suite: `tests/evals/retrieval.json` and
  `tools/eval_retrieval.py`. Fifteen questions must surface the expected
  document in the top 5 (currently 15/15, MRR 0.97). It runs offline and is
  wired into the smoke test and unit tests, so seed/ranking changes regress
  loudly.
- README/SKILL layout and verification docs updated for examples and the eval.

## 1.6.0 — 2026-10-23

- Verified all 29 guidance-registry entries against their sources and added
  `verified_via` evidence to each. Four data errors found and fixed:
  the cybersecurity guidance URL (new QMS slug), the off-the-shelf software URL
  and issue date (August 2023, not September 2019), the retired SaMD clinical
  evaluation page (now cited via its Federal Register notice), and the IMDRF
  N12 URL. `tools/validate_registry.py --strict` now passes with 0 warnings.
- `tools/validate_registry.py` checks schema, status vocabulary, duplicate ids,
  shared URLs, future dates, and unsupported bulk date bumps. A shared
  `last_verified` date is accepted when every entry records `verified_via`.
- `guidance` reports `_meta.verification` (`per-entry`, `bulk-evidenced`, or
  `bulk`) plus evidence coverage.
- Fixed `kb export --format json`: the flag is honoured (a full JSON document),
  `--jsonl` remains NDJSON, and the default is still Markdown.
- `kb get` now disambiguates shared URLs: deterministic id order,
  `_meta.ambiguous` + `_meta.alternatives`, and a new `--source-type` flag
  (also exposed on the MCP `kb_get` tool).
- `kb refresh` honours `--no-cache` / `--cache-ttl`. Cached responses inside the
  TTL are reused by default, so a repeated refresh no longer re-fetches every
  source; `--no-cache` forces live requests.
- `kb search` drops English stopwords before building the FTS query and escapes
  `%`/`_` in the LIKE fallback. `QVO" OR "*` no longer matches every document
  containing "or".
- Added an offline test suite in `tests/` (KB, CLI contract, cache, search,
  refresh wiring, registry, docs/version drift, MCP surface) and a PR/push CI
  workflow.
- `tools/smoke_test.sh --offline` runs everything except `doctor` and the live
  refresh. Version consistency now also checks `scripts/reg.py`.
- `install.sh --sha256` / `install.ps1 -Sha256` (or `US_SLEEP_REG_SHA256`)
  verify a downloaded or local archive before extracting it. Downloads now go
  to a temp file instead of a `curl | tar` pipe.
- `doctor` verifies the 510(k) PDF with a HEAD request instead of re-downloading
  460 KB on every run.
- Cache writes are atomic, and retry backoff no longer holds the per-host
  semaphore while sleeping.
- `install.sh --uninstall` no longer requires a resolvable source directory.

## 1.5.0 — 2026-10-23

- Parallelized official-source fetches in `snapshot` and `kb refresh` using a
  bounded thread pool (stdlib only; no new dependency).
- Added `--jobs` (default 6, max 12) and the `US_REG_JOBS` environment variable.
- Added per-host concurrency limits and 429 `Retry-After` backoff for eCFR,
  openFDA, Federal Register, ClinicalTrials.gov, PubMed, and accessdata.
- Cold-cache benchmark on 2026-10-23: `kb refresh` 26.6s -> 13.4s;
  `snapshot` 21.1s -> 16.5s. `--jobs 1` remains a deterministic sequential run.
- MCP `kb_refresh` and `regulatory_snapshot` accept a `jobs` argument.

## 1.4.1 — 2026-10-23

- Added Claude Code desktop troubleshooting: use the Code tab, type the full
  `/us-sleep-regulatory` command when the `/` picker hides local skills, and run
  `/reload-skills` if the skill was installed during a session.
- Clarified that Cowork/cloud sessions do not read `~/.claude/skills`; enable
  the skill for the claude.ai account or use the Code tab.

## 1.4.0 — 2026-10-23

- Windows installer now auto-installs Python 3.12 per-user from python.org when
  Python 3.9+ is missing. The installer verifies the Authenticode signature,
  runs silently, and needs no admin rights.
- Added `-SkipPythonInstall` (opt out) and `-ForcePythonInstall` (repair).
- Windows CI now tests the Python auto-install path on `windows-latest`.
- README now leads with "Why use this skill": benefits, audience, and non-goals,
  in English and Korean.
- Version references updated to 1.4.0.

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
