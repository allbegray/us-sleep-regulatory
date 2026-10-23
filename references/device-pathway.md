---
last_reviewed: 2026-10-23
review_cadence_days: 120
---

# Device pathway playbook — app-based sleep therapy

Use this when the question is "do we need FDA clearance, and if so which
pathway?" It is a decision framework, not a legal opinion. The answer turns on
**intended use and claims**, then on **predicate availability**, then on
**evidence**.

## The two tracks (do not merge them)

| Track | Question | Governing sources |
|---|---|---|
| FDA device | Is the software a device, and what marketing authorization does it need? | FD&C Act, 21 CFR, FDA guidance |
| HIPAA / privacy | Is the clinical service a covered entity or business associate, and how is PHI handled? | 45 CFR 160/164, FTC HBNR, state law |

A 510(k) clearance says nothing about HIPAA compliance. A HIPAA-compliant
service can still be selling an uncleared device. Answer both tracks separately.

## One-page decision flow

```
1. Write the intended use and every marketing claim.
2. Does the software meet the device definition (FD&C Act 201(h))?
   - No  -> general wellness / non-device CDS / health lifestyle -> document why.
   - Yes -> continue.
3. Is it SaMD (software performing a medical purpose without being part of
   a hardware device), or software in a device?
4. Find the product code, class, and 21 CFR regulation.
5. Is there a predicate with the same intended use and similar technology?
   - Yes -> 510(k).
   - No  -> De Novo (Class I/II) or PMA (Class III).
6. Build the evidence package for that pathway.
7. Plan postmarket surveillance and change control (including AI/PCCP).
```

## Step 1 — Intended use and claims

The single highest-leverage paragraph in the company. Write it once, then make
every screen, ad, app-store description, clinician script, and investor deck
match it.

**Device-style claims** (these create disease-treatment intended use):

- "treats chronic insomnia" / "treats insomnia disorder"
- "reduces insomnia severity" / "improves ISI scores"
- "replaces sleeping pills" / "alternative to medication"
- "clinically proven to cure insomnia"
- "personalized therapy for your insomnia"

**Wellness-style claims** (lower risk, but still must be truthful):

- "helps you build healthier sleep habits"
- "learn relaxation and wind-down techniques"
- "track your sleep and see patterns"
- "improve your sleep hygiene"

The boundary is not the word "sleep"; it is whether the product is intended to
diagnose, cure, mitigate, prevent, or treat a disease or condition. A product
that claims to treat insomnia is on the device side even if it is "just an app."

**Deliverable:** a one-page `intended-use.md` with:

1. The exact intended-use sentence.
2. The target population (age, diagnosis, severity, exclusions).
3. The clinical setting (prescription? clinician-supervised? self-serve?).
4. The claims matrix (claim -> evidence -> substantiation).
5. The claims you are deliberately **not** making.

## Step 2 — Is it a device?

The FD&C Act definition is broad: an instrument, apparatus, implement, machine,
contrivance, implant, in vitro reagent, or other similar or related article,
including a component, part, or accessory, intended for use in the diagnosis,
cure, mitigation, treatment, or prevention of disease, or intended to affect
the structure or function of the body.

Statutory exclusions and policies that can take software out of device
oversight:

| Path | What it requires | Sleep example | Watch out |
|---|---|---|---|
| General wellness | Intended only for general wellness, not for diagnosis/cure/mitigation/prevention/treatment of a disease; low risk | Sleep tracking, relaxation, sleep-habit education | A claim to treat insomnia defeats it |
| Non-device CDS | Intended for a healthcare professional; enables the professional to independently review the basis; does not analyze a signal from an IVD; meets all four 21st Century Cures criteria | Clinician-facing summary of a patient's sleep diary with transparent rationale | Patient-facing therapy does not qualify |
| EHR / administrative | Health administrative functions, not clinical decision-making | Scheduling, billing, claims | Do not assume; check the function |
| Healthy lifestyle | Maintaining or encouraging a healthy lifestyle, unrelated to disease | "Wind-down" audio, sleep hygiene tips | Disease claims defeat it |

**Key point:** the general wellness policy is an enforcement-discretion policy,
not a statutory safe harbor. It does not bind FDA, and it does not protect a
product that makes disease claims. The January 2026 version is the current one.

**CDS is a trap for sleep apps.** A patient-facing app that says "your insomnia
is severe; start sleep restriction" is not non-device CDS. The CDS exclusion is
for software that supports a clinician's independent judgment, with the basis
transparent. A chatbot that gives clinical advice to a patient is more likely a
device function, not CDS.

## Step 3 — SaMD and the product code

SaMD is software intended for a medical purpose that performs that purpose
without being part of a hardware medical device. A sleep app that treats
insomnia is SaMD. A wearable that measures sleep and a separate app that
interprets it may be a system with both device and non-device functions.

### Sleep-relevant product codes (verified 2026-10-23)

| Code | Classification | Class | Regulation | What it covers | Prescription? |
|---|---|---|---|---|---|
| QVO | Computerized Behavioral Therapy Device For Insomnia | II | 21 CFR 882.5801 | Computerized behavioral therapy for psychiatric disorders; cleared for chronic insomnia | Yes |
| QMZ | Digital Therapy Device To Reduce Sleep Disturbance For Psychiatric Conditions | II | 21 CFR 882.5705 | Sleep disturbance due to psychiatric conditions such as nightmare disorder or PTSD | Yes |
| LEL | Device, Sleep Assessment | II | 21 CFR 882.5050 (mapping is legacy; heading is "Biofeedback device") | Actigraphy and sleep assessment | Varies |
| PLC | Sleep Appliances With Patient Monitoring | II | 21 CFR 872.5570 | Oral appliances with monitoring | Varies |
| QJQ | Cranial Electrotherapy Stimulator To Treat Insomnia And/Or Anxiety | II | 21 CFR 882.5800 | CES devices | Yes |

**Do not pick a code from the name alone.** The product-code title, the CFR
heading, and the cleared predicate's intended use can all differ. QVO is the
closest code for a CBT-I therapeutic, but its regulation is written for
"psychiatric disorders" and is prescription-only. QMZ is narrower
(nightmare/PTSD-related sleep disturbance) and is not a general insomnia code.
LEL is assessment, not treatment.

### The QVO special controls (21 CFR 882.5801)

These are the actual bar for a CBT-I device:

1. **Clinical data** that (i) describe a validated model of behavioral therapy
   for the psychiatric disorder and (ii) validate the model **as implemented by
   the device**.
2. **Software** described in an SRS and SDS, with verification, validation, and
   hazard analysis demonstrating that the device effectively implements the
   behavioral therapy model.
3. **Labeling** with instructions for use and images, compatible devices, a
   warning that the device is not a standalone therapy, a warning that it is
   not a substitute for medication, and a physician-labeling summary of the
   clinical testing.

The QMZ special controls (21 CFR 882.5705) add clinical performance testing for
worsening of the psychiatric condition and for increased disturbed sleep or
sleepiness. If your product touches PTSD or nightmare disorder, expect that
bar.

## Step 4 — Predicate and pathway

### Current QVO clearances (openFDA, 2026-10-23)

| K number | Device | Applicant | Decision | Age | Predicate | Notes |
|---|---|---|---|---|---|---|
| K191716 | Somryst | Pear Therapeutics | 2020-03-23 | 22+ | reSET (DEN160018) | Prescription-only 9-week CBT-I; 6 cores; clinician dashboard |
| K233577 | Sleepio | Big Health | 2024-08-05 | 18+ | Somryst (K191716) | Prescription CBT-I; app + web; adjunct to usual care |

Both are Traditional 510(k)s, substantially equivalent, Class II, QVO. The
Somryst summary states the intended use as a prescription-only digital
therapeutic providing CBT-I to patients 22+ with chronic insomnia. Sleepio's
summary states a prescription device for chronic insomnia/insomnia disorder as
an adjunct to usual care in patients 18+.

### What this means for a new entrant

- **If you match the QVO intended use and technology** (prescription CBT-I,
  clinician-supervised/adjunct, similar software), a 510(k) with Somryst or
  Sleepio as predicate is the natural path.
- **If you are direct-to-consumer and non-prescription**, you do not match the
  QVO regulation's "prescription only" and "adjunct to clinician supervised
  outpatient treatment" language. You need a different intended use (wellness,
  which forfeits treatment claims) or a different regulatory strategy (De Novo
  for an OTC/direct-use device, with much stronger evidence and a new
  classification). Do not assume a 510(k) will be accepted just because the app
  looks like Somryst.
- **If you add an AI/LLM function that changes the treatment model** (e.g., an
  LLM therapist that generates individualized clinical advice), the
  technological characteristics may no longer be substantially equivalent.
  Consider a PCCP for planned changes, or a new submission for unplanned ones.
- **If you have no predicate** (new function, new population, new claim), De
  Novo is the route. A De Novo grants a new classification and creates a
  predicate for future 510(k)s. NightWare (DEN200033, QMZ) is an example of a
  De Novo in the sleep/psychiatric space.

### Pathway comparison

| Pathway | When | Evidence burden | Output |
|---|---|---|---|
| Exempt | Class I/II exempt code, no relevant limitations | QMS + labeling | No premarket clearance; still a device |
| 510(k) | Predicate with same intended use and similar technology | SE comparison + required special controls | Clearance |
| De Novo | No predicate; low-to-moderate risk | Full safety/effectiveness + classification proposal + special controls | New Class I/II classification |
| PMA | Class III / high risk | Clinical investigations, manufacturing, etc. | Approval |
| Wellness / non-device | No disease claims; policy criteria met | Truthful substantiation | No FDA marketing authorization |

## Step 5 — Build the 510(k) package

The exact content depends on the device and the software documentation level.
Use the June 2023 software guidance and the current eSTAR template. A practical
checklist for a CBT-I app:

### Administrative and device description

- [ ] 510(k) cover letter, CDRH Premarket Review Submission Cover Sheet, truth
      and accuracy statement
- [ ] Device description, intended use, indications for use
- [ ] Predicate comparison table (intended use, technology, software, population,
      setting, contraindications, warnings)
- [ ] Classification summary (product code, class, regulation, panel)
- [ ] 510(k) summary or statement (public)
- [ ] Financial certification / disclosure

### Software

- [ ] Software documentation level (Basic vs Enhanced) and rationale
- [ ] Software description, architecture, modules, interfaces, dependencies
- [ ] Software requirements specification (SRS)
- [ ] Software design specification (SDS)
- [ ] Risk management file (ISO 14971) and software hazard analysis
- [ ] Verification and validation, including unit/integration/system testing
- [ ] Traceability from requirements to tests to hazards
- [ ] Off-the-shelf software and cloud/LLM dependencies
- [ ] Configuration management, version control, release process
- [ ] Unresolved anomalies and their risk
- [ ] Cybersecurity: threat model, SBOM, security controls, vulnerability
      monitoring, coordinated disclosure, update/patch plan (section 524B if a
      "cyber device")
- [ ] Human factors / usability engineering: use-related risk analysis,
      critical tasks, validation testing if required, HF submission category
- [ ] Interoperability and data exchange (if any)
- [ ] Privacy by design (HIPAA is separate, but the FDA cyber review will ask
      about data protection)

### Clinical

- [ ] Clinical evidence plan aligned to the QVO special controls
- [ ] Validated behavioral therapy model (CBT-I) and its implementation
- [ ] Trial design: randomized, controlled, appropriate comparator; blinded or
      objective endpoints where feasible
- [ ] Population: chronic insomnia diagnosis, age, exclusions (e.g., untreated
      severe depression, bipolar disorder, parasomnia, pregnancy, shift work)
- [ ] Primary endpoint: ISI change or remission; secondary: sleep diary
      (SOL, WASO, TST, SE), PSQI, depression/anxiety, adherence, safety
- [ ] Follow-up: post-treatment and durable follow-up (6/12 months)
- [ ] Safety: sleep restriction risks, excessive daytime sleepiness, worsening
      depression, driving safety, suicidal ideation, parasomnia
- [ ] Statistical analysis plan, missing data, power, effect size
- [ ] Real-world evidence if used (fit-for-purpose, not a substitute for an RCT
      without justification)

### Labeling

- [ ] Indications for use, contraindications, warnings, precautions
- [ ] Prescription status and clinician-supervision statement
- [ ] Instructions for use with images
- [ ] Compatible devices and minimum OS
- [ ] "Not a standalone therapy" warning
- [ ] "Not a substitute for medication" warning
- [ ] Clinician labeling with clinical testing summary
- [ ] Patient labeling reading level and accessibility
- [ ] Cybersecurity patient/user information

### Quality system

- [ ] QMSR-compliant QMS (21 CFR 820 + ISO 13485:2016)
- [ ] Design controls (ISO 13485 clause 7.3)
- [ ] Risk management (ISO 14971:2019)
- [ ] Software lifecycle (IEC 62304)
- [ ] Usability (IEC 62366-1)
- [ ] Health software (IEC 82304-1, if applicable)
- [ ] Supplier controls for cloud, LLM, analytics, and wearable vendors
- [ ] CAPA, complaints, MDR, recalls, UDI

### QMSR note (important as of 2026)

The QMSR final rule (89 FR 7496) took effect on **2026-02-02**. 21 CFR Part 820
now incorporates **ISO 13485:2016** by reference and is much shorter than the
old QSR. Design controls did not disappear; they live in ISO 13485 clause 7.3
and the incorporated requirements. If your consultant gives you a pre-2026
"21 CFR 820.30" checklist, update it. Technical amendments: 90 FR 55978
(2025-12-04).

## Step 6 — AI/ML and change control

| Situation | Likely path |
|---|---|
| Fixed algorithm, no learning after release | Standard software documentation; no PCCP needed |
| Planned model updates within a defined envelope | PCCP reviewed in the 510(k)/De Novo/PMA |
| Unplanned change to intended use, population, or clinical function | New marketing submission |
| LLM/GenAI that generates free-text clinical advice | High uncertainty; likely device function; expect a new submission and robust runtime governance |
| AI that only personalizes content sequencing within the cleared model | Document as software change; assess whether a new 510(k) is needed under the software-change guidance |

**PCCP essentials** (August 2025 final guidance): describe the planned
modifications, the methodology to develop/validate/implement them, the impact
assessment, and the verification/validation evidence. A PCCP is not a license
to change the intended use or to add a new clinical function.

**GenAI**: the August 2026 FDA discussion paper is not guidance and creates no
requirements. It signals interest in competency-based premarket evaluation,
runtime governance, and postmarket monitoring. Do not cite it as a requirement;
do use it to anticipate questions.

## Step 7 — Postmarket

- Complaint handling, MDR (21 CFR 803), corrections/removals (21 CFR 806)
- Cybersecurity vulnerability monitoring and patch cadence
- UDI and device labeling
- Real-world performance and drift monitoring
- Recall readiness and communication templates
- Change control: software-change guidance + PCCP + QMS
- Advertising and promotion: FDA promotional review, FTC substantiation

## Sleep-specific pitfalls

1. **"Prescription-only" vs direct-to-consumer.** QVO is prescription-only. A
   self-serve DTC app that treats insomnia conflicts with the regulation and
   the predicates. Build the clinician order flow or change the claim set.
2. **"Adjunct" vs standalone.** The regulation and both predicates say adjunct
   to clinician-supervised/usual care and not a standalone therapy. A product
   positioned as a replacement for therapy or medication is misbranded.
3. **Age.** Somryst is 22+, Sleepio is 18+. Your population must be supported by
   evidence and labeling. Do not silently widen to adolescents.
4. **Comorbidities.** Insomnia commonly co-occurs with depression, anxiety, PTSD,
   and substance use. Sleep restriction can worsen some conditions. Exclusions
   and safety monitoring matter.
5. **Sleep restriction is not a wellness tip.** It is a therapeutic intervention
   with real risks (sleepiness, driving, mood). Treat it as a clinical function.
6. **AI personalization is not automatically "just software."** If it changes
   the therapeutic model or the clinical advice, it can change the regulatory
   position.
7. **A predicate's clearance is not your evidence.** You can leverage predicate
   data, but the QVO special controls require validation of your model as
   implemented by your device.
8. **A 510(k) is not a HIPAA certificate.** Separate track, separate evidence.
9. **A draft guidance is not a requirement.** Label it as draft and verify
   whether it was finalized before relying on it.
10. **A guidance page can be archived.** In 2026 the FDA's 2017 SaMD Clinical
    Evaluation page appears to have been archived. Check the status banner, not
    just the URL.

## Reusable queries

```bash
# Landscape
python3 scripts/reg.py predicates --product-code QVO
python3 scripts/reg.py 510k-search --query "Somryst"
python3 scripts/reg.py 510k-search --applicant "Big Health"

# One predicate and its summary
python3 scripts/reg.py 510k-get K191716 --fetch-summary
python3 scripts/reg.py 510k-get K233577 --fetch-summary

# The binding rule
python3 scripts/reg.py cfr 21 882.5801
python3 scripts/reg.py cfr 21 882.5705

# Current guidance status
python3 scripts/reg.py guidance --topic device
python3 scripts/reg.py guidance --query "software"

# AI landscape
python3 scripts/reg.py fr-search --term '"artificial intelligence"' --agency fda --since 2024-01-01
python3 scripts/reg.py guidance --topic ai
```

## Bottom line for an app-based sleep therapy clinical service

- If you **treat chronic insomnia with CBT-I** and want to stay close to the
  existing market, plan for a **QVO 510(k)** with Somryst/Sleepio as predicates,
  a **prescription/clinician-supervised** model, and the QVO special-control
  evidence package.
- If you want **DTC self-serve without a prescription**, either stay in
  **wellness** (no treatment claims) or plan a **De Novo / new classification**
  conversation with FDA. Do not assume the QVO route is available.
- If you add **AI/LLM clinical advice**, plan a **PCCP** for bounded changes and
  a **new submission** for new clinical functions. Treat GenAI as a high-scrutiny
  area.
- Run the **HIPAA track in parallel**; it is independent and often the faster
  path to a real compliance gap.
