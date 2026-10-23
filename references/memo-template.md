# Regulatory memo template

Use this template for every substantive answer. It is designed to be auditable:
each conclusion points to a source, and each source carries a retrieval date.

## Confidence labels

| Label | Meaning | Example |
|---|---|---|
| **Binding** | Statute, regulation, final rule, or court order | 21 CFR 882.5801; 45 CFR 164.308 |
| **Final guidance** | FDA/HHS interpretation; not binding but strong evidence of expectations | June 2023 software guidance; Feb 2026 cybersecurity guidance |
| **Draft / proposed** | Not for implementation; may change | Jan 2025 AI lifecycle draft; 2025 HIPAA Security NPRM |
| **Discussion paper** | Policy direction only; no requirements | Aug 2026 GenAI discussion paper |
| **Enforcement discretion** | FDA says it does not intend to enforce in defined circumstances | General wellness policy; mobile medical apps policy |
| **Data** | openFDA/eCFR/FR/ClinicalTrials/PubMed record | K191716; 45 CFR 164.308 text |
| **Assumption** | Stated, not verified | "We assume the service bills commercial insurance" |

Never present a draft, discussion paper, or enforcement-discretion policy as
binding. If you are unsure, say "verify" and name the exact page.

---

# Regulatory position memo — [product / feature]

**As of:** YYYY-MM-DD  
**Prepared by:** [agent / team]  
**Scope:** [US federal FDA device + HIPAA/privacy; exclude state-by-state clinical licensure unless flagged]  
**Status:** Draft for discussion; not legal advice

## 1. Executive summary

- [ ] **Device status:** [device / not a device / uncertain] because [one sentence].
- [ ] **Pathway:** [wellness / 510(k) / De Novo / PMA / CDS / unclear] with [predicate or rationale].
- [ ] **Biggest regulatory risk:** [one sentence].
- [ ] **Biggest evidence gap:** [one sentence].
- [ ] **HIPAA posture:** [covered entity / business associate / outside HIPAA / uncertain] with [one sentence].
- [ ] **Decision needed:** [one sentence].

## 2. Product and intended use

| Item | Answer |
|---|---|
| Product | [name/version] |
| User | [patient / clinician / both] |
| Setting | [DTC / prescription / clinic / employer / health plan] |
| Condition | [chronic insomnia / comorbid insomnia / nightmare / other] |
| Intervention | [CBT-I / sleep restriction / tracking / AI coaching / other] |
| Age | [adult / adolescent / pediatric] |
| Claims | [exact claims] |
| Hardware/wearables | [none / watch / ring / audio / video] |
| AI/LLM | [none / rules / ML / LLM / agentic] |
| Data | [sleep diary / ISI / PHQ-9 / audio / wearable / claims] |

**Intended-use statement (draft):**

> [One paragraph. Name the condition, population, setting, and clinical role.
> Avoid words that create claims you cannot support.]

**Claims we are deliberately not making:**

- [ ] "treats" / "cures" / "replaces medication" / "standalone therapy"
- [ ] "clinically proven" without a specific trial and endpoint
- [ ] "HIPAA compliant" without evidence
- [ ] "FDA approved" (510(k) is "cleared," not "approved")

## 3. FDA device analysis

### 3.1 Is it a device?

| Question | Answer | Source |
|---|---|---|
| Does it meet the FD&C Act 201(h) definition? | [yes/no/uncertain] | [S1] |
| Does a statutory exclusion apply (wellness, CDS, EHR, etc.)? | [yes/no/uncertain] | [S2] |
| Is it SaMD or software in a device? | [SaMD/SiMD] | [S3] |
| Is the function patient-facing or clinician-facing? | [patient/clinician] | [S4] |

**Reasoning:** [3–6 sentences. Address the strongest counterargument.]

### 3.2 Classification

| Item | Value | Source |
|---|---|---|
| Product code | [QVO/QMZ/LEL/other] | [S5] |
| Class | [I/II/III] | [S5] |
| Regulation | [21 CFR ...] | [S6] |
| Special controls | [list] | [S6] |
| Prescription status | [yes/no] | [S6] |

**Discrepancy check:** does the product-code name match the CFR heading and the
predicate's cleared intended use? [Note any mismatch, e.g., LEL → 882.5050
"Biofeedback device"; QVO → 882.5801 "psychiatric disorders."]

### 3.3 Predicate table

| Predicate | K/De Novo | Date | Intended use | Population | Technology | Why it fits / does not fit |
|---|---|---|---|---|---|---|
| [Somryst] | K191716 | 2020-03-23 | prescription CBT-I | 22+ chronic insomnia | app, 6 cores, dashboard | [ ] |
| [Sleepio] | K233577 | 2024-08-05 | prescription CBT-I, adjunct | 18+ | app + web, dashboard | [ ] |
| [other] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

**Predicate conclusion:** [same intended use + similar technology / different
intended use / different technology / no predicate].

### 3.4 Pathway recommendation

| Option | Fit | Evidence burden | Main risk |
|---|---|---|---|
| Wellness / non-device | [ ] | [ ] | [ ] |
| 510(k) | [ ] | [ ] | [ ] |
| De Novo | [ ] | [ ] | [ ] |
| PMA | [ ] | [ ] | [ ] |
| CDS | [ ] | [ ] | [ ] |

**Recommendation:** [one option, with the condition that would change it.]

### 3.5 Evidence gaps

| Gap | Why it matters | What would close it | Owner | Timing |
|---|---|---|---|---|
| [Clinical model validation] | QVO special control | [RCT / fidelity study] | [ ] | [ ] |
| [Software documentation] | QVO special control | [SRS/SDS/V&V] | [ ] | [ ] |
| [Cybersecurity] | 524B / Feb 2026 guidance | [threat model, SBOM, pen test] | [ ] | [ ] |
| [Human factors] | Aug 2026 HF guidance | [URRA, validation] | [ ] | [ ] |
| [AI evaluation] | PCCP/AI guidance | [model card, bias/drift tests] | [ ] | [ ] |
| [Labeling] | QVO special controls | [IFU, warnings, clinician summary] | [ ] | [ ] |

## 4. HIPAA and privacy analysis

### 4.1 Status

| Question | Answer | Source |
|---|---|---|
| Covered entity? | [yes/no/uncertain] | [S7] |
| Business associate? | [yes/no/uncertain] | [S7] |
| Outside HIPAA? | [yes/no/uncertain] | [S7] |
| FTC HBNR applies? | [yes/no/uncertain] | [S8] |
| State law overlay? | [list] | [S9] |

**Reasoning:** [3–6 sentences. Address the billing/claim flow and the
covered-entity contracts.]

### 4.2 PHI data map

| Data | Source | Storage | Recipients | BAA? | Retention | Risk |
|---|---|---|---|---|---|---|
| [sleep diary] | [patient] | [cloud] | [clinician, analytics] | [ ] | [ ] | [ ] |
| [PHQ-9] | [patient] | [ ] | [ ] | [ ] | [ ] | [ ] |
| [audio] | [device] | [ ] | [ ] | [ ] | [ ] | [ ] |
| [LLM prompt] | [app] | [ ] | [vendor] | [ ] | [ ] | [ ] |

### 4.3 Controls

| Control | Status | Evidence |
|---|---|---|
| Risk analysis | [ ] | [ ] |
| BAA inventory | [ ] | [ ] |
| Encryption at rest/in transit | [ ] | [ ] |
| MFA / least privilege | [ ] | [ ] |
| Audit logging | [ ] | [ ] |
| Backup/restore test | [ ] | [ ] |
| Incident response / breach template | [ ] | [ ] |
| Training | [ ] | [ ] |
| AI vendor review | [ ] | [ ] |
| State-law matrix | [ ] | [ ] |

### 4.4 HIPAA conclusion

[HIPAA applies / does not apply / uncertain. If uncertain, state the fact that
would resolve it and the conservative posture to take meanwhile.]

## 5. AI/ML analysis (if applicable)

| Question | Answer | Source |
|---|---|---|
| What does the AI do? | [personalize content / triage / generate advice / image] | [S10] |
| Is it a device function? | [yes/no/uncertain] | [S10] |
| Does it change the intended use? | [yes/no] | [S10] |
| Planned changes? | [none / PCCP / new submission] | [S10] |
| GenAI/LLM? | [yes/no] | [S11] |
| Human oversight? | [describe] | [S12] |
| Evaluation plan? | [accuracy, bias, drift, safety] | [S12] |

**AI conclusion:** [one paragraph. If GenAI, note that the Aug 2026 discussion
paper is not guidance.]

## 6. 90-day roadmap

| Week | Action | Output | Owner |
|---|---|---|---|
| 1–2 | Lock intended use and claims | `intended-use.md` | [ ] |
| 2–4 | Predicate deep dive + Q-Sub decision | Predicate memo | [ ] |
| 4–6 | Clinical evidence plan | Protocol synopsis | [ ] |
| 4–8 | Software/cyber/HF gap assessment | Gap register | [ ] |
| 6–10 | HIPAA risk analysis + BAA inventory | Risk analysis | [ ] |
| 8–12 | Pre-submission meeting package (if needed) | Q-Sub | [ ] |

## 7. Open questions and assumptions

| # | Question / assumption | Why it matters | How to resolve |
|---|---|---|---|
| 1 | [Do we bill insurance?] | Covered-entity status | [Ask finance/legal] |
| 2 | [Is the app prescription-only?] | QVO fit | [Product decision] |
| 3 | [Will the LLM see PHI?] | BAA/AI | [Architecture review] |
| 4 | [Age range?] | Predicate/labeling | [Clinical plan] |
| 5 | [Any audio/video?] | State biometric/privacy | [Product decision] |

## 8. Sources

| ID | Source | Citation / document | URL | Retrieved | Status |
|---|---|---|---|---|---|
| S1 | FD&C Act | 21 U.S.C. 321(h) | [ ] | [ ] | Binding |
| S2 | FDA guidance | General Wellness (Jan 2026) | [ ] | [ ] | Final guidance |
| S3 | IMDRF | SaMD N12 (2014) | [ ] | [ ] | International |
| S4 | FDA guidance | Mobile Medical Apps (Sep 2022) | [ ] | [ ] | Final guidance |
| S5 | openFDA | QVO classification | [ ] | [ ] | Data |
| S6 | eCFR | 21 CFR 882.5801 | [ ] | [ ] | Binding |
| S7 | eCFR | 45 CFR 160.103 / 164.308 | [ ] | [ ] | Binding |
| S8 | eCFR | 16 CFR 318 | [ ] | [ ] | Binding |
| S9 | State statute | [WA MHMDA / CA CMIA] | [ ] | [ ] | Binding |
| S10 | FDA guidance | AI PCCP (Aug 2025) | [ ] | [ ] | Final guidance |
| S11 | FDA | GenAI discussion paper (Aug 2026) | [ ] | [ ] | Not guidance |
| S12 | FDA guidance | HF (Aug 2026) + HF content (May 2026) | [ ] | [ ] | Final guidance |

## 9. What would change this answer

- [ ] The service starts billing insurance or contracting with a health plan
      (HIPAA status).
- [ ] The product adds a disease claim or a new population (device status).
- [ ] The product becomes non-prescription/DTC (QVO fit).
- [ ] The AI moves from content personalization to clinical advice (device/AI
      status).
- [ ] FDA finalizes the HIPAA Security Rule NPRM or the AI lifecycle guidance.
- [ ] A new predicate is cleared or a guidance is archived.

---

## Writing rules

1. Lead with the decision, not the background.
2. Separate **binding** from **guidance** from **assumption**.
3. Every factual sentence gets a source ID or an explicit "assumption."
4. Quote the operative phrase when the wording matters ("prescription only,"
   "adjunct to clinician supervised outpatient treatment").
5. State the counterargument and why it does not win.
6. If you could not retrieve a source, say so; do not fill the gap from memory.
7. End with the decision needed and the date it is needed.
