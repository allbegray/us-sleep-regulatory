---
name: us-sleep-regulatory
description: Research US FDA 510(k)/De Novo, SaMD, AI/ML device software, QMSR, and HIPAA/FTC obligations for an app-based sleep therapy clinical service. Use for predicate searches, product-code and classification questions, pathway decisions, evidence-gap analyses, HIPAA covered-entity/BAA/security reviews, or a cited regulatory memo. Pulls openFDA, eCFR, Federal Register, ClinicalTrials.gov, and PubMed through scripts instead of manual web searching.
---

# US Sleep Regulatory

A research and decision skill for an app-based sleep-therapy clinical service in
the United States. It replaces ad-hoc web searching with official APIs, a
curated guidance index, and a memo format that keeps the retrieval trail.

## Non-negotiable rules

1. **Two tracks, separately.** FDA device status and HIPAA/privacy status are
   independent. Answer both. A 510(k) clearance is not HIPAA compliance.
2. **Local first.** Default to the local knowledge base (`kb stats`, `kb search`,
   `kb get`). Live APIs are for `kb refresh` or when the KB is missing or stale.
3. **Claims drive the pathway.** The intended use and every marketing claim
   decide whether the software is a device. Read the claims before naming a
   product code or predicate.
4. **Cite or label.** Every legal/regulatory statement carries a source URL, a
   retrieval date, and a status: Binding / Final guidance / Draft / Proposed /
   Discussion paper / Data / Assumption. If you could not retrieve it, say so.
5. **Binding beats guidance.** 21 CFR and 45 CFR are binding. FDA guidance is
   nonbinding. A draft, discussion paper, or enforcement-discretion policy is
   not a requirement.
6. **Verify status, not just the URL.** FDA pages get archived, superseded, and
   redirected. The local registry is an index, not proof of current status. Open
   the page or the Federal Register notice when the answer matters.
7. **A product code is not a predicate.** Predicate analysis is intended use +
   technological characteristics. A clearance under the same code can still be
   unusable.
8. **Do not invent.** No invented K numbers, guidance dates, CFR sections, or
   "FDA approved" claims. 510(k) devices are "cleared," not "approved."
9. **Not legal advice.** For a filing decision, a novel intended use, a De Novo,
   or a breach response, recommend regulatory counsel.

## Workflow

### Step 1 — Intake (mandatory)

Ask these ten questions, or extract the answers from the user's message. Mark
unknowns explicitly.

1. Exact intended use and the claims you want to make.
2. Who uses it: patient, clinician, or both?
3. Prescription/clinician-ordered, or direct-to-consumer self-serve?
4. Condition, population, and age range.
5. What the software does: CBT-I, sleep restriction, tracking, triage, AI
   coaching, clinician decision support?
6. AI/ML/LLM: what does it decide or generate? Does it change the clinical
   advice?
7. Do you bill insurance, contract with providers/employers, or operate
   cash-pay?
8. What data: sleep diary, ISI/PSQI/PHQ-9, wearables, audio/video, chat, claims?
9. Current status: idea, prototype, live product, predicate lined up, prior
   submission?
10. What decision are you making now: pathway, predicate, evidence plan, HIPAA
    gap, investor diligence, launch review?

**Completion:** all ten answered or marked unknown, with the impact of each
unknown stated.

### Step 2 — Device triage

Read `references/device-pathway.md`. Produce a one-page decision table:

| Question | Answer | Source |
|---|---|---|
| Is it a device? | yes / no / uncertain | statute, guidance |
| Wellness, CDS, or device? | ... | general wellness / CDS guidance |
| SaMD? | ... | IMDRF / FDA |
| Product code, class, regulation | ... | openFDA + eCFR |
| Predicate(s) | ... | openFDA + 510(k) summary |
| Pathway | wellness / 510(k) / De Novo / PMA | reasoned |
| Biggest evidence gap | ... | ... |

**Completion:** a recommendation with the fact that would change it, and no
"it depends" without naming the resolving fact.

### Step 3 — Retrieve the evidence (local first)

The skill ships with a local SQLite knowledge base seeded from `references/`,
the guidance registry, and `knowledge/seed/`. It answers most questions without
a network call.

```bash
SKILL_DIR="/absolute/path/to/us-sleep-regulatory"
REG="$SKILL_DIR/scripts/reg.py"

python3 "$REG" kb stats
python3 "$REG" kb search "QVO predicate chronic insomnia"
python3 "$REG" kb get cfr-21-882.5801
```

Use live commands only when:

- `kb search` has no useful hit,
- `kb stats` or `kb stale` shows the relevant entry is stale,
- the user asks for current or "latest" data,
- the question depends on a fast-moving source (new guidance, new clearance).

Refresh the local copy:

```bash
python3 "$REG" kb refresh --jobs 6              # CFR, classifications, 510(k), FR
python3 "$REG" kb refresh --extended --jobs 6   # + FR search, trials, PubMed
python3 "$REG" kb refresh --summaries --jobs 6  # + 510(k) summary PDFs (needs extractor)
python3 "$REG" kb refresh --no-cache            # bypass the HTTP cache, fetch live
```

Refresh reuses HTTP cache entries inside `--cache-ttl` (default 24h,
`US_REG_CACHE_TTL`), so a second run is cheap and idempotent. `--no-cache` (or
`--cache-ttl 0`) forces live fetches.

| Content | TTL | Refresh |
|---|---|---|
| CFR sections | 90 days | `kb refresh` |
| Classifications / 510(k) | 30 days | `kb refresh` |
| Guidance registry | 30 days | `kb refresh` |
| Federal Register | 30 days | `kb refresh` |
| Trials / PubMed | 30 days | `kb refresh --extended` |
| 510(k) summaries | 90 days | `kb refresh --summaries` |

`--jobs` defaults to 6 (max 12) and parallelizes independent HTTP requests. Use
`--jobs 1` when you need a deterministic sequential run for debugging.

Live commands, when the KB is insufficient:

```bash
python3 "$REG" predicates --product-code QVO
python3 "$REG" 510k-get K191716 --fetch-summary
python3 "$REG" cfr 21 882.5801
python3 "$REG" fr-search --term '"software as a medical device"' --agency fda --since 2024-01-01
python3 "$REG" trials --condition insomnia --intervention "cognitive behavioral therapy"
python3 "$REG" pubmed --term "digital CBT-I insomnia randomized" --limit 10
python3 "$REG" snapshot
```

After the research session, save the durable conclusion and citations:

```bash
python3 "$REG" kb note add "QVO is prescription-only; DTC model is a fit gap." \
  --title "QVO vs DTC" --tags "device,qvo,strategy" \
  --source "https://www.ecfr.gov/current/title-21/section-882.5801"
python3 "$REG" kb export --format md   --out snapshots/knowledge.md
python3 "$REG" kb export --format json --out snapshots/knowledge.json
python3 "$REG" kb export --jsonl       --out snapshots/knowledge.jsonl
```

When two documents share a URL (a CFR section and its guidance-registry stub
do), `kb get` returns the first by id and reports `_meta.ambiguous` with
`_meta.alternatives`. Use the exact id or `--source-type` to disambiguate.

```bash
python3 "$REG" kb get cfr-21-882.5801 --format md
python3 "$REG" kb get https://www.ecfr.gov/current/title-21/section-882.5801 --source-type guidance
```

**Completion:** each conclusion has a source URL + `retrieved_at`; at least one
binding source for each legal conclusion; guidance status checked against the
official page when the registry is stale or the stakes are high. The conclusion
is saved as a KB note or export, not just left in chat.

### Step 4 — HIPAA/privacy track

Read `references/hipaa-privacy.md`. Produce:

- Status: covered entity / business associate / outside HIPAA / uncertain.
- The fact that resolves the uncertainty (billing flow, contracts, data flow).
- A PHI data map (data -> source -> storage -> recipients -> BAA -> retention).
- BAA inventory and the top five Security Rule gaps.
- Breach readiness and the FTC/state overlay.
- AI vendor review if any PHI reaches an LLM.

**Completion:** a status, a data map, and five evidence-backed gaps. "We are
HIPAA compliant" without evidence is not an answer.

### Step 5 — Write the memo

Use `references/memo-template.md`. Write to the user's requested path, or to
`snapshots/YYYY-MM-DD-<slug>-memo.md`. `examples/example-memo-dtc-cbti.md` is a
complete worked example (synthetic product, real sources) of the format and
level of reasoning expected. Include:

- Executive summary with the decision.
- Device analysis and predicate table.
- Pathway recommendation and evidence gaps.
- HIPAA analysis and data map.
- AI/ML analysis.
- 90-day roadmap.
- Open questions and assumptions.
- Sources with URLs and retrieval dates.
- "What would change this answer."

**Completion:** a reader can trace every conclusion to a source or an explicit
assumption, and knows the next decision.

## Narrow-question shortcuts

| User asks | Do this |
|---|---|
| "Do we need a 510(k)?" | Intake + device triage + `kb search "QVO predicate"` + live `predicates` only if stale |
| "Find predicates" | `kb search "QVO predicate"` then `kb get 510k-K191716` / `kb get 510k-K233577` |
| "Is this HIPAA?" | HIPAA track + `kb search "HIPAA covered entity BAA"` |
| "What does FDA say about AI?" | `kb search "AI PCCP lifecycle"`, then `kb refresh` if stale |
| "What changed recently?" | `guidance --max-age-days 30`, `fr-search --since ...`, `snapshot` |
| "Build a regulatory snapshot" | `python3 "$REG" snapshot` |
| "Review our draft claims" | Claims matrix + device/wellness/CDS boundary |
| "We are DTC, not prescription" | QVO fit analysis + wellness vs De Novo options |

## Environment notes

- `fda.gov` and `hhs.gov` HTML often block shell clients. Use the agent's
  web-fetch/browser tool for those pages. The scripts use official APIs and
  `accessdata.fda.gov` for 510(k) PDFs.
- `openFDA` works without a key at 240 req/min and 1,000/day. Set
  `OPENFDA_API_KEY` for heavier use.
- The local KB is `~/.cache/us-sleep-regulatory/kb.sqlite`. Set `US_REG_KB` to
  move it. `kb search`/`kb get` are offline; `kb refresh` is the network path.
- The HTTP cache is `~/.cache/us-sleep-regulatory` (24h default). Use
  `--no-cache` when freshness matters.
- `--fetch-summary` downloads the 510(k) PDF. If no PDF text extractor is
  installed, install `pypdf` (`python3 -m pip install pypdf`) or poppler
  (`pdftotext`), or use the agent's PDF reader on the downloaded file.
- The MCP server is optional: `scripts/mcp_server.py` exposes the same tools
  over stdio. See `README.md` for the OpenCode config.

## Reference map

| File | Use |
|---|---|
| `references/source-catalog.md` | Endpoints, query syntax, rate limits, failure modes |
| `references/device-pathway.md` | Device/SaMD/510(k)/De Novo/QMSR/AI analysis |
| `references/hipaa-privacy.md` | Covered entity/BAA/Security Rule/breach/FTC/state |
| `references/sleep-domain.md` | CBT-I, endpoints, predicates, trial design, safety |
| `references/guidance-registry.json` | Curated guidance index with last-verified dates |
| `references/memo-template.md` | Auditable memo and claims matrix |
| `examples/example-memo-dtc-cbti.md` | Worked example of the memo format (synthetic product; not evidence) |
| `knowledge/seed/` | Offline CFR, classification, 510(k), FR seed documents |
| `scripts/reg.py` | Unified CLI + local knowledge base |
| `scripts/mcp_server.py` | Optional stdio MCP server |

## Stop conditions

Stop and ask, rather than guessing, when:

- The user has not stated the intended use or the claims.
- The answer turns on whether the service bills insurance or contracts with a
  covered entity.
- The product is DTC/non-prescription but claims to treat insomnia.
- The product uses an LLM to generate clinical advice.
- The user asks for a legal opinion, a filing decision, or a breach conclusion.
- A source is unavailable and the conclusion depends on it.

In those cases, state the assumption, the conservative posture, and the exact
fact or document needed to resolve it.
