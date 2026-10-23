---
last_reviewed: 2026-10-23
review_cadence_days: 120
---

# Source catalog — verified 2026-10-23

This is the retrieval layer. It exists so the agent stops guessing URLs, query
parameters, and field names. Every endpoint below was exercised on 2026-10-23
unless marked otherwise.

**Citation rule:** a claim about law, regulation, guidance, or a clearance is
not usable until it carries `source`, `url`, `retrieved_at`, and an `as_of` or
`issued` date. If a page redirects to a generic landing page, treat the
document as archived and say so.

## Source matrix

| Source | Answers | Auth | Endpoint | Freshness | Main caveat |
|---|---|---|---|---|---|
| openFDA | 510(k)/De Novo, classification, recalls, MAUDE, PMA, UDI | Optional key | `https://api.fda.gov` | `meta.last_updated` | Convenience copy, not the official decision database |
| eCFR | Codified regulations (21 CFR, 45 CFR, 16 CFR) | None | `https://www.ecfr.gov/api/versioner/v1` | `up_to_date_as_of` | Requires gzip; use an as-of date |
| Federal Register | Final rules, proposed rules, guidance notices | None | `https://www.federalregister.gov/api/v1` | Live | Full-text search is not title search |
| ClinicalTrials.gov v2 | Trial design, endpoints, enrollment, sponsors | None | `https://clinicaltrials.gov/api/v2` | Live | Sparse records; request fields explicitly |
| PubMed E-utilities | Peer-reviewed evidence | None (key optional) | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils` | Live | 3 req/sec without a key |
| accessdata.fda.gov | 510(k) detail pages and summary PDFs | None | `https://www.accessdata.fda.gov` | Live | Some records have no public summary |
| fda.gov HTML | Guidance landing pages, AI device list, indexes | None | `https://www.fda.gov` | Live | Akamai blocks many shell clients; use web-fetch/browser |
| hhs.gov HTML | OCR guidance, breach portal | None | `https://www.hhs.gov/hipaa` | Live | 403 in this environment; use eCFR/FR or a browser |
| IMDRF | SaMD N12/N41 international framework | None | `https://www.imdrf.org` | Static | Some shell TLS handshakes fail; use web-fetch |

## openFDA

Base: `https://api.fda.gov`

### Endpoints that matter

| Endpoint | Use |
|---|---|
| `/device/510k.json` | 510(k) and De Novo clearances (DEN numbers appear here) |
| `/device/classification.json` | Product code, class, 21 CFR regulation number, flags |
| `/device/pma.json` | PMA approvals and supplements |
| `/device/recall.json` | Recall records |
| `/device/enforcement.json` | Enforcement reports |
| `/device/event.json` | MAUDE adverse events |
| `/device/registrationlisting.json` | Establishment registration and device listing |
| `/device/udi.json` | UDI/GUDID records |

### Query syntax

```
?search=field:value
?search=field:"exact phrase"
?search=field:value+AND+field2:value2      # URL-encoded spaces become +
?search=decision_date:[2024-01-01+TO+2026-12-31]
?limit=100&skip=0
```

- Quote exact phrases. `device_name:"Somryst"` works; bare `insomnia` does not
  behave like full-text search on `/device/510k`.
- `device_name` on `/device/510k` is the **trade name** (Somryst, Sleepio), not
  the classification name (Computerized Behavioral Therapy Device For Insomnia).
  Use `/device/classification` for the classification name, then search 510(k)
  by `product_code`.
- `AND` between clauses; no `OR` needed for most work.
- Date ranges are inclusive.
- `limit` max 100 per request. Paginate with `skip` if you truly need more, but
  for a product-code landscape 100 is usually enough.

### Key 510(k) fields

`k_number`, `applicant`, `device_name`, `product_code`, `decision_date`,
`decision_code`, `decision_description`, `clearance_type`,
`statement_or_summary`, `advisory_committee`, `regulation_number`,
`device_class`, `date_received`, `expedited_review_flag`.

`decision_code` is an internal code; use `decision_description` when explaining
the outcome. `statement_or_summary` tells you whether a public summary exists,
not whether the PDF is guaranteed.

### Rate limits

- No key: 240 requests/minute and 1,000/day per IP.
- With key: 240 requests/minute and 120,000/day per key.
- Get a key at `https://open.fda.gov/apis/authentication/`.
- The CLI reads `OPENFDA_API_KEY` and never puts the key into the cache key.

### Data caveats

- `meta.last_updated` is the dataset timestamp, not the decision date.
- openFDA is a convenience copy. Confirm the current decision and the summary
  on `accessdata.fda.gov` before relying on a predicate.
- Product-code → regulation-number mappings can be legacy. Example verified
  2026-10-23: LEL (Device, Sleep Assessment) maps to 21 CFR 882.5050, whose
  heading is "Biofeedback device." Always read the CFR text and the predicate's
  cleared intended use; do not infer the regulation from the product-code name.
- A cleared device is not automatically a valid predicate. Predicate analysis
  is about intended use and technological characteristics, not just product code.

### Useful direct calls

```bash
# All QVO clearances
curl -s 'https://api.fda.gov/device/510k.json?search=product_code:QVO&limit=100'

# One record
curl -s 'https://api.fda.gov/device/510k.json?search=k_number:K191716&limit=1'

# Classification for a product code
curl -s 'https://api.fda.gov/device/classification.json?search=product_code:QVO&limit=1'

# 510(k) summary PDF (works from shell)
curl -L -o K191716.pdf 'https://www.accessdata.fda.gov/cdrh_docs/pdf19/K191716.pdf'
```

The CLI wraps all of this:

```bash
python3 scripts/reg.py 510k-search --product-code QVO
python3 scripts/reg.py 510k-get K191716 --fetch-summary
python3 scripts/reg.py classify --product-code QVO
python3 scripts/reg.py predicates --product-code QVO
```

## eCFR

Base: `https://www.ecfr.gov/api/versioner/v1`

### Endpoints

| Endpoint | Use |
|---|---|
| `/titles.json` | Current `up_to_date_as_of` date per title |
| `/full/{YYYY-MM-DD}/title-{n}.xml?part=...&section=...` | Full text of a part or section |
| `/versions/title-{n}.json?part=...` | Amendment history |
| `/api/search/v1/results?query=...` | Full-text search across the CFR |

### Rules

- The full-text endpoint **requires compression**. Send
  `Accept-Encoding: gzip` or it returns HTTP 406 with a message telling you so.
- Use `titles.json` to get a valid as-of date. Do not hard-code a date that may
  be in the future or before an amendment.
- Section requests: `title-45.xml?part=164&section=164.308`.
- Part requests: `title-21.xml?part=820`.
- Citation format: `45 CFR 164.308`, `21 CFR 882.5801`, `16 CFR 318.5`.

### Current-as-of anchors (2026-10-23)

| Citation | Heading | Why it matters |
|---|---|---|
| 21 CFR 882.5801 | Computerized behavioral therapy device for psychiatric disorders | QVO; Class II; prescription only; adjunct to clinician-supervised outpatient treatment |
| 21 CFR 882.5705 | Digital therapy device to reduce sleep disturbance for psychiatric conditions | QMZ; nightmare disorder/PTSD, not general insomnia |
| 21 CFR 882.5050 | Biofeedback device | LEL maps here in openFDA, but the heading is a legacy mismatch |
| 21 CFR 820.1 | Scope (QMSR) | Part 820 now incorporates ISO 13485:2016 by reference |
| 45 CFR 164.308 | Administrative safeguards | HIPAA Security Rule |
| 45 CFR 164.402 | Definitions (breach) | Breach notification analysis |

```bash
python3 scripts/reg.py cfr 45 164.308
python3 scripts/reg.py cfr 21 882.5801
python3 scripts/reg.py cfr 21 --part 820 --full
```

## Federal Register

Base: `https://www.federalregister.gov/api/v1`

### Query parameters

```
conditions[term]="exact phrase"
conditions[agencies][]=food-and-drug-administration
conditions[type][]=RULE|PRORULE|NOTICE|PRESDOCU
conditions[publication_date][gte]=2024-01-01
conditions[publication_date][lte]=2026-12-31
per_page=20
order=newest
fields[]=title&fields[]=citation&fields[]=html_url
```

Agency slugs verified: `food-and-drug-administration`,
`health-and-human-services-department`, `federal-trade-commission`. The CLI
also maps `fda`, `hhs`, `ftc`, `cms`, `onc`, `nih`.

**Search behavior:** `conditions[term]` is full-text, not title-only. A search
for `"HIPAA Security Rule"` returns many documents that mention the phrase.
Use exact phrases, add the agency, and sort by newest; then read the title.

### Documents to anchor on

| Document | Citation | Date | Use |
|---|---|---|---|
| QMSR final rule | 89 FR 7496 | 2024-02-02 | Effective 2026-02-02; 21 CFR 820 incorporates ISO 13485 |
| QMSR technical amendments | 90 FR 55978 | 2025-12-04 | Current technical fixes |
| HIPAA Security Rule NPRM | 90 FR 898 | 2025-01-06 | Proposed, not final as of 2026-10-23 |
| FTC Health Breach Notification Rule | 89 FR 47028 | 2024-05-30 | 16 CFR 318; non-HIPAA health apps |
| AI PCCP final guidance notice | 2024-28361 | 2024-12-04 | Final guidance announced |
| AI lifecycle draft guidance notice | 90 FR 1154 | 2025-01-07 | Draft; verify final status |
| HF content final guidance notice | 91 FR 32061 | 2026-05-29 | Final; implemented 2026-08-01 |
| GenAI discussion paper | docket FDA-2026-N-7874 | 2026-08-18 | Not guidance; policy direction only |

```bash
python3 scripts/reg.py fr-search --term '"software as a medical device"' --agency fda --since 2024-01-01
python3 scripts/reg.py fr-get 2024-30983
```

## ClinicalTrials.gov v2

Base: `https://clinicaltrials.gov/api/v2`

```
GET /studies?query.cond=insomnia&query.intr=cognitive%20behavioral%20therapy&pageSize=20
GET /studies?query.term=digital%20CBT-I&fields=NCTId,BriefTitle,OverallStatus,Phase,EnrollmentCount
```

- `query.cond`, `query.intr`, `query.term`, `filter.overallStatus`,
  `pageSize` (max 1000), `fields`, `nextPageToken`.
- The response nests most data under `protocolSection`.
- Use trials to understand endpoints, comparators, sample sizes, and
  recruitment, not to prove efficacy. Efficacy claims need the publications.

```bash
python3 scripts/reg.py trials --condition insomnia --intervention "cognitive behavioral therapy"
```

## PubMed E-utilities

Base: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`

```
esearch.fcgi?db=pubmed&term=...&retmode=json&retmax=20&sort=relevance&tool=...&email=...
esummary.fcgi?db=pubmed&id=...&retmode=json
efetch.fcgi?db=pubmed&id=...&retmode=xml
```

- 3 requests/second without an API key; 10/second with a key.
- Set `NCBI_EMAIL` so NCBI can contact you if a query misbehaves.
- `esummary` is enough for titles, journals, dates, authors, DOI.

```bash
python3 scripts/reg.py pubmed --term "digital CBT-I insomnia randomized" --limit 10
```

## HTML-only sources and their failure modes

| Source | Shell behavior (2026-10-23) | Workaround |
|---|---|---|
| `www.fda.gov/regulatory-information/...` | HTTP 404 "abuse-detection-apology" | Use the agent's web-fetch/browser tool |
| `www.fda.gov/media/{id}/download` | HTTP 404 from curl; web-fetch can fetch CSV/XLSX | Use web-fetch; for PDFs, use the browser or `read` after download |
| `www.hhs.gov/hipaa/...` | HTTP 403 | Use eCFR/FR for binding text; use a browser for OCR guidance |
| `www.accessdata.fda.gov/...` | Works (510(k) detail and PDFs) | Use directly |
| `www.imdrf.org/...` | TLS handshake may fail from curl | Use web-fetch/browser |
| `www.ecfr.gov/current/...` | Redirects to `unblock.federalregister.gov` for bots | Use the eCFR API for text |

When a page is blocked, do not fabricate its contents. Say "could not retrieve"
and use the official structured source that covers the same proposition. For
example, a HIPAA guidance page is nice-to-have; 45 CFR 164.308 is the binding
text.

## The local guidance registry

`references/guidance-registry.json` is a curated index of the guidance documents
that matter most for this product. Each entry carries:

- `status`: Final / Draft / Proposed rule / Discussion paper / Archived
- `issued`: issue month or date
- `docket`
- `url` and `pdf`
- `topics`: device, software, ai, cyber, hipaa, sleep, etc.
- `last_verified`
- `notes`: what it is for and what to watch

The CLI reports `age_days` and `stale` (default >120 days). A non-stale entry is
still not proof of current status; open the URL and confirm the banner.

```bash
python3 scripts/reg.py guidance --topic ai
python3 scripts/reg.py guidance --query "human factors"
python3 scripts/reg.py guidance --status Draft
```

## Snapshot and audit trail

`reg.py snapshot` writes two files:

- `snapshots/YYYY-MM-DD-regulatory-snapshot.json` — machine-readable, with
  per-section `_meta.url`, `_meta.retrieved_at`, `_meta.cached`
- `snapshots/YYYY-MM-DD-regulatory-snapshot.md` — a human-readable digest

This is how knowledge accumulates without re-searching: commit the snapshot,
then cite the snapshot date and the underlying URL. Re-run the snapshot when a
guidance is updated or a new clearance appears.

## Politeness and failure handling

- Cache for 24h by default. Use `--no-cache` only when freshness matters.
- Do not run the same query in parallel; the CLI is sequential on purpose.
- On HTTP 429/5xx, the CLI retries with exponential backoff.
- If openFDA returns `NOT_FOUND`, treat it as zero results, not an outage.
- If eCFR returns 406, you forgot gzip.
- If the Federal Register returns `{"errors":{"agencies":"invalid value"}}`,
  you used the wrong agency slug; use the full slug from the matrix.

## What this catalog deliberately does not do

- It does not scrape fda.gov or hhs.gov HTML.
- It does not use a third-party proxy or an LLM-generated summary as a source.
- It does not treat a draft, discussion paper, or enforcement-discretion policy
  as binding law.
- It does not replace a regulatory consultant or counsel for a filing decision.
