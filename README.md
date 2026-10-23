# US Sleep Regulatory

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

### Update / uninstall

```bash
./install.sh --target all --force
./install.sh --target all --uninstall
```

The installer checks Python 3.9+, copies only skill files, skips generated
snapshots, runs `doctor` unless `--no-doctor`, and prints the MCP config with
the real path. It never edits your client configuration.

## Invoke

| Client | How |
|---|---|
| Codex CLI | `$us-sleep-regulatory` or `/skills` |
| Claude Code | `@us-sleep-regulatory` |
| OpenCode | `@us-sleep-regulatory` or just ask |
| Any MCP client | `scripts/mcp_server.py` (10 tools) |

Example:

```
@us-sleep-regulatory  우리 앱이 미국에서 CBT-I 치료 서비스인데 510(k) 필요한지,
predicate랑 HIPAA까지 같이 검토해줘.
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

## Verify

```bash
bash tools/smoke_test.sh
```

It checks Python syntax, seven upstream sources, the guidance registry, the MCP
handshake, the installer/uninstaller for all three clients, and version
consistency.

## License

MIT. Not affiliated with the FDA, HHS, or any government agency.
