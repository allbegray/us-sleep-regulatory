---
last_reviewed: 2026-10-23
review_cadence_days: 120
---

# HIPAA and privacy playbook — app-based sleep clinical service

This is the second track. It is independent of FDA. A product can be an
uncleared device and still be HIPAA-compliant, or a cleared device and still
have a serious HIPAA gap.

> Not legal advice. HIPAA analysis is fact-specific. The binding text is
> 45 CFR Parts 160 and 164 (and 16 CFR Part 318 for the FTC rule). Verify the
> current eCFR text before relying on a section.

## Step 1 — Which regime applies?

Answer these in order. Do not skip to a BAA template.

```
1. Do we provide, bill for, or get paid for health care?
   - Do we submit claims electronically (or use a clearinghouse)?
   - Are we a health plan or clearinghouse?
   -> If yes, we may be a covered entity.

2. Do we create, receive, maintain, or transmit PHI for a covered entity
   (or for a business associate)?
   -> If yes, we may be a business associate.

3. If neither, are we a consumer health app?
   -> FTC Health Breach Notification Rule, FTC Act Section 5,
      state privacy/health-data laws, and contract law may apply.

4. Are we doing research?
   -> Common Rule + FDA IDE/21 CFR 50/56 + HIPAA authorization/waiver.
```

### Covered entity test (45 CFR 160.103)

A **health care provider** is a covered entity if it transmits health
information in electronic form in connection with a transaction covered by
45 CFR Part 162 (e.g., claims, eligibility, remittance). A cash-only,
self-pay practice that never conducts a covered electronic transaction may not
be a covered entity — but it can still be a business associate of one, and
state law still applies.

A **health plan** and a **health care clearinghouse** are covered entities
regardless of size.

**Practical read for this product:**

- If the service employs licensed clinicians, bills insurance/Medicare/Medicaid,
  or contracts with health systems/employers, assume covered-entity or
  business-associate status until counsel says otherwise.
- A pure DTC self-pay app with no covered-entity integration may fall outside
  HIPAA. It does not fall outside the FTC Act, the FTC Health Breach
  Notification Rule, or state health-privacy laws.
- A "platform" that hosts clinician workflows for a provider network is very
  likely a business associate.

### Business associate test (45 CFR 160.103)

A business associate is a person or entity that, on behalf of a covered entity,
creates, receives, maintains, or transmits PHI for a covered entity, including
claims processing, data analysis, utilization review, quality assurance,
billing, benefit management, practice management, and legal/accounting/consulting
services that involve PHI. A subcontractor that handles PHI for a business
associate is also a business associate.

**Your vendor map is part of the analysis.** Cloud hosting, LLM APIs, analytics,
crash reporting, email/SMS, customer support, transcription, and wearable
integrations can each be a business associate or subcontractor.

## Step 2 — PHI data map for a sleep service

PHI is individually identifiable health information transmitted or maintained
in any form or medium by a covered entity or business associate. Sleep data can
be PHI even when it looks like a consumer metric, if it is created or received
by a covered entity/BA in connection with care.

Map every data element and every flow:

| Data | Examples | PHI risk | Notes |
|---|---|---|---|
| Identity | name, DOB, email, phone, address, member ID | High | Direct identifiers |
| Sleep diary | bedtime, wake time, SOL, WASO, TST, naps | High when linked | The core therapeutic input |
| Questionnaire | ISI, PSQI, PHQ-9, GAD-7, Epworth | High | Mental health data |
| Device/wearable | actigraphy, HRV, SpO2, accelerometer | High when linked | Consumer wearable data becomes PHI in a clinical workflow |
| Audio/video | sleep sounds, video, voice | Very high | May capture third parties; biometric/voiceprint laws |
| Chat/LLM | free-text symptoms, suicidal ideation | Very high | Prompt logs, model training, vendor retention |
| Clinician notes | assessment, treatment plan | High | EHR/records rules |
| Billing | claims, CPT, payer, authorization | High | Covered transactions |
| Technical | IP, device ID, advertising ID, cookies | Medium/high | Re-identification risk |
| Aggregates | de-identified counts | Lower | Only if 45 CFR 164.514 is satisfied |

**Minimum necessary:** use, disclose, and request only the minimum PHI needed
for the purpose (45 CFR 164.502(b), 164.514(d)). This applies to analytics,
support, and AI prompts too.

**De-identification:** safe harbor (remove the 18 identifiers) or expert
determination (45 CFR 164.514(b)). "Pseudonymized" is not de-identified.
Hashing an email is not de-identification if the key exists.

## Step 3 — The BAA

A business associate agreement is required before a business associate creates,
receives, maintains, or transmits PHI on your behalf (45 CFR 164.504(e),
164.314(a)). A BAA is not a substitute for security; it is a contract that
allocates obligations.

### BAA checklist

- [ ] Identify the parties, the covered entity, and the services.
- [ ] Describe the permitted uses and disclosures of PHI.
- [ ] Prohibit uses/disclosures other than those permitted by the contract or law.
- [ ] Require appropriate safeguards (including Security Rule compliance).
- [ ] Require breach reporting to the covered entity without unreasonable delay,
      with the identity of affected individuals if known.
- [ ] Require subcontractor BAAs with the same restrictions.
- [ ] Require access, amendment, accounting, and availability obligations as
      applicable.
- [ ] Require return or destruction of PHI at termination, with a certificate.
- [ ] Require cooperation with OCR/DOJ investigations.
- [ ] Address AI/LLM training, retention, subprocessors, and model improvement.
- [ ] Address data location, cross-border transfers, and government access.
- [ ] Address audit rights and security evidence (SOC 2, pen test, risk analysis).

**LLM-specific:** a generic consumer LLM API is not a BAA. If prompts contain
PHI, you need a BAA or a HIPAA-eligible enterprise configuration with no
training on your data, no retention beyond the request, and documented
subprocessors. "We don't train on your data" is not the same as "we are a
business associate."

## Step 4 — Security Rule safeguards

The Security Rule applies to ePHI. It is organized into administrative,
physical, and technical safeguards, plus organizational requirements and
policies/procedures (45 CFR 164.308, 164.310, 164.312, 164.314, 164.316).

### Administrative safeguards (164.308)

- [ ] Security management process: risk analysis, risk management, sanction
      policy, information system activity review
- [ ] Assigned security responsibility (security official)
- [ ] Workforce security: authorization/supervision, clearance, termination
- [ ] Information access management: access authorization, establishment,
      modification, revocation
- [ ] Security awareness and training: reminders, malware protection, log-in
      monitoring, password management
- [ ] Security incident procedures: identify, respond, mitigate, document
- [ ] Contingency plan: data backup, disaster recovery, emergency mode,
      testing, criticality analysis
- [ ] Evaluation: periodic technical and non-technical evaluation
- [ ] BAA and subcontractor management

### Physical safeguards (164.310)

- [ ] Facility access controls (for offices/data centers you control)
- [ ] Workstation use and workstation security
- [ ] Device and media controls: disposal, media re-use, accountability,
      data backup/storage

For a cloud-native company, most physical controls sit with the cloud provider;
you still need to document the shared-responsibility split and your own
workstation/device controls.

### Technical safeguards (164.312)

- [ ] Access control: unique user IDs, emergency access, automatic logoff,
      encryption/decryption
- [ ] Audit controls: record and examine activity
- [ ] Integrity: protect ePHI from improper alteration/destruction
- [ ] Person/entity authentication
- [ ] Transmission security: integrity controls, encryption

**Encryption note:** encryption is "addressable," but the practical safe harbor
for breach notification (45 CFR 164.402) makes encryption at rest and in
transit the default expectation. If you have an unencrypted laptop with sleep
data, you have a breach problem, not an "addressable" debate.

### Organizational and policy requirements (164.314, 164.316)

- [ ] BAA provisions
- [ ] Group health plan requirements (if applicable)
- [ ] Policies and procedures, documented and reviewed
- [ ] Documentation retention (6 years from last effective date)
- [ ] Sanctions for workforce violations

### The 2025 Security Rule NPRM

HHS proposed a significant update on 2025-01-06 (90 FR 898), including asset
inventory, encryption, MFA, contingency planning, and 72-hour restoration
expectations. It is **proposed, not final** as of 2026-10-23. Do not cite it as
binding. Do use it as a design signal: the direction of travel is toward
documented, tested, enterprise-grade controls.

## Step 5 — Breach notification

A breach is the acquisition, access, use, or disclosure of PHI in a manner not
permitted by the Privacy Rule that compromises the security or privacy of the
PHI (45 CFR 164.402). There is a rebuttable presumption of breach unless you
demonstrate a low probability of compromise based on a four-factor risk
assessment:

1. The nature and extent of the PHI involved (identifiers, clinical content).
2. The unauthorized person who used or received the PHI.
3. Whether the PHI was actually acquired or viewed.
4. The extent to which the risk has been mitigated.

### Notification duties

| Who | When | Citation |
|---|---|---|
| Affected individuals | Without unreasonable delay, no later than 60 days after discovery | 45 CFR 164.404 |
| HHS OCR | 60 days after discovery; immediate for 500+ individuals | 45 CFR 164.408 |
| Media | 500+ residents of a state or jurisdiction, without unreasonable delay, no later than 60 days | 45 CFR 164.406 |
| Business associate -> covered entity | Without unreasonable delay, no later than 60 days after discovery | 45 CFR 164.410 |

"Discovery" is when the breach is known or would have been known with
reasonable diligence, not when the investigation ends. Document the risk
assessment, the decision, and the timeline.

**Encryption safe harbor:** if the PHI was encrypted with a technology meeting
the HHS guidance and the key was not compromised, the incident may not be a
breach. Get this in writing from security, not from a vendor's marketing page.

## Step 6 — If HIPAA does not apply: FTC and state law

### FTC Health Breach Notification Rule (16 CFR 318)

The HBNR applies to vendors of personal health records (PHR) and PHR related
entities that are not covered by HIPAA. The FTC's 2024 amendments (89 FR 47028)
clarify that health apps and connected devices can be covered. It requires:

- Notice to affected individuals without unreasonable delay and no later than
  60 days after discovery.
- Notice to the FTC within 60 days if 500+ individuals are affected.
- Notice to the media if 500+ residents of a state or jurisdiction.
- A written policy on breach notification.

The FTC also enforces Section 5 against deceptive health claims and unfair
data practices. A "HIPAA compliant" badge on a DTC app that is not a covered
entity or BA can itself be deceptive.

### State overlay

State law can be stricter and can apply regardless of HIPAA status. Build a
state matrix for the states where you have users, clinicians, or data centers.
Common categories to check:

| State | Law | What to check |
|---|---|---|
| Washington | My Health My Data Act (RCW 19.373) | Consent, sale restrictions, private right of action, geofencing |
| California | CMIA (Civil Code 56) + CCPA/CPRA | Medical information, sensitive personal information, opt-out |
| Illinois | BIPA (740 ILCS 14) | Voiceprints/face geometry; written consent; damages |
| Texas | TDPSA + Texas Medical Records Privacy Act | Sensitive data, consent, sale |
| Nevada | SB 370 | Sale of personal information, opt-out |
| Connecticut | CTDPA | Sensitive data, consent, data protection assessments |
| Colorado | CPA | Sensitive data, universal opt-out, profiling |
| New York | SHIELD Act + NY PHL | Reasonable safeguards, breach notice |

This table is a starting point, not a complete 50-state survey. Also check:

- Telehealth licensure and consent laws in each state where clinicians see
  patients.
- State mental-health confidentiality laws (often stricter than HIPAA).
- State biometric/voiceprint laws if you record audio.
- State consumer-health-data laws (Washington, Nevada, Connecticut) that reach
  apps outside HIPAA.
- Contract terms with employers/health plans (ERISA, ASO arrangements).

## Step 7 — AI, LLMs, and vendors

The regulatory question is not "is the model HIPAA compliant?" It is "does PHI
flow to the model, and what contractual and technical controls surround it?"

### A practical AI data-flow review

1. **Classify the prompt.** Does it contain identifiers, sleep data, symptoms,
   medication, or free-text mental health content? If yes, it is PHI when
   handled by a covered entity/BA.
2. **Classify the vendor.** Is it a business associate? Is there a BAA? Does it
   train on your data? How long does it retain prompts? Where are subprocessors?
3. **Minimize.** Send only the fields needed. Redact identifiers. Prefer
   structured summaries over raw chat logs.
4. **Log deliberately.** Audit logs are required; prompt logs can create a new
   PHI repository with its own retention and access rules.
5. **Human oversight.** A clinician should review AI-generated clinical advice
   before it reaches the patient, unless the function is genuinely
   non-clinical.
6. **Evaluate.** Test for hallucination, bias, drift, prompt injection, and
   unsafe escalation. Document the evaluation.
7. **Contract.** BAA, no-training clause, retention/deletion, breach notice,
   subprocessor list, audit rights, model-change notice.

### De-identification and AI training

- Safe harbor requires removing the 18 identifiers (45 CFR 164.514(b)(2)).
  Sleep timestamps and rare device IDs can re-identify.
- Expert determination requires a documented statistical method and a qualified
  expert.
- "Synthetic data" is not automatically de-identified; membership inference and
  memorization are real risks.
- Do not use patient data to fine-tune a model without a legal basis
  (authorization, waiver, or de-identification).

## Step 8 — Research and clinical trials

If you run a study to support a 510(k) or De Novo:

- **FDA**: IDE requirements (21 CFR 812) may apply; significant-risk device
  studies need an approved IDE. Early feasibility studies have their own path.
- **Common Rule**: IRB review, informed consent, vulnerable populations
  (45 CFR 46).
- **HIPAA**: authorization (45 CFR 164.508) or waiver (164.512(i)); minimum
  necessary; accounting of disclosures.
- **Data security**: the research dataset is a new PHI repository. Give it an
  owner, retention schedule, access list, and deletion plan.
- **ClinicalTrials.gov**: registration and results reporting obligations.
- **Publication**: avoid re-identification in quotes, images, or small cells.

## Step 9 — Clinical service operations (adjacent, but critical)

HIPAA is not the only obligation for a clinical service. Flag these to counsel
and operations:

- Clinician licensure in each state where the patient is located.
- Telehealth consent, prescribing rules, and standard of care.
- Malpractice coverage and clinical supervision.
- Credentialing and payer enrollment.
- Adverse event and complaint handling.
- Crisis escalation (suicidal ideation, parasomnia, severe sleepiness).
- Accessibility (WCAG 2.2 AA), language access, and informed consent.
- Advertising and testimonials (FTC substantiation, HIPAA marketing
  authorization, state testimonial rules).

## Audit-ready evidence folder

Create a folder per year with:

- [ ] Current HIPAA policies and procedures (with version/date/owner)
- [ ] Security risk analysis (dated, scoped, signed)
- [ ] Risk management plan and remediation tracker
- [ ] BAA inventory (vendor, service, PHI, signed date, renewal)
- [ ] Subprocessor list and flow-down BAAs
- [ ] Access control matrix and quarterly access review
- [ ] Encryption/config standards and exceptions
- [ ] Audit log retention and review evidence
- [ ] Training records and phishing test results
- [ ] Contingency plan test results (backup restore, disaster recovery)
- [ ] Incident log and breach risk assessments
- [ ] Vendor security reviews (SOC 2, pen test, questionnaire)
- [ ] AI vendor review and model change log
- [ ] Data retention/deletion evidence
- [ ] Patient rights request log (access, amendment, accounting)
- [ ] Complaint log and CAPA
- [ ] State-law matrix and consent templates

## Red flags

1. "We're HIPAA compliant" without a risk analysis, BAA inventory, or audit
   logs.
2. A consumer LLM API receiving PHI with no BAA.
3. Sleep audio/video recordings stored indefinitely with broad access.
4. Analytics SDKs receiving symptom or sleep data without a BAA or
   de-identification.
5. A DTC app claiming HIPAA compliance while operating outside HIPAA and
   ignoring the FTC HBNR.
6. A "de-identified" dataset that still contains timestamps, device IDs, or
   rare diagnoses.
7. No breach response owner, no 60-day clock, no template.
8. Clinicians using personal email/phones for patient data.
9. A vendor's "HIPAA compliant" badge used as your own evidence.
10. AI-generated clinical advice with no human review and no evaluation file.

## Reusable queries

```bash
# Binding text
python3 scripts/reg.py cfr 45 164.308
python3 scripts/reg.py cfr 45 164.402
python3 scripts/reg.py cfr 16 318

# Rulemaking and guidance
python3 scripts/reg.py fr-search --term '"HIPAA Security Rule"' --agency hhs --since 2024-01-01
python3 scripts/reg.py fr-get 2024-30983
python3 scripts/reg.py guidance --topic hipaa

# Research context
python3 scripts/reg.py pubmed --term "digital CBT-I insomnia randomized" --limit 10
```
