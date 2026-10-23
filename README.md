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
`guidance_search`, `regulatory_snapshot`.

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

- **Python 3.9+** from [python.org](https://www.python.org/downloads/windows/).
  Check **Add python.exe to PATH**.
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
  --from https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.2.0/us-sleep-regulatory-v1.2.0.tar.gz \
  --target all --force
```

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 `
  -From https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.2.0/us-sleep-regulatory-v1.2.0.zip `
  -Target all -Force
```

### What an update preserves

- `snapshots/` is backed up before the replacement and restored afterward.
- `references/`, `scripts/`, `SKILL.md`, and other skill files are replaced.
  Keep custom edits in a separate repo or in `snapshots/`.
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

## What it does

- **FDA device track**: device vs wellness vs CDS, SaMD, product code, predicate,
  510(k)/De Novo/PMA, QVO/QMZ/LEL, QMSR, software/cyber/human-factors evidence.
- **HIPAA/privacy track**: covered entity vs business associate, PHI data map,
  BAA, Security Rule safeguards, breach notification, FTC HBNR, state overlay.
- **Sleep domain**: CBT-I, ISI/PSQI, trial design, safety, predicate landscape.
- **AI/ML**: PCCP, AI lifecycle guidance, GenAI discussion paper, human
  oversight, vendor/BAA analysis.
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
├── agents/openai.yaml
├── commands/opencode/us-sleep-regulatory.md
├── references/
├── scripts/
│   ├── reg.py
│   └── mcp_server.py
├── snapshots/
├── tools/
│   ├── package.sh
│   ├── build_catalog.py
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

## Versioning

`MAJOR.MINOR.PATCH`:

- **PATCH** — docs, typos, source URL fixes.
- **MINOR** — new sources, playbooks, CLI options, client support.
- **MAJOR** — breaking CLI/config/layout changes.

Release checklist:

1. Bump `VERSION`, `install.sh` `DEFAULT_VERSION`, and `install.ps1`
   `$DefaultVersion`.
2. Add a `CHANGELOG.md` entry.
3. Run `bash tools/smoke_test.sh`.
4. Run `bash tools/package.sh`.
5. Commit, tag `vX.Y.Z`, push. GitHub Actions tests Linux and Windows, creates the
   release, and deploys the catalog.

## Verify

```bash
bash tools/smoke_test.sh
```

Checks Python syntax, the seven upstream sources, the guidance registry, the MCP
handshake, the installer/uninstaller for all three clients, and version
consistency. The release workflow also runs `install.ps1` on `windows-latest`.

## License

MIT. Not affiliated with the FDA, HHS, or any government agency.
