# Example memo — DTC CBT-I app

> **Synthetic example.** SleepBridge is a fictional product and the company facts
> below are invented. The FDA/HIPAA facts (K numbers, CFR text, clearance dates,
> predicate relationships) come from public records and the skill's seed KB.
> Replace every product-specific assumption before reusing this memo. This is a
> worked example of the format and reasoning, not legal advice.

**As of:** 2026-10-23
**Prepared by:** us-sleep-regulatory (example output)
**Scope:** US federal FDA device + HIPAA/FTC privacy; state clinical licensure out of scope
**Status:** Draft for discussion; not legal advice

## 1. Executive summary

- **Device status: device (prescription).** The intended use — treating chronic
  insomnia in adults with a structured CBT-I program — matches 21 CFR
  882.5801 (QVO), which is a **prescription-only** device intended as an
  **adjunct to clinician-supervised outpatient treatment** [S1].
- **Pathway: 510(k) under QVO**, with Somryst (K191716) or Sleepio (K233577) as
  the predicate [S2][S3]. De Novo is not needed while QVO covers the intended
  use.
- **Biggest regulatory risk:** the proposed **DTC, self-serve, no-clinician**
  model is incompatible with QVO's prescription and adjunct-to-care framing.
  This is a product-model decision, not a labeling fix.
- **Biggest evidence gap:** a validated CBT-I model implemented by *this*
  software, plus clinical data in the labeled population — both are QVO special
  controls, not optional [S1].
- **HIPAA posture: outside HIPAA as a pure cash-pay DTC app**, but the FTC
  Health Breach Notification Rule and state health-privacy laws still apply. The
  posture changes to business associate the moment the company contracts with a
  covered entity [S4][S5].
- **Decision needed:** choose (a) prescription/adjunct model with a 510(k), or
  (b) wellness-only model with treatment claims removed. Do not ship the current
  claim set under (b).

## 2. Intake snapshot

| Item | Answer |
|---|---|
| Product | SleepBridge v0.9 (fictional) |
| User | Patient-facing; optional clinician dashboard |
| Setting | DTC subscription, no prescription today |
| Condition | Chronic insomnia in adults 18+ |
| Intervention | 8-week CBT-I: sleep restriction, stimulus control, cognitive restructuring, sleep hygiene, relapse prevention |
| Age | 18+ |
| Claims | "reduces insomnia severity", "improves sleep efficiency", "clinically proven CBT-I" |
| Hardware | Apple Watch / Oura ring import (sleep staging) |
| AI/LLM | LLM coach that answers sleep questions and adjusts the schedule |
| Data | Sleep diary, ISI, PHQ-9, wearable sleep stages, chat transcripts |

**Intended-use statement (draft, prescription model):**

> SleepBridge is a prescription digital therapeutic that delivers a structured
> CBT-I program to adults 18 and older with chronic insomnia, as an adjunct to
> clinician-supervised care. It provides sleep-restriction and stimulus-control
> tools, a daily sleep diary, and a clinician dashboard; it does not replace
> medication or standalone therapy.

**Claims deliberately not made:** "cures insomnia", "replaces sleeping pills",
"standalone treatment", "FDA approved", "HIPAA compliant".

## 3. FDA device analysis

### 3.1 Is it a device?

| Question | Answer | Source |
|---|---|---|
| Meets FD&C Act 201(h)? | Yes — intended to treat a disease/condition | [S1] |
| Statutory exclusion? | No. General wellness does not cover treatment claims; CDS does not cover patient-facing therapy | [S6][S7] |
| SaMD or software in a device? | SaMD (runs on general-purpose hardware) | [S8] |
| Patient- or clinician-facing? | Primarily patient-facing, with a clinician dashboard | [S2][S3] |

**Reasoning.** The product intervenes on chronic insomnia with a therapeutic
program, not with general wellness information. The wellness exclusion is
available only while claims stay unrelated to diagnosis, cure, mitigation,
prevention, or treatment; "reduces insomnia severity" is a treatment claim
[S6]. The CDS exclusion is clinician-facing by design and does not shelter a
patient-facing therapeutic app [S7].

### 3.2 Classification and special controls

| Item | Value | Source |
|---|---|---|
| Product code | QVO | [S9] |
| Class | II | [S9] |
| Regulation | 21 CFR 882.5801 | [S1] |
| Prescription status | **Prescription only** | [S1] |
| Special controls | Validated behavioral-therapy model; validation of the model *as implemented*; SRS/SDS, V&V, hazard analysis; labeling warnings (not standalone, not a medication substitute) | [S1] |

**Discrepancy check.** QVO's regulation heading is "computerized behavioral
therapy device for **psychiatric disorders**", while the device name is
"…for insomnia". The narrower intended use is still QVO; do not infer a broader
psychiatric claim from the heading.

### 3.3 Predicate table

| Predicate | K/De Novo | Date | Intended use | Population | Technology | Fit |
|---|---|---|---|---|---|---|
| Somryst | K191716 | 2020-03-23 | Prescription CBT-I, adjunct, clinician dashboard | 22+ chronic insomnia | App, 6 cores, 9 weeks | Strong: same therapy, same code. Age 22+ vs our 18+ is a labeled-population difference to address. |
| Sleepio | K233577 | 2024-08-05 | Prescription CBT-I as adjunct to usual care | 18+ | App + web, dashboard | Strong: adult population matches; predicate is Somryst. |
| NightWare | DEN200033 | 2020-11-06 | Prescription device that interrupts nightmares (PTSD/nightmare disorder) | Adults with nightmare disorder | Apple Watch + iPhone | **Not a predicate**: different intended use and product code (QMZ, 882.5705). |

**Predicate conclusion:** Sleepio (K233577) is the closest fit on population and
intended use; Somryst (K191716) is the technology ancestor. A 510(k) should
compare the software-implemented CBT-I model, the age range, the wearable
inputs, and the LLM coach against the chosen predicate.

### 3.4 Pathway options

| Option | Fit | Evidence burden | Main risk |
|---|---|---|---|
| Wellness / non-device | Only if treatment claims are removed | Low | Product value proposition collapses; still FTC substantiation |
| 510(k) QVO | **Recommended** if shipping CBT-I | High: validated model, software V&V, clinical data, labeling | Prescription/adjunct model conflicts with DTC |
| De Novo | Not needed for this intended use | Very high | Wasteful while QVO exists |
| PMA | No | — | Not applicable |
| CDS | No | — | Patient-facing therapy, not clinician decision support |

**Recommendation:** 510(k) under QVO, with a prescription/adjunct go-to-market
(or a clinician-supervised DTC model where a licensed provider orders the
program). If the company refuses both, strip treatment claims and re-scope to
wellness — and re-run this analysis before launch.

## 4. Evidence gaps

| Gap | Why it matters | What would close it | Owner | Timing |
|---|---|---|---|---|
| Validated CBT-I model | QVO special control (a)(1)(i) | Published protocol + fidelity mapping to the 8-week program | Clinical | 0–60 days |
| Model validation *as implemented* | QVO special control (a)(1)(ii) | Prospective study or equivalence analysis vs predicate's evidence | Clinical | 3–9 months |
| Software SRS/SDS, V&V, hazard analysis | QVO special control (a)(2) | Design-control package under QMSR/ISO 13485 7.3 | Engineering/QA | 0–90 days |
| Labeling warnings | QVO special control (a)(3) | IFU with "not standalone" and "not a medication substitute" warnings | Regulatory | Before submission |
| Wearable sleep-staging accuracy | New input vs predicate | Analytical validation against polysomnography | Clinical/Data | 2–4 months |
| LLM coach behavior | New function; can generate clinical advice | Model spec, guardrails, human oversight, PCCP if changes are planned | Product/QA | 0–90 days |
| Age 18–21 | Sleepio covers 18+, Somryst 22+ | Justify with predicate choice + clinical data | Clinical | With protocol |

## 5. HIPAA and privacy

**Status: outside HIPAA as a pure cash-pay DTC app** — no covered entity or
business associate relationship on the current facts [S4]. That changes if the
company:

- contracts with providers or health plans (likely business associate), or
- administers an employer health plan (the plan may be a covered entity).

**Data map (current model):**

| Data | Source | Storage | Recipients | BAA | Retention |
|---|---|---|---|---|---|
| Sleep diary, ISI, PHQ-9 | User | App + cloud DB | LLM vendor, analytics | None today | TBD |
| Wearable sleep stages | Apple/Oura | Cloud DB | Analytics | None | TBD |
| Chat transcripts | LLM coach | Vendor + app DB | LLM vendor | None | TBD |
| Subscription/billing | Payment processor | Processor | — | — | Per processor |

**Top gaps:**

1. PHQ-9 and sleep data are sensitive; the FTC Health Breach Notification Rule
   applies to health apps outside HIPAA [S5].
2. LLM vendor handling of chat transcripts: no BAA, unclear retention/training.
3. State overlay: Washington's My Health My Data Act and similar laws add
   consent/consumer-rights duties even without HIPAA.
4. No documented breach-response runbook for a non-HIPAA health app.
5. Wearable data can reveal alcohol use, illness, pregnancy, or mood; minimize
   and disclose.

## 6. AI/LLM analysis

- A coach that **generates or changes clinical advice** (e.g., adjusts sleep
  restriction) is part of the device's therapeutic function, not a neutral
  feature. Document it in the SRS/SDS and the hazard analysis.
- A coach that only answers logistics ("what time is my session?") is lower
  risk; keep the two modes technically separate and label the boundary.
- Planned model updates fit a Predetermined Change Control Plan (PCCP); without
  one, each material change needs its own submission [S10].
- GenAI-specific expectations are still a discussion paper, not a requirement;
  do not cite it as binding [S11].

## 7. 90-day roadmap

| Window | Work |
|---|---|
| Days 0–30 | Freeze the intended use and claims; choose prescription vs wellness; map the CBT-I protocol to a validated model; stand up QMSR/ISO 13485 design controls |
| Days 31–60 | Write SRS/SDS; hazard analysis; human-factors plan; wearable analytical validation protocol; LLM guardrails and evaluation set |
| Days 61–90 | Predicate deep-dive (K233577/K191716 summaries); pre-submission (Q-Sub) meeting package; cybersecurity threat model + SBOM; privacy notice and state-law review |

## 8. Open questions

1. Will a licensed clinician order the program, or is it truly self-serve?
2. Does the LLM coach ever change the sleep-restriction schedule?
3. Which predicate — Sleepio (population fit) or Somryst (technology fit)?
4. Will the company contract with providers, employers, or health plans?
5. Which states are launch states (MHMDA, CMIA, Nevada, others)?

## 9. Sources

| ID | Source | Status | URL | Retrieved |
|---|---|---|---|---|
| S1 | 21 CFR 882.5801 | Binding | https://www.ecfr.gov/current/title-21/section-882.5801 | 2026-10-23 |
| S2 | K191716 Somryst 510(k) | Data | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID=K191716 | 2026-10-23 |
| S3 | K233577 Sleepio 510(k) | Data | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID=K233577 | 2026-10-23 |
| S4 | 45 CFR 164.308 / 164.402 | Binding | https://www.ecfr.gov/current/title-45/section-164.308 | 2026-10-23 |
| S5 | FTC Health Breach Notification Rule (16 CFR 318) | Binding | https://www.federalregister.gov/documents/2024/05/30/2024-10855/health-breach-notification-rule | 2026-10-23 |
| S6 | General Wellness: Policy for Low Risk Devices | Final guidance | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices | 2026-10-23 |
| S7 | Clinical Decision Support Software | Final guidance | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software | 2026-10-23 |
| S8 | IMDRF SaMD N10 — Key Definitions | Final (international) | https://www.imdrf.org/documents/software-medical-device-samd-key-definitions | 2026-10-23 |
| S9 | openFDA classification QVO | Data | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPCD/classification.cfm?ID=QVO | 2026-10-23 |
| S10 | PCCP for AI-enabled device software | Final guidance | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence | 2026-10-23 |
| S11 | Generative AI discussion paper | Discussion paper | https://www.fda.gov/medical-devices/digital-health-center-excellence/considerations-regulation-generative-ai-enabled-medical-devices-discussion-paper-and-request | 2026-10-23 |

## 10. What would change this answer

- **A clinician orders the program and the company contracts with providers** →
  HIPAA business-associate analysis moves to the front; add BAAs and a Security
  Rule gap assessment.
- **Treatment claims are removed** → re-run the wellness analysis; the device
  question may disappear, but FTC substantiation and state privacy remain.
- **The LLM coach only answers logistics** → the AI/PCCP burden drops; document
  the boundary and test it.
- **The company adds nightmare/PTSD features** → QMZ (882.5705) enters the
  analysis; NightWare becomes relevant as a different intended use, not a
  predicate for insomnia.
