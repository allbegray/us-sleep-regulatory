# US Sleep Regulatory

**English** | [한국어](README.ko.md)

A distributable Agent Skill for researching US FDA 510(k)/De Novo, SaMD, AI/ML
device software, QMSR, and HIPAA/FTC obligations for an app-based sleep-therapy
clinical service.

It works with **Codex**, **Claude Code**, and **OpenCode** from one source tree.
Install once, then trigger it with `/us-sleep-regulatory` or
`$us-sleep-regulatory` depending on the client.

> Research aid, not legal advice. Verify the current official text before a
> filing, launch, or breach decision.

## Why use this skill

A sleep-therapy app's regulatory question is three questions tangled together:

1. Is the app a medical device? (wellness vs 510(k) vs De Novo)
2. Which product code and predicate apply, and what evidence is required? (QVO/QMZ/LEL)
3. What do HIPAA, the FTC, and state law require for the clinical service and its data?

This skill answers all three from one source base.

| Benefit | What changes in practice |
|---|---|
| **Official sources** | Queries openFDA, eCFR, Federal Register, ClinicalTrials.gov, and PubMed directly. No blog posts, memory, or invented K numbers. |
| **Citation and audit trail** | Every answer carries a KB ID, URL, `retrieved_at`, and a binding/guidance/draft status. The memo can go straight into a report. |
| **Local-first speed** | 50+ seed documents in SQLite + FTS5. No API call per prompt; `kb refresh` is the only network path. |
| **Sleep-specific** | QVO/QMZ/LEL, Somryst/Sleepio/NightWare, CBT-I endpoints, QMSR, AI/PCCP, and HIPAA in one flow. |
| **Two tracks, not one** | Separates FDA 510(k) from HIPAA so "we got 510(k), therefore we are HIPAA compliant" does not survive review. |
| **DTC/prescription trap** | Flags the QVO prescription-only and adjunct requirements before you build a self-serve funnel. |
| **Repeatable output** | `snapshot`, `kb note`, and `memo-template` accumulate dated, citable research. |
| **Three clients, three OSes** | Codex, Claude Code, OpenCode; macOS, Linux, and Windows installers. |

### Who it is for

- **Founders and product managers** — DTC vs prescription, 510(k) vs wellness vs De Novo, 12-month roadmap.
- **Regulatory and quality** — predicates, QVO special controls, QMSR, software/cyber/HF evidence.
- **Engineering and security** — SRS/SDS/V&V, 524B, SBOM, human factors, AI/PCCP.
- **Clinical and medical affairs** — CBT-I endpoints, safety exclusions, trial design.
- **Investors and diligence teams** — pathway, evidence gaps, and the top regulatory risks.

### What it does not do

- It is not legal advice and does not file a 510(k)/De Novo for you.
- It does not build your QMS, run your trial, or write your submission.
- It does not survey every state medical-privacy law.
- For fast-moving guidance or new clearances, run `kb refresh` or a live command.

## Use it

### Trigger matrix

| Client | Trigger | Notes |
|---|---|---|
| **Codex CLI** | `$us-sleep-regulatory` | `/skills` lists skills. `/` is for built-in commands |
| **Claude Code** | `/us-sleep-regulatory` | The skill name is the slash command |
| **OpenCode** | `/us-sleep-regulatory` or `@us-sleep-regulatory` | `/` is the installed wrapper; `@` mentions the skill |
| **MCP client** | tools from `scripts/mcp_server.py` | For clients without a skill system |
| **CLI** | `python .../scripts/reg.py` | Direct terminal use |

> Codex custom `/prompts:*` are deprecated. Use `$us-sleep-regulatory` in Codex.
> Claude Code and OpenCode use `/us-sleep-regulatory`.

### Local knowledge base first

The skill ships with a **SQLite + FTS5** knowledge base seeded from
`references/`, the guidance registry, and `knowledge/seed/`. The first `kb`
command initializes it offline; no network call is needed.

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
python3 "$REG" kb stats
python3 "$REG" kb search "QVO predicate chronic insomnia"
python3 "$REG" kb get cfr-21-882.5801
```

Windows:

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
py -3 $REG kb stats
py -3 $REG kb search "QVO predicate chronic insomnia"
py -3 $REG kb get cfr-21-882.5801
```

`kb refresh` uses 6 parallel workers by default (cold-cache benchmark:
26.6s → 13.4s on 2026-10-23). Use `--jobs 1` for a sequential debug run.

Call live APIs only when:

- the local KB has no useful hit,
- `kb stats` / `kb stale` shows the entry is stale,
- the user asks for current or "latest" data,
- the question depends on a fast-moving source (new guidance, new clearance).

Refresh the local copy:

```bash
python3 "$REG" kb refresh --jobs 6              # CFR, classifications, 510(k), FR
python3 "$REG" kb refresh --extended --jobs 6   # + FR search, trials, PubMed
python3 "$REG" kb refresh --summaries --jobs 6  # + 510(k) summary PDFs
python3 "$REG" kb refresh --no-cache            # ignore the HTTP cache, fetch live
```

`kb refresh` reuses HTTP cache entries inside `--cache-ttl` (default 24h,
`US_REG_CACHE_TTL`), so running it twice in a row is cheap and idempotent. Pass
`--no-cache` (or `--cache-ttl 0`) when you need every source re-fetched.

Track additional FDA product codes beyond QVO/QMZ/LEL:

```bash
python3 "$REG" kb follow add QMF
python3 "$REG" kb follow list
python3 "$REG" kb follow remove QMF
```

Followed codes are fetched by the next `kb refresh` (classification + 510(k)
landscape) and are stored in the KB metadata, so they survive `kb init --force`.

Save durable conclusions after a session:

```bash
python3 "$REG" kb note add "QVO is prescription-only; DTC model is a fit gap." \
  --title "QVO vs DTC" --tags "device,qvo,strategy" \
  --source "https://www.ecfr.gov/current/title-21/section-882.5801"
python3 "$REG" kb export --format md   --out snapshots/knowledge.md
python3 "$REG" kb export --format json --out snapshots/knowledge.json
python3 "$REG" kb export --jsonl       --out snapshots/knowledge.jsonl
```

When two documents share a URL (a CFR section and its guidance-registry stub
do), `kb get` picks the first by id and reports `_meta.ambiguous` plus
`_meta.alternatives`. Pass `--source-type cfr` or use the exact id to choose.

```bash
python3 "$REG" kb get cfr-21-882.5801 --format md
python3 "$REG" kb get https://www.ecfr.gov/current/title-21/section-882.5801 --source-type guidance
```

| Content | TTL | Refresh |
|---|---|---|
| CFR | 90 days | `kb refresh` |
| Classifications / 510(k) | 30 days | `kb refresh` |
| Guidance registry | 30 days | `kb refresh` |
| Federal Register | 30 days | `kb refresh` |
| Trials / PubMed | 30 days | `kb refresh --extended` |
| 510(k) summaries | 90 days | `kb refresh --summaries` |

> Search in English technical terms (`QVO predicate`, `HIPAA BAA`, `PCCP`) for
> the best results. The agent can translate Korean questions into English
> search terms.

### Codex CLI

1. Restart Codex.
2. Run `/skills` to confirm the skill is installed.
3. Invoke it with `$us-sleep-regulatory`, or type `$` and pick it from the list.

```text
$us-sleep-regulatory 우리 앱이 CBT-I 디지털 치료제인데 QVO 510(k) predicate와
evidence gap을 정리해줘. DTC 모델이라 prescription-only 요건과 충돌하는지도 봐줘.
```

If it is not visible:

```powershell
Test-Path "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\SKILL.md"
```

`True` means the files are in place; restart Codex. Older builds that only read
`~/.codex/skills` can use `--target codex-legacy` (`install.sh`) or
`-Target codex-legacy` (`install.ps1`).

### Claude Code

1. Restart Claude Code.
2. Invoke `/us-sleep-regulatory`.

```text
/us-sleep-regulatory 우리 서비스가 HIPAA covered entity인지 business associate인지
판단하고, PHI 데이터 맵과 BAA 체크리스트를 만들어줘.
```

If it is not visible:

```powershell
Get-ChildItem "$env:USERPROFILE\.claude\skills\us-sleep-regulatory"
```

**Claude Code desktop:** use the **Code** tab (a local session), not Cowork.
Local sessions read `~/.claude/skills`. If the `/` picker does not show the
skill, type `/us-sleep-regulatory` in full and press Enter; this is a known
desktop picker regression, and the skill still runs. Run `/reload-skills` if you
installed it while a session was open. Cowork/cloud sessions do not read
`~/.claude/skills`; enable the skill for your claude.ai account or use the Code
tab.

### OpenCode

1. Restart OpenCode.
2. Invoke `/us-sleep-regulatory`, or mention `@us-sleep-regulatory`.

```text
/us-sleep-regulatory QVO / QMZ / LEL 중 우리 제품에 맞는 product code를 골라줘.
Somryst와 Sleepio를 predicate로 비교하고, QMSR 기준 evidence gap도 정리해줘.
```

The `/` command is a wrapper installed to
`~/.config/opencode/commands/us-sleep-regulatory.md` (Windows:
`%USERPROFILE%\.config\opencode\commands\us-sleep-regulatory.md`). The `@`
mention is OpenCode's native skill invocation.

If it is not visible:

```powershell
Test-Path "$env:USERPROFILE\.config\opencode\skills\us-sleep-regulatory\SKILL.md"
Test-Path "$env:USERPROFILE\.config\opencode\commands\us-sleep-regulatory.md"
```

### MCP client

If the client has no skill system, run the MCP server.

**macOS/Linux:**

```jsonc
{
  "mcp": {
    "servers": {
      "us-sleep-reg": {
        "type": "local",
        "command": [
          "python3",
          "/Users/<you>/.agents/skills/us-sleep-regulatory/scripts/mcp_server.py"
        ],
        "cwd": "."
      }
    }
  }
}
```

**Windows:**

```jsonc
{
  "mcp": {
    "servers": {
      "us-sleep-reg": {
        "type": "local",
        "command": [
          "python",
          "C:\\Users\\<you>\\.agents\\skills\\us-sleep-regulatory\\scripts\\mcp_server.py"
        ],
        "cwd": "."
      }
    }
  }
}
```

Tools: `fda_510k_search`, `fda_510k_get`, `fda_classification`,
`fda_predicates`, `ecfr_get`, `fr_search`, `trials_search`, `pubmed_search`,
`guidance_search`, `regulatory_snapshot`, `kb_search`, `kb_get`, `kb_stats`,
`kb_note_add`, `kb_refresh`, `kb_init`.

### CLI

**macOS/Linux:**

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
python3 "$REG" doctor
python3 "$REG" predicates --product-code QVO --format md
python3 "$REG" 510k-get K191716 --fetch-summary --format md
python3 "$REG" snapshot
```

**Windows PowerShell:**

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
py -3 $REG doctor
py -3 $REG predicates --product-code QVO --format md
py -3 $REG 510k-get K191716 --fetch-summary --format md
py -3 $REG snapshot
```

### Good first prompt

The skill first asks for the intended use, care model, AI role, data types, and
current decision. Answer those and it produces a memo with sources, retrieval
dates, confidence labels, and open questions.

- FDA device path and predicate comparison
- QVO/QMZ/LEL product-code fit
- 510(k)/De Novo evidence gaps
- HIPAA covered entity/BA analysis and PHI data map
- AI/LLM/PCCP review
- 90-day roadmap
- Source table with URLs and `retrieved_at`

## Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all
```

Or clone:

```bash
git clone https://github.com/allbegray/us-sleep-regulatory.git
cd us-sleep-regulatory
./install.sh
```

### Windows (PowerShell)

`install.ps1` works natively on Windows. It copies files instead of creating
symlinks, so it does not require Developer Mode or admin rights.

**Download and run (recommended):**

```powershell
Invoke-WebRequest `
  -Uri https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.ps1 `
  -OutFile "$env:TEMP\us-sleep-install.ps1"

powershell -ExecutionPolicy Bypass -File "$env:TEMP\us-sleep-install.ps1" -Target all
```

**One-liner (defaults to `-Target all`):**

```powershell
irm https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.ps1 | iex
```

Use the downloaded form when you need `-Force`, `-Uninstall`, or `-Target`.

**From a clone:**

```powershell
git clone https://github.com/allbegray/us-sleep-regulatory.git
cd us-sleep-regulatory
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all
```

#### Windows prerequisites

- **Python 3.9+** is installed automatically (per-user, from python.org,
  signature verified) when missing. Use `-SkipPythonInstall` to opt out, or
  `-ForcePythonInstall` to repair. Manual install also works.
- Verify:

  ```powershell
  py -3 --version
  # or
  python --version
  ```

- If you see an execution-policy error:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1
  ```

  Or allow it for the current session only:

  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```

- **Git** is only needed for the clone method.
- **Git Bash / WSL** can run `install.sh`, but `install.ps1` is the recommended
  native path.

#### Windows install paths

| Client | Path |
|---|---|
| Codex | `%USERPROFILE%\.agents\skills\us-sleep-regulatory` |
| Claude Code | `%USERPROFILE%\.claude\skills\us-sleep-regulatory` |
| OpenCode | `%USERPROFILE%\.config\opencode\skills\us-sleep-regulatory` |
| OpenCode `/` command | `%USERPROFILE%\.config\opencode\commands\us-sleep-regulatory.md` |

### Targets

| Target | Real path | Links | Client |
|---|---|---|---|
| `all` (default) | `~/.agents/skills/...` | both | all |
| `auto` | `~/.agents/skills/...` | only configured clients | all |
| `codex` | `~/.agents/skills/...` | none | Codex |
| `claude` | `~/.claude/skills/...` | none | Claude Code |
| `opencode` | `~/.config/opencode/skills/...` | none | OpenCode |
| `project` | `./.opencode/skills/...` | `./.agents/skills`, `./.claude/skills` | current repo |
| `codex-legacy` | `~/.codex/skills/...` | none | older Codex builds |
| `PATH` | explicit directory | none | custom |

### Verify

**macOS/Linux:**

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
cat "$HOME/.agents/skills/us-sleep-regulatory/VERSION"
python3 "$REG" doctor
```

**Windows:**

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
Get-Content "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\VERSION"
py -3 $REG doctor
```

`doctor` reports `7/7 checks passed` when openFDA, eCFR, Federal Register,
ClinicalTrials.gov, PubMed, and the 510(k) PDF path are reachable.

## Update

### Latest version

**macOS/Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all --force
```

**Windows:**

```powershell
Invoke-WebRequest `
  -Uri https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.ps1 `
  -OutFile "$env:TEMP\us-sleep-install.ps1"

powershell -ExecutionPolicy Bypass -File "$env:TEMP\us-sleep-install.ps1" -Target all -Force
```

### From a clone

```bash
git pull
./install.sh --target all --force
```

Windows:

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Force
```

### Pin a version

```bash
US_SLEEP_REG_VERSION=1.0.0
```

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Force -Version 1.0.0
```

Or use a release artifact:

```bash
./install.sh \
  --from https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.9.0/us-sleep-regulatory-v1.9.0.tar.gz \
  --target all --force
```

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 `
  -From https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.9.0/us-sleep-regulatory-v1.9.0.zip `
  -Target all -Force
```

### Verify the download

Release artifacts ship with `SHA256SUMS`. `install.sh --sha256` and
`install.ps1 -Sha256` verify the archive before extracting it.

```bash
SHA="$(curl -fsSL https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.9.0/SHA256SUMS | awk '/tar.gz/{print $1}')"
./install.sh \
  --from https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.9.0/us-sleep-regulatory-v1.9.0.tar.gz \
  --target all --sha256 "$SHA"
```

```powershell
$SHA = (Get-Content .\SHA256SUMS | Select-String '\.zip').Line.Split()[0]
powershell -ExecutionPolicy Bypass -File .\install.ps1 `
  -From .\us-sleep-regulatory-v1.9.0.zip -Target all -Sha256 $SHA
```

### What an update preserves

- `snapshots/` is backed up before the replacement and restored afterward.
- `references/`, `scripts/`, `SKILL.md`, and other skill files are replaced.
  Keep custom edits in a separate repo or in `snapshots/`.
- The local KB is outside the skill directory
  (`~/.cache/us-sleep-regulatory/kb.sqlite`), so updates do not delete it. Run
  `kb refresh` to pick up new sources.
- Check the installed `VERSION` file after updating.

### Verify after an update

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
cat "$HOME/.agents/skills/us-sleep-regulatory/VERSION"
python3 "$REG" doctor
python3 "$REG" guidance --max-age-days 30 --format md
```

Windows:

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
Get-Content "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\VERSION"
py -3 $REG doctor
```

### Uninstall

```bash
./install.sh --target all --uninstall
```

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Uninstall
```

`--uninstall` removes the skill but keeps the local KB and HTTP cache.
`--purge --yes` removes those too (the KB may contain your notes):

```bash
./install.sh --target all --uninstall --purge --yes
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Uninstall -Purge -Yes
```

### Verify an installation

```bash
./install.sh --target all --verify
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Verify
```

It checks the real directory, the client symlinks, the OpenCode `/` wrapper,
and prints the installed version. Exit code 1 means something is missing.

## What it does

- **FDA device track**: device vs wellness vs CDS, SaMD, product code, predicate,
  510(k)/De Novo/PMA, QVO/QMZ/LEL, QMSR, software/cyber/human-factors evidence.
- **HIPAA/privacy track**: covered entity vs business associate, PHI data map,
  BAA, Security Rule safeguards, breach notification, FTC HBNR, state overlay.
- **Sleep domain**: CBT-I, ISI/PSQI, trial design, safety, predicate landscape.
- **AI/ML**: PCCP, AI lifecycle guidance, GenAI discussion paper, human
  oversight, vendor/BAA analysis.
- **Local knowledge base**: SQLite + FTS5 index of `references/`, the guidance
  registry, and `knowledge/seed/`. Offline by default; `kb refresh` is the only
  network path.
- **Audit trail**: every response carries source, URL, retrieval date, and cache
  status. `snapshot` writes dated JSON + Markdown.

## Layout

```
.
├── SKILL.md
├── README.md
├── README.ko.md
├── install.sh
├── install.ps1
├── VERSION
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── agents/openai.yaml
├── commands/opencode/us-sleep-regulatory.md
├── knowledge/seed/
├── references/
├── scripts/
│   ├── reg.py
│   └── mcp_server.py
├── snapshots/
├── examples/
├── tests/
│   ├── test_reg.py
│   └── evals/retrieval.json
├── tools/
│   ├── package.sh
│   ├── build_catalog.py
│   ├── validate_registry.py
│   ├── eval_retrieval.py
│   └── smoke_test.sh
└── .github/workflows/
```

## Docs

- [SKILL.md](SKILL.md) — agent workflow and guardrails
- [references/source-catalog.md](references/source-catalog.md) — endpoints,
  query syntax, rate limits, failure modes
- [references/device-pathway.md](references/device-pathway.md) — device/SaMD/
  510(k)/De Novo/QMSR/AI
- [references/hipaa-privacy.md](references/hipaa-privacy.md) — covered entity/
  BAA/Security Rule/breach/FTC/state
- [references/sleep-domain.md](references/sleep-domain.md) — CBT-I, endpoints,
  predicates, trial design
- [references/memo-template.md](references/memo-template.md) — auditable memo
- [examples/example-memo-dtc-cbti.md](examples/example-memo-dtc-cbti.md) —
  worked example memo (synthetic product, real sources)
- `knowledge/seed/` — offline CFR / 510(k) / Federal Register seed

## Versioning

`MAJOR.MINOR.PATCH`:

- **PATCH** — docs, typos, source URL fixes.
- **MINOR** — new sources, playbooks, CLI options, client support.
- **MAJOR** — breaking CLI/config/layout changes.

Release checklist:

1. Bump `VERSION`, `install.sh` `DEFAULT_VERSION`, `install.ps1`
   `$DefaultVersion`, and `scripts/reg.py` `VERSION`.
2. Add a `CHANGELOG.md` entry.
3. Run `python3 -m unittest discover -s tests` and
   `bash tools/smoke_test.sh --offline`.
4. Run `bash tools/smoke_test.sh` (network) and `bash tools/package.sh`.
5. Verify registry entries individually: `python3 tools/validate_registry.py --strict`.
   Check reference freshness: `python3 tools/check_freshness.py --strict`.
6. Commit, tag `vX.Y.Z`, push. GitHub Actions tests Linux and Windows, creates the
   release, and deploys the catalog.

## Verify

```bash
python3 -m unittest discover -s tests -v   # offline, no fixtures or network
python3 tools/eval_retrieval.py            # 25 questions -> expected doc ids
python3 tools/check_freshness.py           # reference review dates
bash tools/smoke_test.sh --offline         # syntax, versions, registry, KB, evals, MCP, installer
bash tools/smoke_test.sh                   # + the seven upstream sources
```

`--offline` is the PR/CI mode: it skips `doctor` and the live refresh, so a
flaky FDA endpoint cannot block a merge. The release workflow runs the full
networked smoke test, and `install.ps1` on `windows-latest`. A weekly
`source-canary` workflow runs the networked suite plus strict registry and
reference-freshness checks, and opens an issue on failure.

## License

MIT. Not affiliated with the FDA, HHS, or any government agency.
