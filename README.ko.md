# US Sleep Regulatory

[English](README.md) | **한국어**

미국에서 앱 기반 수면 치료 임상 서비스를 준비할 때 필요한 **FDA 510(k)/De Novo,
SaMD, AI/ML 의료기기 소프트웨어, QMSR, HIPAA/FTC** 의무를 공식 API로 조사하는
Agent Skill입니다.

Codex, Claude Code, OpenCode에서 같은 스킬을 사용할 수 있습니다. 실제 파일은
`~/.agents/skills/us-sleep-regulatory`에 한 번만 복사하고, Claude Code와
OpenCode는 심볼릭 링크로 연결합니다.

> 리서치 도구 안내이며 법률 자문이 아닙니다. 510(k)/De Novo 제출, 새로운
> intended use, 유출 대응, 다주 출시 전에는 최신 공식 문서와 regulatory counsel을
> 함께 확인하세요.

## 설치

### 한 줄 설치

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all
```

`--target all`은 세 클라이언트를 모두 설정합니다. `--target`을 생략해도 기본값이
`all`입니다.

설치 결과:

```
~/.agents/skills/us-sleep-regulatory           # 실제 파일 (Codex + OpenCode)
~/.claude/skills/us-sleep-regulatory           # symlink
~/.config/opencode/skills/us-sleep-regulatory  # symlink
```

Codex는 `~/.agents/skills`를 사용자 스코프로 읽고, OpenCode는 같은 경로를 global
compatibility 소스로 읽습니다. Claude Code는 `~/.claude/skills`를 읽으며 symlink를
따릅니다. 그래서 사본을 세 벌 만들 필요가 없습니다.

### git clone으로 설치

```bash
git clone https://github.com/allbegray/us-sleep-regulatory.git
cd us-sleep-regulatory
./install.sh
```

### 설치 대상 선택

| `--target` | 실제 설치 위치 | 링크 | 대상 |
|---|---|---|---|
| `all` (기본) | `~/.agents/skills/...` | Claude + OpenCode | 세 클라이언트 모두 |
| `auto` | `~/.agents/skills/...` | 설정된 클라이언트만 | 세 클라이언트 모두 |
| `codex` | `~/.agents/skills/...` | 없음 | Codex |
| `claude` | `~/.claude/skills/...` | 없음 | Claude Code |
| `opencode` | `~/.config/opencode/skills/...` | 없음 | OpenCode |
| `project` | `./.opencode/skills/...` | `./.agents`, `./.claude` | 현재 repo |
| `codex-legacy` | `~/.codex/skills/...` | 없음 | 구버전 Codex |
| `PATH` | 지정한 디렉토리 | 없음 | 커스텀 |

### 설치 확인

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
cat "$HOME/.agents/skills/us-sleep-regulatory/VERSION"
python3 "$REG" doctor
```

`doctor`가 `7/7 checks passed`를 출력하면 openFDA, eCFR, Federal Register,
ClinicalTrials.gov, PubMed, 510(k) PDF까지 모두 연결된 상태입니다.

## 업데이트

스킬은 계속 버전업됩니다. 업데이트도 설치와 같은 명령으로 합니다.

### 최신 버전으로 업데이트 (권장)

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all --force
```

`install.sh`의 `DEFAULT_VERSION`이 최신 릴리스 버전을 가리킵니다. `main`의
설치 스크립트를 다시 받아 실행하면 최신 태그 아카이브를 내려받아 덮어씁니다.

### git clone에서 업데이트

```bash
cd us-sleep-regulatory
git pull
./install.sh --target all --force
```

### 특정 버전으로 고정

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory US_SLEEP_REG_VERSION=1.0.0 \
    bash -s -- --target all --force
```

또는 릴리스 tarball을 직접 지정합니다.

```bash
./install.sh \
  --from https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.1.0/us-sleep-regulatory-v1.1.0.tar.gz \
  --target all --force
```

### 업데이트할 때 보존되는 것

- `snapshots/`는 업데이트 전에 백업했다가 복원합니다. 날짜별 JSON/Markdown
  스냅샷과 그 안에 정리한 메모는 유지됩니다.
- `references/`, `scripts/`, `SKILL.md` 등 스킬 본체 파일은 새 버전으로
  덮어씁니다. 직접 수정한 내용이 있다면 별도 repo나 `snapshots/`에 보관하세요.
- 설치된 스킬의 `VERSION` 파일로 실제 버전을 확인할 수 있습니다.

### 업데이트 후 확인

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
cat "$HOME/.agents/skills/us-sleep-regulatory/VERSION"
python3 "$REG" doctor
python3 "$REG" guidance --max-age-days 30 --format md
```

### 삭제

```bash
./install.sh --target all --uninstall
```

## 설치 후 AI 에이전트에서 사용하기

### Codex CLI

1. Codex를 재시작합니다.
2. `/skills`로 설치된 스킬 목록을 확인합니다.
3. `$us-sleep-regulatory`로 직접 호출하거나, `$`를 입력해 목록에서 선택합니다.

```text
$us-sleep-regulatory 우리 앱이 CBT-I 디지털 치료제인데 QVO 510(k) predicate와
evidence gap을 정리해줘. DTC 모델이라 prescription-only 요건과 충돌하는지도 봐줘.
```

Codex에서 스킬이 보이지 않으면:

```bash
test -f "$HOME/.agents/skills/us-sleep-regulatory/SKILL.md" && echo OK
```

`OK`가 나오면 Codex를 완전히 종료했다가 다시 실행하세요. `~/.codex`만 사용하는
구버전이라면 `--target codex-legacy`로 `~/.codex/skills`에 설치할 수 있습니다.

### Claude Code

1. Claude Code를 재시작합니다.
2. `@us-sleep-regulatory`로 호출합니다.
3. 스킬 설명과 일치하는 질문을 하면 자동으로 선택될 수도 있습니다.

```text
@us-sleep-regulatory 우리 서비스가 HIPAA covered entity인지 business associate인지
판단하고, PHI 데이터 맵과 BAA 체크리스트를 만들어줘.
```

스킬이 보이지 않으면:

```bash
ls -l "$HOME/.claude/skills/us-sleep-regulatory"
```

symlink가 `~/.agents/skills/us-sleep-regulatory`를 가리키는지 확인하고 Claude
Code를 재시작하세요.

### OpenCode

1. OpenCode를 재시작합니다.
2. `@us-sleep-regulatory`로 호출하거나, 그냥 규제 질문을 합니다.
3. 스킬은 설명(description)을 기준으로 자동 노출됩니다.

```text
@us-sleep-regulatory QVO / QMZ / LEL 중 우리 제품에 맞는 product code를 골라줘.
Somryst와 Sleepio를 predicate로 비교하고, QMSR 기준 evidence gap도 정리해줘.
```

OpenCode에서 보이지 않으면:

```bash
ls -l "$HOME/.config/opencode/skills/us-sleep-regulatory"
# 또는
ls -l "$HOME/.agents/skills/us-sleep-regulatory"
```

OpenCode는 `~/.config/opencode/skills`와 `~/.agents/skills`를 모두 읽습니다.
둘 중 하나에 `SKILL.md`가 있으면 됩니다.

### MCP 클라이언트

스킬 시스템이 없는 클라이언트는 MCP 서버로 같은 도구를 쓸 수 있습니다.

```jsonc
{
  "mcp": {
    "servers": {
      "us-sleep-reg": {
        "type": "local",
        "command": [
          "python3",
          "/Users/<you>/.agents/skills/us-sleep-regulatory/scripts/mcp_server.py"
        ],
        "cwd": "."
      }
    }
  }
}
```

제공 도구:

`fda_510k_search`, `fda_510k_get`, `fda_classification`, `fda_predicates`,
`ecfr_get`, `fr_search`, `trials_search`, `pubmed_search`, `guidance_search`,
`regulatory_snapshot`

### CLI로 직접 사용

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"

python3 "$REG" predicates --product-code QVO --format md
python3 "$REG" 510k-get K191716 --fetch-summary --format md
python3 "$REG" cfr 21 882.5801 --format md
python3 "$REG" guidance --topic ai --format md
python3 "$REG" trials --condition insomnia --intervention "cognitive behavioral therapy"
python3 "$REG" snapshot
```

### 좋은 첫 질문

스킬은 바로 결론을 내리지 않고 다음 10가지를 먼저 확인합니다.

1. 정확한 intended use와 마케팅 문구
2. 사용자가 환자인지, 임상가인지, 둘 다인지
3. 처방/임상가 주문 모델인지, DTC self-serve인지
4. 질환, 대상 인구, 연령
5. CBT-I, 수면 제한, 트래킹, 트리아지, AI 코칭, CDS 중 무엇인지
6. AI/LLM이 실제로 무엇을 결정하거나 생성하는지
7. 보험 청구, 의료기관/고용주 계약, cash-pay 여부
8. 수면 일지, ISI/PSQI/PHQ-9, 웨어러블, 오디오/비디오, 채팅, 청구 데이터
9. 현재 단계(아이디어/프로토타입/출시/기존 predicate)
10. 지금 내려야 하는 결정(경로, predicate, evidence plan, HIPAA gap, 투자 실사)

답을 함께 주면 `memo-template.md` 형식으로 다음을 정리합니다.

- FDA device 경로와 predicate 비교
- QVO/QMZ/LEL product code 적합성
- 510(k)/De Novo evidence gap
- HIPAA covered entity/BA 판단과 PHI 데이터 맵
- AI/LLM/PCCP 검토
- 90일 로드맵
- 출처 URL과 `retrieved_at`이 붙은 근거 표

## 스킬이 하는 일

- **FDA device track**: device vs wellness vs CDS, SaMD, product code,
  predicate, 510(k)/De Novo/PMA, QVO/QMZ/LEL, QMSR, software/cyber/HF evidence
- **HIPAA/privacy track**: covered entity vs BA, PHI data map, BAA, Security Rule,
  breach notification, FTC HBNR, state law overlay
- **Sleep domain**: CBT-I, ISI/PSQI, trial design, safety, predicate landscape
- **AI/ML**: PCCP, AI lifecycle, GenAI discussion paper, human oversight,
  vendor/BAA analysis
- **Audit trail**: 모든 응답에 source, URL, retrieval date, cache status 포함.
  `snapshot`은 날짜별 JSON + Markdown을 생성

## 저장소 구조

```
.
├── SKILL.md                  # agent workflow / guardrails
├── README.md                 # English
├── README.ko.md              # 한국어
├── install.sh                # Codex / Claude / OpenCode installer
├── VERSION                   # release version
├── LICENSE                   # MIT
├── CHANGELOG.md              # release history
├── agents/openai.yaml        # Codex UI metadata
├── references/               # source catalog, device, HIPAA, sleep, memo
├── scripts/reg.py            # unified CLI (stdlib only)
├── scripts/mcp_server.py     # optional MCP server
├── snapshots/                # generated JSON + Markdown snapshots
├── tools/                    # packaging, catalog, smoke test
└── .github/workflows/        # release + Pages catalog
```

## 문서

- [SKILL.md](SKILL.md) — 에이전트 워크플로와 가드레일
- [references/source-catalog.md](references/source-catalog.md) — API
  엔드포인트, 쿼리 문법, rate limit, 차단 대응
- [references/device-pathway.md](references/device-pathway.md) — device/SaMD/
  510(k)/De Novo/QMSR/AI
- [references/hipaa-privacy.md](references/hipaa-privacy.md) — covered entity/
  BAA/Security Rule/breach/FTC/state
- [references/sleep-domain.md](references/sleep-domain.md) — CBT-I, endpoint,
  predicate, trial design
- [references/memo-template.md](references/memo-template.md) — 감사 가능한 메모

## 버전 정책

`MAJOR.MINOR.PATCH`를 사용합니다.

| 변경 | 버전 |
|---|---|
| 오탈자, 문서, URL 수정 | PATCH |
| 새 소스, 새 가이드, 새 CLI 옵션, 새 클라이언트 지원 | MINOR |
| CLI/설정/디렉토리 구조의 breaking change | MAJOR |

### 릴리스 절차

1. `VERSION`과 `install.sh`의 `DEFAULT_VERSION`을 같은 값으로 올립니다.
2. `CHANGELOG.md`에 변경 내용을 추가합니다.
3. `bash tools/smoke_test.sh`로 7개 소스, MCP, 설치 3종, 버전 일치를 확인합니다.
4. `bash tools/package.sh`로 tarball, zip, checksum, catalog를 만듭니다.
5. commit 후 `vX.Y.Z` 태그를 push합니다.
6. GitHub Actions가 Release와 Pages catalog를 배포합니다.

### 사용자 업데이트

- 최신 버전: 설치 때와 같은 한 줄 명령을 다시 실행
- 버전 고정: `US_SLEEP_REG_VERSION=X.Y.Z` 지정
- clone: `git pull && ./install.sh --target all --force`
- 확인: `cat .../VERSION`, `python3 .../scripts/reg.py doctor`

## 검증

```bash
bash tools/smoke_test.sh
```

검사 항목:

- Python 문법
- openFDA, eCFR, Federal Register, ClinicalTrials.gov, PubMed, 510(k) PDF
- guidance registry
- MCP `initialize` + `tools/list` (10 tools)
- Codex/Claude/OpenCode 설치·삭제
- `VERSION` / `DEFAULT_VERSION` 일치

## 라이선스

MIT. FDA, HHS 또는 정부 기관과 제휴하지 않았습니다.
