# US Sleep Regulatory

**English** | [한국어](README.ko.md)

A distributable Agent Skill for researching US FDA 510(k)/De Novo, SaMD, AI/ML
device software, QMSR, and HIPAA/FTC obligations for an app-based sleep-therapy
clinical service.

It works with **Codex**, **Claude Code**, and **OpenCode** from one source tree.
It replaces ad-hoc web searching with official APIs, a curated 2026 guidance
index, and a memo format that keeps the retrieval trail.

> Research aid, not legal advice. Verify the current official text before a
> filing, launch, or breach decision.

## Install

### One command

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all
```

The default install copies the skill once to
`~/.agents/skills/us-sleep-regulatory` and links:

```
~/.claude/skills/us-sleep-regulatory           -> ~/.agents/skills/...
~/.config/opencode/skills/us-sleep-regulatory  -> ~/.agents/skills/...
```

Codex reads `~/.agents/skills` as its user scope. OpenCode reads it as a global
compatibility source. Claude Code reads `~/.claude/skills` and follows the
symlink.

### From a clone

```bash
git clone https://github.com/allbegray/us-sleep-regulatory.git
cd us-sleep-regulatory
./install.sh
```

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

### Update

Re-run the installer with `--force`. It replaces the skill files and backs up
and restores `snapshots/`:

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all --force
```

From a clone:

```bash
git pull
./install.sh --target all --force
```

Pin a version:

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory US_SLEEP_REG_VERSION=1.0.0 \
    bash -s -- --target all --force
```

Or install a specific release tarball:

```bash
./install.sh \
  --from https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.1.0/us-sleep-regulatory-v1.1.0.tar.gz \
  --target all --force
```

Verify after an update:

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
cat "$HOME/.agents/skills/us-sleep-regulatory/VERSION"
python3 "$REG" doctor
```

Uninstall:

```bash
./install.sh --target all --uninstall
```

The installer checks Python 3.9+, copies only skill files, skips generated
snapshots, runs `doctor` unless `--no-doctor`, and prints the MCP config with
the real path. It never edits your client configuration.

## Use it in your agent tool

| Client | How |
|---|---|
| Codex CLI | `/skills` to list, `$us-sleep-regulatory` to invoke |
| Claude Code | `@us-sleep-regulatory` |
| OpenCode | `@us-sleep-regulatory` or just ask |
| Any MCP client | `scripts/mcp_server.py` (10 tools) |

### Codex CLI

1. Restart Codex.
2. Run `/skills` to confirm the skill is installed.
3. Invoke it with `$us-sleep-regulatory`, or type `$` and pick it from the list.

```text
$us-sleep-regulatory 우리 앱이 CBT-I 디지털 치료제인데 QVO 510(k) predicate와
evidence gap을 정리해줘. DTC 모델이라 prescription-only 요건과 충돌하는지도 봐줘.
```

If it is not visible:

```bash
test -f "$HOME/.agents/skills/us-sleep-regulatory/SKILL.md" && echo OK
```

`OK` means the files are in place; restart Codex. Older builds that only read
`~/.codex/skills` can use `--target codex-legacy`.

### Claude Code

1. Restart Claude Code.
2. Mention the skill with `@us-sleep-regulatory`.

```text
@us-sleep-regulatory 우리 서비스가 HIPAA covered entity인지 business associate인지
판단하고, PHI 데이터 맵과 BAA 체크리스트를 만들어줘.
```

If it is not visible:

```bash
ls -l "$HOME/.claude/skills/us-sleep-regulatory"
```

The symlink should point at `~/.agents/skills/us-sleep-regulatory`. Restart
Claude Code after fixing the link.

### OpenCode

1. Restart OpenCode.
2. Mention `@us-sleep-regulatory`, or just ask a matching regulatory question.

```text
@us-sleep-regulatory QVO / QMZ / LEL 중 우리 제품에 맞는 product code를 골라줘.
Somryst와 Sleepio를 predicate로 비교하고, QMSR 기준 evidence gap도 정리해줘.
```

If it is not visible:

```bash
ls -l "$HOME/.config/opencode/skills/us-sleep-regulatory"
ls -l "$HOME/.agents/skills/us-sleep-regulatory"
```

OpenCode reads both locations; either one with `SKILL.md` is enough.

### MCP client

If the client has no skill system, run the MCP server:

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

Tools: `fda_510k_search`, `fda_510k_get`, `fda_classification`,
`fda_predicates`, `ecfr_get`, `fr_search`, `trials_search`, `pubmed_search`,
`guidance_search`, `regulatory_snapshot`.

The full per-client walkthrough in Korean is in
[README.ko.md](README.ko.md#설치-후-ai-에이전트에서-사용하기).

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

### CLI examples

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"

python3 "$REG" doctor
python3 "$REG" predicates --product-code QVO --format md
python3 "$REG" 510k-get K191716 --fetch-summary --format md
python3 "$REG" cfr 21 882.5801 --format md
python3 "$REG" guidance --topic ai --format md
python3 "$REG" snapshot
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

## Layout

```
.
├── SKILL.md
├── README.md
├── README.ko.md
├── install.sh
├── VERSION
├── LICENSE
├── CHANGELOG.md
├── agents/openai.yaml
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

## Release and catalog

```bash
bash tools/package.sh
```

Produces `dist/us-sleep-regulatory-v<version>.tar.gz`, `.zip`, `SHA256SUMS`,
and an OpenCode HTTP catalog under `dist/catalog/`.

- `release.yml` runs the smoke test, builds the artifacts, and attaches them to
  the GitHub Release on a `v*` tag.
- `pages.yml` publishes `dist/catalog` to GitHub Pages on `main`.

Add the catalog URL once:

```jsonc
{
  "skills": ["https://allbegray.github.io/us-sleep-regulatory/"]
}
```

## Versioning

`MAJOR.MINOR.PATCH`:

- **PATCH** — docs, typos, source URL fixes.
- **MINOR** — new sources, playbooks, CLI options, client support.
- **MAJOR** — breaking CLI/config/layout changes.

Release checklist:

1. Bump `VERSION` and `install.sh` `DEFAULT_VERSION`.
2. Add a `CHANGELOG.md` entry.
3. Run `bash tools/smoke_test.sh`.
4. Run `bash tools/package.sh`.
5. Commit, tag `vX.Y.Z`, push. GitHub Actions creates the release and deploys
   the catalog.

Users update by re-running the one-liner (latest) or setting
`US_SLEEP_REG_VERSION=X.Y.Z` (pinned).

## Verify

```bash
bash tools/smoke_test.sh
```

It checks Python syntax, seven upstream sources, the guidance registry, the MCP
handshake, the installer/uninstaller for all three clients, and version
consistency.

## License

MIT. Not affiliated with the FDA, HHS, or any government agency.
