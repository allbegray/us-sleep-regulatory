---
last_reviewed: 2026-10-23
review_cadence_days: 120
---

# Output language — Korean users

The skill mirrors the user's language. A Korean question gets a Korean memo,
Korean headings, and Korean explanations — without translating the legal
record.

## What stays in English

Keep these exactly as published, even in a Korean memo:

- official document titles (e.g. "Clinical Decision Support Software")
- CFR citations (`21 CFR 882.5801`, `45 CFR 164.308`)
- K / De Novo numbers (`K191716`, `DEN200033`)
- product codes (`QVO`, `QMZ`, `LEL`)
- status labels (`Binding`, `Final guidance`, `Draft`, `Proposed`, `Data`,
  `Assumption`)
- verbatim quoted regulatory text

Add a Korean gloss on first use, then use the English term:

> QVO는 **prescription-only(처방전 필요)**이며, **adjunct to clinician-supervised
> outpatient treatment(임상의 감독 하 외래 치료의 보조)**로 정의됩니다.

Never translate a binding quote. Quote it in English inside a blockquote or code
block, then explain it in Korean.

## Korean heading map

| Template heading | Korean |
|---|---|
| Executive summary | 요약 |
| Product and intended use | 제품과 의도된 사용목적 |
| FDA device analysis | FDA 기기 분석 |
| Is it a device? | 기기인가? |
| Classification | 분류 |
| Predicate table | Predicate 비교 |
| Pathway recommendation | Pathway 권고 |
| Evidence gaps | Evidence gap |
| HIPAA and privacy | HIPAA/프라이버시 |
| AI/ML analysis | AI/ML 분석 |
| 90-day roadmap | 90일 로드맵 |
| Open questions | 미해결 질문 |
| Sources | 출처 |
| What would change this answer | 이 답을 바꿀 사실 |

## Term glossary

| English | Korean | Note |
|---|---|---|
| intended use | 의도된 사용목적 | 적응증(indication)과 구분 |
| indication | 적응증 | |
| predicate | predicate / 선행 허가 기기 | 번역보다 원어를 유지 |
| substantial equivalence | 실질적 동등성 | |
| 510(k) clearance | 510(k) 허가 | "cleared"이지 "approved"가 아님 |
| De Novo | De Novo 분류 | |
| PMA | 시판 전 승인 | |
| prescription-only | 처방전 필요 | |
| adjunct | 보조 요법 | |
| special controls | 특별 통제 | |
| general wellness | 일반 웰니스 | |
| CDS | 임상 의사결정 지원 | |
| SaMD | 의료기기 소프트웨어 | |
| QMSR | 품질관리시스템 규정 | |
| design controls | 설계관리 | |
| cybersecurity | 사이버보안 | |
| human factors | 인간공학 / 사용적합성 | |
| PCCP | 사전 변경관리계획 | |
| HIPAA | HIPAA | 원어 유지 |
| covered entity | 적용 대상 기관 | |
| business associate | 업무 제휴자(BA) | |
| BAA | 업무 제휴 계약 | |
| PHI | 보호 건강정보 | |
| PII | 개인식별정보 | |
| de-identification | 비식별화 | |
| breach | 유출 / 침해사고 | |
| risk analysis | 위험 분석 | |
| retention | 보존 | |
| Safe Harbor | Safe Harbor(안전항) | |
| enforcement discretion | 집행 재량 | 구속력 없음 |
| guidance | 가이던스 | 구속력 없음 |

## Example — Korean executive summary

> ## 요약
>
> - **기기 여부:** 기기입니다. "reduces insomnia severity"는 treatment claim입니다.
> - **Pathway:** 510(k) under QVO. Predicate는 Sleepio(`K233577`)가 가장 근접합니다.
> - **최대 리스크:** DTC 비처방 모델은 QVO의 **prescription-only**·**adjunct**
>   요건과 충돌합니다.
> - **결정 필요:** prescription/adjunct 모델로 갈지, treatment claim을 빼고
>   wellness로 갈지.

## Do / Don't

| Do | Don't |
|---|---|
| "510(k) 허가(cleared)" | "FDA 승인" |
| 원문 제목 유지 + 첫 사용 시 한국어 gloss | 모든 고유명사를 음차 |
| binding quote는 영어 원문 + 한국어 설명 | CFR 문장을 의역해 인용 |
| `2026-10-23` | `2026년 10월 23일` (본문 서술은 가능, 표는 ISO) |
| 사용자 언어를 따름 | 한국어 사용자에게 영어 메모를 그대로 반환 |

## Memo file name

Content is Korean, but the file name stays ASCII for portability:
`snapshots/YYYY-MM-DD-<english-slug>-memo.md`.

## CLI output

The agent's memo is the primary response; the CLI is the evidence layer. For a
Korean user, run it with `--lang ko` (or export `US_REG_LANG=ko`):

```bash
python3 "$REG" kb search "QVO" --lang ko --format md
python3 "$REG" cfr 45 164.312 --lang ko --format md
```

That translates the provenance badge (`실시간` / `캐시` / `로컬` / `혼합`) and
table headers. JSON keys, official document titles, source names, and status
labels stay English. If a client opened the skill before an update, restart the
session so it reloads `SKILL.md`.

## Query pipeline

Retrieval happens in English; the answer is written in the user's language.
Translate the question into English search terms, keep identifiers verbatim,
then synthesize in Korean. See `references/query-pipeline.md`.

## Beginner mode

When the user is new to US regulatory, do not lead with citations. Use
`references/beginner-mode.md`: a one-line decision, a plain-language "why", the
next three actions, what they do **not** need to worry about yet, and a short
glossary. The full memo can follow below it.

