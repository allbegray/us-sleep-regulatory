---
last_reviewed: 2026-10-23
review_cadence_days: 120
---

# Query pipeline — ask in Korean, search in English, answer in Korean

Official sources (openFDA, eCFR, Federal Register, ClinicalTrials.gov, PubMed)
and most of the local KB are written in English. Translating the question into
English before retrieval gives better recall; translating the answer back gives
usability. The CLI stays deterministic — the agent does the translation.

## Steps

1. **Detect the user's language.** English input skips steps 2–4.
2. **Extract identifiers and never translate them:**
   K / De Novo numbers (`K240929`), product codes (`QZW`), CFR citations
   (`21 CFR 868.2378`), docket numbers (`FDA-2018-D-1774`), URLs, and official
   device/drug names.
3. **Translate the intent into 1–3 English queries.** Use the regulatory term,
   not a literal translation. Example: "위험을 알려주는 기능" →
   "risk assessment", not "risk notification function".
4. **Query in English.**
   - Local: `kb search "sleep apnea risk assessment"`
   - Live: `classify --name "sleep apnea"`, `predicates --product-code QZW`
   - Guidance: `guidance --query "Clinical Decision Support"`
   - CFR: `cfr 45 164.312` (numeric, no translation needed)
   - Literature: `pubmed --term "digital CBT-I insomnia randomized"`
5. **Fallback.** If the English query returns nothing, retry with the user's
   original terms. The KB tokenizer is Unicode-aware and strips Korean
   particles.
6. **Synthesize in the user's language.** Keep official titles, CFR citations,
   status labels, and verbatim quotes in English. Gloss a term on first use.
7. **Record the English queries** in the retrieval trail, e.g.
   `검색어(영어): "sleep apnea risk assessment", "QZW predicate"`.

## Example

**User:** "웨어러블로 수면무호흡 위험을 알려주는 기능이 FDA 허가 대상이야?"

**English queries actually run:**

```text
kb search "sleep apnea risk assessment wearable"
classify --name "sleep apnea"
predicates --product-code QZW
```

**Answer shape (Korean):**

> 이 기능은 SaMD(의료기기 소프트웨어)입니다. product code는 QZW이고, 510(k)
> 허가 대상입니다. 가장 가까운 predicate는 Apple `K240929`와 Samsung
> `K261011`입니다.

`--lang ko` is used on the CLI to localize the table headers and provenance
badge. It does **not** translate the query — that is step 3.

## Korean → English term map

| Korean | English retrieval term |
|---|---|
| 의료기기 | medical device |
| 의료기기 소프트웨어 | software as a medical device / SaMD |
| 체외진단 | in vitro diagnostic / IVD |
| 적응증 | indication |
| 의도된 사용목적 | intended use |
| 선행 기기 / 비교 제품 | predicate |
| 실질적 동등성 | substantial equivalence |
| 시판 전 허가 | premarket clearance / 510(k) |
| 시판 전 승인 | premarket approval / PMA |
| 신규 분류 | De Novo classification |
| 사전 상담 | Q-Submission / pre-submission |
| 분류 문의 | 513(g) request |
| 일반 웰니스 | general wellness |
| 임상 의사결정 지원 | clinical decision support / CDS |
| 처방전 필요 | prescription-only |
| 보조 요법 | adjunct therapy |
| 특별 통제 | special controls |
| 품질관리시스템 | quality management system / QMS |
| 설계관리 | design controls |
| 검증·타당성 | verification and validation / V&V |
| 위험관리 | risk management |
| 사이버보안 | cybersecurity |
| 인간공학 / 사용적합성 | human factors / usability |
| 사전 변경관리계획 | predetermined change control plan / PCCP |
| 건강정보 보호 | health information privacy |
| 보호 건강정보 | protected health information / PHI |
| 개인식별정보 | personally identifiable information / PII |
| 비식별화 | de-identification |
| 적용 대상 기관 | covered entity |
| 업무 제휴자 | business associate |
| 업무 제휴 계약 | business associate agreement / BAA |
| 유출 / 침해사고 | breach |
| 위험 분석 | risk analysis |
| 보존 | retention |
| 불면증 | insomnia |
| 만성 불면증 | chronic insomnia |
| 인지행동치료 | cognitive behavioral therapy / CBT-I |
| 수면무호흡 | sleep apnea |
| 폐쇄성 수면무호흡 | obstructive sleep apnea / OSA |
| 수면다원검사 | polysomnography / PSG |
| 무호흡-저호흡 지수 | apnea-hypopnea index / AHI |
| 수면 단계 | sleep staging |
| 웨어러블 | wearable |
| 선별 / 위험 평가 | screening / risk assessment |
| 진단 | diagnosis |
| 치료 | treatment |
| 금기 | contraindication |

## Do / Don't

| Do | Don't |
|---|---|
| `"sleep apnea risk assessment"` | `"sleep apnea suspicion screening"` (literal) |
| Keep `QZW`, `K240929`, `868.2378` verbatim | Translate product codes or K numbers |
| Use the official English title for `guidance --query` | Search the registry with a translated title |
| Show the English query in the trail | Hide why a result appeared |
| Retry the Korean query if English returns nothing | Assume the KB has no answer |
