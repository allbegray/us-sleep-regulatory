---
last_reviewed: 2026-10-23
review_cadence_days: 120
---

# Sleep domain reference — clinical, evidence, and product archetypes

This file keeps the regulatory analysis grounded in the actual clinical model.
A sleep app is not a generic "digital health" product; the diagnosis, the
delivery model, and the claims determine the device pathway.

## Clinical taxonomy

| Condition | What it is | Regulatory relevance |
|---|---|---|
| Chronic insomnia disorder | Difficulty initiating/maintaining sleep or early awakening, with daytime impairment, ≥3 nights/week for ≥3 months despite adequate opportunity | The core QVO indication (Somryst, Sleepio) |
| Short-term insomnia | Symptoms <3 months, often triggered by stress/illness | May be a different intended use; check evidence |
| Comorbid insomnia | Insomnia with depression, anxiety, pain, PTSD, etc. | Population/exclusion decisions; QMZ if sleep disturbance is due to a psychiatric condition |
| Obstructive sleep apnea | Breathing pauses, snoring, daytime sleepiness | Different pathway (diagnosis/treatment devices); do not blur with CBT-I |
| Circadian rhythm disorders | Shift work, delayed/advanced sleep phase | Behavioral/light interventions; different evidence |
| Nightmare disorder / PTSD-related sleep disturbance | Frequent nightmares, trauma-related sleep disruption | QMZ (21 CFR 882.5705), not QVO |
| Parasomnias | Sleepwalking, REM behavior disorder, night terrors | Safety exclusions; may require clinical referral |
| Pediatric sleep problems | Behavioral insomnia of childhood, etc. | Separate evidence and labeling; do not assume adult data |

**Diagnosis matters.** "Insomnia" in marketing can mean a symptom, a disorder,
or a comorbidity. The intended-use statement should name the population and the
diagnostic criteria (e.g., ICSD-3/DSM-5-TR chronic insomnia disorder).

## CBT-I: the therapeutic model

Cognitive Behavioral Therapy for Insomnia is the first-line treatment for
chronic insomnia in major guidelines. The core components:

1. **Sleep restriction / sleep consolidation** — reduce time in bed to the
   estimated sleep need, then titrate upward. This is the active ingredient and
   the main safety risk.
2. **Stimulus control** — strengthen the bed-sleep association; leave the bed
   when awake; fixed wake time.
3. **Cognitive restructuring** — challenge dysfunctional beliefs about sleep,
   catastrophizing, and performance anxiety.
4. **Sleep hygiene** — caffeine, alcohol, light, exercise, environment. Necessary
   but not sufficient on its own.
5. **Relaxation training** — breathing, progressive muscle relaxation,
   mindfulness.
6. **Relapse prevention** — plan for setbacks, sleep-wake stabilization.

Digital CBT-I typically delivers these as sequential modules ("cores") over
6–9 weeks, with a daily sleep diary and tailored sleep-window recommendations.
Somryst: 9 weeks, 6 cores, prescription-only, clinician dashboard. Sleepio:
CBT-I for chronic insomnia/insomnia disorder, prescription device, adjunct to
usual care, app + web, clinician dashboard.

### The therapeutic window is a safety issue

Sleep restriction can cause:

- Excessive daytime sleepiness and driving/occupational risk.
- Worsening depression, anxiety, or bipolar symptoms.
- Seizure threshold concerns in susceptible patients.
- Mania/hypomania in bipolar disorder.
- Worsening of parasomnia or REM behavior disorder.
- Problems in pregnancy, shift workers, and patients with unstable medical
  conditions.

A credible CBT-I product has explicit exclusions, screening, monitoring, and
escalation. This is also what a QVO/QMZ clinical evidence package will probe.

## Evidence package

### Core endpoints

| Domain | Instrument | Notes |
|---|---|---|
| Insomnia severity | Insomnia Severity Index (ISI) | 0–28; change and remission (e.g., ISI <10) are common |
| Sleep quality | Pittsburgh Sleep Quality Index (PSQI) | Global score; component scores |
| Sleep diary | SOL, WASO, TST, SE, number of awakenings | Daily, prospective; the therapeutic input |
| Objective sleep | Actigraphy, polysomnography | Actigraphy for patterns; PSG for apnea/parasomnia |
| Daytime function | ESS, FOSQ, work productivity | Especially for safety and payer value |
| Mood | PHQ-9, GAD-7 | Comorbid depression/anxiety; safety monitoring |
| Adherence | Cores completed, sessions, diary completion | Digital therapeutic outcomes depend on engagement |
| Safety | AEs, daytime sleepiness, driving, suicidal ideation, worsening mood | Prespecified and adjudicated |

### Trial design questions FDA will ask

1. What is the validated model of behavioral therapy, and what is the evidence
   for it?
2. Does the software implement that model faithfully? (SRS/SDS, content map,
   clinician review, fidelity testing)
3. What is the comparator? (usual care, waitlist, sleep hygiene education,
   face-to-face CBT-I, sham app)
4. Is the population the labeled population? (age, diagnosis, severity,
   comorbidities, medications)
5. Is the primary endpoint clinically meaningful and prespecified?
6. Is the effect durable? (6/12-month follow-up)
7. Is the safety profile acceptable, including sleep restriction risks?
8. Is adherence adequate, and how is dropout handled?
9. Is the analysis intent-to-treat, with a prespecified missing-data plan?
10. Do subgroup analyses support the labeling (age, sex, severity, comorbidity)?

### Digital-specific evidence issues

- **Blinding** is hard. A sham app or waitlist is common; "treatment as usual"
  can be contaminated.
- **Engagement** is both an outcome and a confounder. Report both.
- **Clinician dashboard** use is part of the intervention; measure it.
- **Software version** must be locked and reported; a moving app invalidates
  the evidence.
- **AI/LLM** functions need a separate evaluation plan (accuracy, safety,
  bias, drift, human oversight).
- **Real-world evidence** can support labeling or postmarket claims, but it
  rarely replaces a well-controlled trial for a new intended use.

### Literature search strings

```
"cognitive behavioral therapy for insomnia" AND randomized
"digital CBT-I" OR "dCBT-I" OR "internet-delivered CBT-I"
insomnia AND "insomnia severity index" AND randomized
"sleep restriction" AND safety AND insomnia
"comorbid insomnia" AND depression AND CBT-I
"nightmare disorder" AND digital AND randomized
"sleep app" AND randomized AND insomnia
```

Use PubMed via the CLI; use ClinicalTrials.gov to see what is recruiting and
what endpoints sponsors are choosing.

## Product archetypes and regulatory posture

| Archetype | Example | Likely posture | Key risk |
|---|---|---|---|
| Wellness sleep tracker | Sleep cycle app, wearable dashboard | General wellness / non-device, if no disease claims | A "treats insomnia" claim flips it |
| Digital CBT-I therapeutic | Somryst, Sleepio | QVO 510(k), prescription, adjunct | Evidence + prescription model |
| Clinician-facing CBT-I support | Dashboard with recommendations | CDS analysis; may be device if it outputs treatment decisions | Four CDS criteria |
| Sleep assessment | Actigraphy, home sleep testing | LEL or apnea pathway | Measurement claims, clinical validation |
| Nightmare/PTSD digital therapy | NightWare | QMZ De Novo/510(k) | Psychiatric safety, worsening symptoms |
| AI sleep coach / chatbot | LLM-generated advice | High uncertainty; likely device if clinical | GenAI, hallucination, escalation |
| Insomnia triage | Screener → referral | Possible CDS/wellness | Diagnosis claims, clinical validity |

## The predicate landscape (QVO)

| Device | K number | Date | Population | Prescription | Predicate | Key lesson |
|---|---|---|---|---|---|---|
| Somryst | K191716 | 2020-03-23 | 22+ chronic insomnia | Yes | reSET (DEN160018) | A De Novo device can be a predicate; a 9-week, 6-core CBT-I program with a clinician dashboard |
| Sleepio | K233577 | 2024-08-05 | 18+ chronic insomnia/insomnia disorder | Yes | Somryst | Same intended use, broader age; adjunct to usual care; app + web |

**What the QVO predicates do not support:**

- A non-prescription, fully self-serve product with disease claims.
- A product positioned as a replacement for medication or as standalone therapy.
- An unvalidated AI model that generates clinical advice.
- Adolescent or pediatric use without data.
- A different psychiatric condition (that may be QMZ or another code).

## QMZ and NightWare

NightWare (DEN200033, 2020-11-06) is a prescription device that uses an Apple
Watch/iPhone to detect and interrupt nightmares in PTSD. It is QMZ, 21 CFR
882.5705. The regulation is specifically about sleep disturbance due to
psychiatric conditions such as nightmare disorder or PTSD — not general
insomnia. If your product treats PTSD-related nightmares, QMZ is the starting
point; if it treats chronic insomnia, QVO is the starting point.

## AI sleep landscape (not a predicate list)

The FDA AI-enabled device list (September 2026) includes sleep-adjacent
authorizations such as:

- SOMNUM (K253390, OLZ)
- Onera SleepMap (K253668, OLZ)
- DeepRESP (K252330/K241960, OLZ)
- Dreem 3S (K242094, OLZ)
- RX-1 Sleep (K253148, MNR)
- SANSA HSAT (K252497/K250882, MNR)
- Oxevision Sleep Device (K233618, LEL)
- EmbraceMini (K252981, LEL)

These are useful for landscape and competitive analysis. They are **not**
automatically predicates for a CBT-I therapeutic. Match intended use and
technology, not the word "sleep."

## Reimbursement and care model (not legal advice)

- CBT-I is guideline-recommended, but coverage is payer-specific. Digital
  therapeutics may be covered under a medical benefit, pharmacy benefit, or
  employer program; check the applicable CMS/local coverage determination and
  commercial policies.
- A prescription-only model needs a licensed clinician to order the device and
  a workflow for supervision, refills, and adverse events.
- A DTC self-pay model avoids some payer constraints but conflicts with the QVO
  prescription-only labeling if you make disease claims.
- Employer/health-plan distribution can trigger HIPAA business-associate
  status, ERISA, and state insurance law.
- "Reimbursable" is a claim; substantiate it or avoid it.

## Sleep data is unusually sensitive

- Sleep audio/video can capture conversations, sexual activity, children, and
  health information. Treat it as high-risk PHI.
- Dream content and psychiatric symptoms are sensitive mental-health data.
- Wearable data can reveal alcohol use, illness, pregnancy, or mood.
- Minors' sleep data triggers COPPA and state child-privacy laws.
- Voice recordings can trigger BIPA and similar biometric laws.
- Advertising IDs and analytics can turn a wellness app into a surveillance
  product; minimize and disclose.

## Claims matrix template

| Claim | Evidence | Regulatory posture | Approved wording |
|---|---|---|---|
| "Improves sleep habits" | Usability/behavior change data | Wellness | Keep it habit-focused |
| "Reduces insomnia severity" | RCT with ISI | Device (treatment) | Only with cleared indication |
| "Treats chronic insomnia" | Pivotal RCT + QVO clearance | Device (prescription) | Only with clearance and prescription |
| "Replaces sleeping pills" | Comparative trial vs medication | Device + high risk | Avoid unless cleared |
| "Clinically proven" | Substantiated RCT | FTC substantiation | Specify the endpoint and population |
| "AI-powered" | Model documentation | FDA software/AI review | Describe the function, not the hype |

## Bottom line

- The clinical model is CBT-I, and the regulatory model is QVO if you treat
  chronic insomnia with a prescription digital therapeutic.
- The evidence bar is not just "CBT-I works"; it is "your software implements a
  validated CBT-I model, and your implementation is safe and effective in your
  labeled population."
- Sleep restriction is the active ingredient and the main safety risk. Treat it
  with clinical seriousness.
- The AI label does not change the clinical evidence bar. It adds software,
  cybersecurity, human-factors, and change-control questions.
