# US Sleep Regulatory

[English](README.md) | **한국어**

미국에서 앱 기반 수면 치료 임상 서비스를 준비할 때 필요한 **FDA 510(k)/De Novo,
SaMD, AI/ML 의료기기 소프트웨어, QMSR, HIPAA/FTC** 의무를 공식 API로 조사하는
Agent Skill입니다.

Codex, Claude Code, OpenCode에서 같은 스킬을 사용할 수 있습니다. 설치는 한 번만
하면 되고, 이후에는 `/us-sleep-regulatory` 또는 `$us-sleep-regulatory`로
호출합니다.

> 리서치 도구 안내이며 법률 자문이 아닙니다. 510(k)/De Novo 제출, 새로운
> intended use, 유출 대응, 다주 출시 전에는 최신 공식 문서와 regulatory counsel을
> 함께 확인하세요.

## 왜 이 스킬을 써야 하나

수면 치료 앱의 규제 질문은 세 가지가 동시에 얽혀 있습니다.

1. 이 앱이 FDA 의료기기인가? (웰니스 vs 510(k) vs De Novo)
2. 어떤 product code/predicate가 맞고, 어떤 evidence가 필요한가? (QVO/QMZ/LEL)
3. 임상 서비스와 데이터가 HIPAA/FTC/주법상 어떤 의무를 지는가?

이 스킬은 세 질문을 같은 출처 기준으로 한 번에 정리합니다.

| 장점 | 실제로 무엇이 달라지나 |
|---|---|
| **공식 출처 기반** | openFDA, eCFR, Federal Register, ClinicalTrials.gov, PubMed를 직접 조회합니다. 블로그·기억·환각에 의존하지 않습니다. |
| **인용·감사 추적** | 모든 답에 KB ID, URL, `retrieved_at`, binding/guidance/draft 상태가 붙습니다. 메모를 그대로 보고서에 붙일 수 있습니다. |
| **로컬 우선 속도** | 50+개 seed 문서를 SQLite+FTS5에 색인합니다. 매 프롬프트마다 API를 호출하지 않고, `kb refresh`할 때만 최신화합니다. |
| **수면 도메인 특화** | QVO/QMZ/LEL, Somryst/Sleepio/NightWare, CBT-I endpoint, QMSR, AI/PCCP, HIPAA를 한 흐름으로 봅니다. |
| **두 트랙 동시 분석** | FDA 510(k)와 HIPAA를 분리합니다. “510(k)를 받았으니 HIPAA도 된다”는 흔한 오해를 막습니다. |
| **DTC/처방 함정 경고** | QVO의 prescription-only·adjunct 요건과 DTC 모델 충돌을 퍼널을 만들기 전에 플래그합니다. |
| **반복 가능한 산출물** | `snapshot`, `kb note`, `memo-template`으로 날짜별·인용 가능한 조사 결과를 축적합니다. |
| **출력 언어** | 사용자의 언어로 답합니다. 한국어 메모에서도 공식 문서 제목, CFR 인용, 상태 라벨은 영어로 유지합니다. |
| **초심자 모드** | 미국 규제가 처음인 개발자에게는 결론·다음 3단계·쉬운 용어 사전을 먼저 보여줍니다. |
| **세 클라이언트, 세 OS** | Codex, Claude Code, OpenCode / macOS, Linux, Windows 설치를 지원합니다. |

### 이런 사람에게 유용합니다

- **창업자·기획자** — DTC vs 처방, 510(k) vs 웰니스 vs De Novo, 12개월 로드맵
- **규제·품질 담당** — predicate, QVO special controls, QMSR, software/cyber/HF evidence
- **개발·보안 담당** — SRS/SDS/V&V, 524B, SBOM, human factors, AI/PCCP
- **임상·메디컬 어페어** — CBT-I endpoint, safety exclusion, trial design
- **투자·실사 담당** — 규제 경로, evidence gap, 핵심 리스크

### 이 스킬이 하지 않는 것

- 법률 자문이 아니며, 510(k)/De Novo를 대신 제출하지 않습니다.
- QMS 구축, 임상시험 수행, 제출서 작성을 대신하지 않습니다.
- 50개 주의 모든 의료·개인정보 법률을 전수 조사하지 않습니다.
- 최신성이 중요한 가이던스·새 clearance는 `kb refresh` 또는 live 명령으로 확인해야 합니다.

## 사용법

### 도구별 호출 방법

| 도구 | 호출 | 비고 |
|---|---|---|
| **Codex CLI** | `$us-sleep-regulatory` | `/skills`로 목록 확인. `/`는 내장 명령용 |
| **Claude Code** | `/us-sleep-regulatory` | 스킬 이름이 곧 slash command |
| **OpenCode** | `/us-sleep-regulatory` 또는 `@us-sleep-regulatory` | `/`는 설치되는 command wrapper, `@`는 스킬 멘션 |
| **MCP 클라이언트** | `scripts/mcp_server.py`의 10개 tool | 스킬 시스템이 없는 클라이언트용 |
| **CLI** | `py -3 ...\scripts\reg.py` | 터미널에서 직접 실행 |

> Codex의 `/prompts:*` 커스텀 프롬프트는 deprecated입니다. Codex에서는
> `$us-sleep-regulatory`를 쓰세요. Claude Code와 OpenCode는 `/`로 호출합니다.

### 로컬 지식베이스 먼저

스킬은 `references/`, `references/guidance-registry.json`, `knowledge/seed/`를
**SQLite + FTS5**로 색인한 로컬 KB를 함께 설치합니다. 첫 `kb` 명령에서 자동
초기화되며 네트워크가 필요 없습니다.

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
python3 "$REG" kb stats
python3 "$REG" kb search "QVO predicate chronic insomnia"
python3 "$REG" kb get cfr-21-882.5801
```

모든 Markdown 출력은 `live`, `cache`, `local`, `mixed` 중 하나의 provenance
배지로 시작합니다. 네트워크·HTTP 캐시·로컬 KB 중 어디서 왔는지 바로 알 수
있고, JSON 출력은 `_meta.fetch`에 같은 값이 들어갑니다. `--lang ko`(또는
`US_REG_LANG=ko`)를 쓰면 배지와 표 헤더가 한국어로 바뀝니다. 공식 문서 제목과
status 라벨은 영어로 유지됩니다.

Windows:

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
py -3 $REG kb stats
py -3 $REG kb search "QVO predicate chronic insomnia"
py -3 $REG kb get cfr-21-882.5801
```

`kb refresh`는 기본 6개 worker로 병렬 조회합니다(콜드 캐시 기준 26.6s → 13.4s,
2026-10-23 측정). `--jobs 1`은 순차 디버깅용입니다.

API는 다음 경우에만 호출합니다.

- 로컬 KB에 답이 없을 때
- `kb stats` / `kb stale`에서 해당 문서가 오래됐을 때
- 사용자가 최신 데이터를 요청할 때
- 새 가이던스·새 clearance처럼 빠르게 바뀌는 소스를 확인할 때

로컬 KB 갱신:

```bash
python3 "$REG" kb refresh --jobs 6              # CFR, classification, 510(k), FR
python3 "$REG" kb refresh --extended --jobs 6   # + FR search, trials, PubMed
python3 "$REG" kb refresh --summaries --jobs 6  # + 510(k) summary PDF
python3 "$REG" kb refresh --no-cache            # HTTP 캐시 무시, 라이브 조회
```

`kb refresh`는 `--cache-ttl`(기본 24시간, `US_REG_CACHE_TTL`) 안의 HTTP 캐시를
재사용합니다. 연속 실행해도 저렴하고 결과가 같으며, 모든 소스를 다시 받아야
할 때만 `--no-cache`(또는 `--cache-ttl 0`)를 쓰세요.

QVO/QMZ/LEL 외의 product code를 추적하려면:

```bash
python3 "$REG" kb follow add QMF
python3 "$REG" kb follow list
python3 "$REG" kb follow remove QMF
```

추적 중인 코드는 다음 `kb refresh`에서 classification과 510(k) landscape를
함께 갱신하며, KB 메타데이터에 저장되어 `kb init --force` 후에도 유지됩니다.

세션 후 결론을 로컬 KB에 축적:

```bash
python3 "$REG" kb note add "QVO is prescription-only; DTC model is a fit gap." \
  --title "QVO vs DTC" --tags "device,qvo,strategy" \
  --source "https://www.ecfr.gov/current/title-21/section-882.5801"
python3 "$REG" kb export --format md   --out snapshots/knowledge.md
python3 "$REG" kb export --format json --out snapshots/knowledge.json
python3 "$REG" kb export --jsonl       --out snapshots/knowledge.jsonl
```

CFR 섹션과 guidance registry 항목처럼 두 문서가 같은 URL을 공유하면
`kb get`은 id 순서로 첫 문서를 고르고 `_meta.ambiguous`와
`_meta.alternatives`를 함께 반환합니다. `--source-type`이나 정확한 id로
명시하세요.

```bash
python3 "$REG" kb get cfr-21-882.5801 --format md
python3 "$REG" kb get https://www.ecfr.gov/current/title-21/section-882.5801 --source-type guidance
```

| 콘텐츠 | TTL | 갱신 |
|---|---|---|
| CFR | 90일 | `kb refresh` |
| classification / 510(k) | 30일 | `kb refresh` |
| guidance registry | 30일 | `kb refresh` |
| Federal Register | 30일 | `kb refresh` |
| trials / PubMed | 30일 | `kb refresh --extended` |
| 510(k) summary | 90일 | `kb refresh --summaries` |

> 한국어 질문은 에이전트가 **영어 검색어로 바꿔 조회한 뒤**, 결과를 다시
> 한국어로 풀어 씁니다. K 번호, product code, CFR 인용은 번역하지 않습니다.
> 자세한 규칙은 `references/query-pipeline.md`를 참고하세요.

### Codex CLI

1. Codex를 재시작합니다.
2. `/skills`로 설치된 스킬을 확인합니다.
3. `$us-sleep-regulatory`로 호출하거나 `$`를 입력해 목록에서 선택합니다.

```text
$us-sleep-regulatory 우리 앱이 CBT-I 디지털 치료제인데 QVO 510(k) predicate와
evidence gap을 정리해줘. DTC 모델이라 prescription-only 요건과 충돌하는지도 봐줘.
```

스킬이 보이지 않으면:

```powershell
Test-Path "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\SKILL.md"
```

`True`가 나오면 Codex를 완전히 종료했다가 다시 실행하세요. `~/.codex`만 읽는
구버전이라면 `install.ps1 -Target codex-legacy` 또는 `install.sh --target
codex-legacy`를 사용합니다.

### Claude Code

1. Claude Code를 재시작합니다.
2. `/us-sleep-regulatory`로 호출합니다.

```text
/us-sleep-regulatory 우리 서비스가 HIPAA covered entity인지 business associate인지
판단하고, PHI 데이터 맵과 BAA 체크리스트를 만들어줘.
```

스킬이 보이지 않으면:

```powershell
Get-ChildItem "$env:USERPROFILE\.claude\skills\us-sleep-regulatory"
```

**Claude Code 데스크탑:** **Code** 탭(로컬 세션)을 사용하세요. Cowork 탭은
`~/.claude/skills`를 읽지 않습니다. 로컬 세션은 읽습니다. `/` 피커에 스킬이
안 보이면 `/us-sleep-regulatory`를 끝까지 직접 입력하고 Enter를 누르세요.
알려진 데스크탑 피커 회귀이며, 명령은 정상 실행됩니다. 세션이 열린 상태에서
설치했다면 `/reload-skills`를 실행하세요. Cowork/클라우드 세션이면 claude.ai
계정에 스킬을 활성화하거나 Code 탭을 사용하세요.

### OpenCode

1. OpenCode를 재시작합니다.
2. `/us-sleep-regulatory`로 호출하거나 `@us-sleep-regulatory`로 스킬을 멘션합니다.

```text
/us-sleep-regulatory QVO / QMZ / LEL 중 우리 제품에 맞는 product code를 골라줘.
Somryst와 Sleepio를 predicate로 비교하고, QMSR 기준 evidence gap도 정리해줘.
```

`/us-sleep-regulatory`는 설치 시 `~/.config/opencode/commands/`에 추가되는
래퍼입니다. `@` 멘션은 OpenCode의 스킬 호출 문법입니다.

스킬이 보이지 않으면:

```powershell
Test-Path "$env:USERPROFILE\.config\opencode\skills\us-sleep-regulatory\SKILL.md"
Test-Path "$env:USERPROFILE\.config\opencode\commands\us-sleep-regulatory.md"
```

### MCP 클라이언트

스킬 시스템이 없는 클라이언트는 MCP 서버로 같은 도구를 씁니다.

**macOS/Linux:**

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

**Windows:**

```jsonc
{
  "mcp": {
    "servers": {
      "us-sleep-reg": {
        "type": "local",
        "command": [
          "python",
          "C:\\Users\\<you>\\.agents\\skills\\us-sleep-regulatory\\scripts\\mcp_server.py"
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
`regulatory_snapshot`, `kb_search`, `kb_get`, `kb_stats`, `kb_note_add`,
`kb_refresh`, `kb_init`

### CLI

**macOS/Linux:**

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
python3 "$REG" doctor
python3 "$REG" predicates --product-code QVO --format md
python3 "$REG" 510k-get K191716 --fetch-summary --format md
python3 "$REG" snapshot
```

**Windows PowerShell:**

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
py -3 $REG doctor
py -3 $REG predicates --product-code QVO --format md
py -3 $REG 510k-get K191716 --fetch-summary --format md
py -3 $REG snapshot
```

### 좋은 첫 질문

스킬은 결론부터 내리지 않고 다음 10가지를 먼저 확인합니다.

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

## 설치

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all
```

또는 clone:

```bash
git clone https://github.com/allbegray/us-sleep-regulatory.git
cd us-sleep-regulatory
./install.sh
```

### Windows (PowerShell)

Windows에서는 `install.ps1`을 사용합니다. Git Bash나 WSL 없이 동작하며,
심볼릭 링크 대신 필요한 위치에 복사합니다.

**1. 스크립트 다운로드 후 실행 (권장)**

```powershell
Invoke-WebRequest `
  -Uri https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.ps1 `
  -OutFile "$env:TEMP\us-sleep-install.ps1"

powershell -ExecutionPolicy Bypass -File "$env:TEMP\us-sleep-install.ps1" -Target all
```

**2. 한 줄 실행 (기본값 `-Target all`)**

```powershell
irm https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.ps1 | iex
```

`-Force`, `-Uninstall`, `-Target` 같은 옵션이 필요하면 1번처럼 파일로 받아
실행하세요.

**3. clone 후 실행**

```powershell
git clone https://github.com/allbegray/us-sleep-regulatory.git
cd us-sleep-regulatory
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all
```

#### Windows 사전 준비

- **Python 3.9+**: 없으면 `install.ps1`이 python.org에서 **per-user**로
  자동 설치합니다(서명 검증 후 조용히 설치). `-SkipPythonInstall`로 끌 수
  있습니다. 수동 설치도 가능합니다.
- 확인:

  ```powershell
  py -3 --version
  # 또는
  python --version
  ```

- **Execution Policy** 오류가 나면:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1
  ```

  또는 현재 세션에서만 허용:

  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```

- **Git**: clone으로 설치할 때만 필요합니다.
- **Git Bash / WSL**을 쓰는 경우 `install.sh`도 사용할 수 있지만, Windows
  네이티브 환경에서는 `install.ps1`을 권장합니다.

#### Windows 설치 경로

| 클라이언트 | 경로 |
|---|---|
| Codex | `%USERPROFILE%\.agents\skills\us-sleep-regulatory` |
| Claude Code | `%USERPROFILE%\.claude\skills\us-sleep-regulatory` |
| OpenCode | `%USERPROFILE%\.config\opencode\skills\us-sleep-regulatory` |
| OpenCode `/` 커맨드 | `%USERPROFILE%\.config\opencode\commands\us-sleep-regulatory.md` |

`install.ps1`은 위 위치에 각각 복사합니다. Windows에서 디렉토리 심볼릭 링크
권한을 요구하지 않습니다.

### 설치 대상 선택

| `--target` / `-Target` | 실제 설치 위치 | 링크 | 대상 |
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

**macOS/Linux:**

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
cat "$HOME/.agents/skills/us-sleep-regulatory/VERSION"
python3 "$REG" doctor
```

**Windows:**

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
Get-Content "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\VERSION"
py -3 $REG doctor
```

`doctor`가 `7/7 checks passed`를 출력하면 openFDA, eCFR, Federal Register,
ClinicalTrials.gov, PubMed, 510(k) PDF까지 모두 연결된 상태입니다.

## 업데이트

### 최신 버전으로 업데이트 (권장)

**macOS/Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory bash -s -- --target all --force
```

**Windows:**

```powershell
Invoke-WebRequest `
  -Uri https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.ps1 `
  -OutFile "$env:TEMP\us-sleep-install.ps1"

powershell -ExecutionPolicy Bypass -File "$env:TEMP\us-sleep-install.ps1" -Target all -Force
```

### clone에서 업데이트

```bash
cd us-sleep-regulatory
git pull
./install.sh --target all --force
```

Windows:

```powershell
cd us-sleep-regulatory
git pull
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Force
```

### 특정 버전으로 고정

```bash
curl -fsSL https://raw.githubusercontent.com/allbegray/us-sleep-regulatory/main/install.sh \
  | US_SLEEP_REG_REPO=allbegray/us-sleep-regulatory US_SLEEP_REG_VERSION=1.0.0 \
    bash -s -- --target all --force
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:TEMP\us-sleep-install.ps1" `
  -Target all -Force -Version 1.0.0
```

또는 릴리스 tarball/zip을 직접 지정합니다.

```bash
./install.sh \
  --from https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.11.3/us-sleep-regulatory-v1.11.3.tar.gz \
  --target all --force
```

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 `
  -From https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.11.3/us-sleep-regulatory-v1.11.3.zip `
  -Target all -Force
```

### 다운로드 검증

릴리스 아티팩트에는 `SHA256SUMS`가 함께 배포됩니다. `install.sh --sha256`과
`install.ps1 -Sha256`은 압축을 풀기 전에 해시를 검증합니다.

```bash
SHA="$(curl -fsSL https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.11.3/SHA256SUMS | awk '/tar.gz/{print $1}')"
./install.sh \
  --from https://github.com/allbegray/us-sleep-regulatory/releases/download/v1.11.3/us-sleep-regulatory-v1.11.3.tar.gz \
  --target all --sha256 "$SHA"
```

```powershell
$SHA = (Get-Content .\SHA256SUMS | Select-String '\.zip').Line.Split()[0]
powershell -ExecutionPolicy Bypass -File .\install.ps1 `
  -From .\us-sleep-regulatory-v1.11.3.zip -Target all -Sha256 $SHA
```

### 업데이트할 때 보존되는 것

- `snapshots/`는 업데이트 전에 백업했다가 복원합니다. 날짜별 JSON/Markdown
  스냅샷과 그 안에 정리한 메모는 유지됩니다.
- `references/`, `scripts/`, `SKILL.md` 등 스킬 본체 파일은 새 버전으로
  덮어씁니다. 직접 수정한 내용이 있다면 별도 repo나 `snapshots/`에 보관하세요.
- 로컬 KB는 `~/.cache/us-sleep-regulatory/kb.sqlite`에 있어 스킬 디렉터리를
  덮어써도 유지됩니다. 업데이트 후 `kb refresh`로 새 소스를 반영하세요.
- 설치된 스킬의 `VERSION` 파일로 실제 버전을 확인할 수 있습니다.

### 업데이트 후 확인

```bash
REG="$HOME/.agents/skills/us-sleep-regulatory/scripts/reg.py"
cat "$HOME/.agents/skills/us-sleep-regulatory/VERSION"
python3 "$REG" doctor
python3 "$REG" guidance --max-age-days 30 --format md
```

Windows:

```powershell
$REG = "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\scripts\reg.py"
Get-Content "$env:USERPROFILE\.agents\skills\us-sleep-regulatory\VERSION"
py -3 $REG doctor
```

### 삭제

**macOS/Linux:**

```bash
./install.sh --target all --uninstall
```

**Windows:**

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Uninstall
```

`--uninstall`은 스킬만 제거하고 로컬 KB와 HTTP 캐시는 남깁니다. 노트가 포함된
KB까지 지우려면 `--purge --yes`(`-Purge -Yes`)를 추가하세요.

**설치 상태 확인:**

```bash
./install.sh --target all --verify
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Verify
```

실제 디렉토리, 클라이언트 심링크, OpenCode `/` 래퍼, 설치 버전을 확인하고
누락이 있으면 exit 1을 반환합니다.

## 스킬이 하는 일

- **FDA device track**: device vs wellness vs CDS, SaMD, product code,
  predicate, 510(k)/De Novo/PMA, QVO/QMZ/LEL, QMSR, software/cyber/HF evidence
- **HIPAA/privacy track**: covered entity vs BA, PHI data map, BAA, Security Rule,
  breach notification, FTC HBNR, state law overlay
- **Sleep domain**: CBT-I, ISI/PSQI, trial design, safety, predicate landscape
- **AI/ML**: PCCP, AI lifecycle, GenAI discussion paper, human oversight,
  vendor/BAA analysis
- **Local knowledge base**: `references/`, guidance registry, `knowledge/seed/`를
  SQLite + FTS5로 색인. 기본 조회는 오프라인이고, API는 `kb refresh`에서만 사용
- **Audit trail**: 모든 응답에 source, URL, retrieval date, cache status 포함.
  `snapshot`은 날짜별 JSON + Markdown을 생성

## 저장소 구조

```
.
├── SKILL.md                  # agent workflow / guardrails
├── README.md                 # English
├── README.ko.md              # 한국어
├── install.sh                # macOS / Linux / Git Bash
├── install.ps1               # Windows PowerShell
├── VERSION
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── agents/openai.yaml
├── commands/opencode/        # OpenCode /us-sleep-regulatory wrapper
├── knowledge/seed/           # offline CFR / 510(k) / FR seed
├── references/
├── scripts/reg.py
├── scripts/mcp_server.py
├── snapshots/
├── examples/
├── tests/
│   ├── test_reg.py
│   └── evals/retrieval.json
├── tools/
└── .github/workflows/
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
- [examples/example-memo-dtc-cbti.md](examples/example-memo-dtc-cbti.md) —
  완성된 예시 메모(가상 제품, 실제 출처)
- `knowledge/seed/` — 오프라인 CFR / 510(k) / FR seed 문서

## 버전 정책

`MAJOR.MINOR.PATCH`를 사용합니다.

| 변경 | 버전 |
|---|---|
| 오탈자, 문서, URL 수정 | PATCH |
| 새 소스, 새 가이드, 새 CLI 옵션, 새 클라이언트 지원 | MINOR |
| CLI/설정/디렉토리 구조의 breaking change | MAJOR |

### 릴리스 절차

1. `VERSION`, `install.sh`의 `DEFAULT_VERSION`, `install.ps1`의
   `$DefaultVersion`, `scripts/reg.py`의 `VERSION`을 같은 값으로 올립니다.
2. `CHANGELOG.md`에 변경 내용을 추가합니다.
3. `python3 -m unittest discover -s tests`와 `bash tools/smoke_test.sh --offline`을
   실행합니다.
4. `bash tools/smoke_test.sh`(네트워크)와 `bash tools/package.sh`로 tarball, zip,
   checksum, catalog를 만듭니다.
5. `python3 tools/validate_registry.py --strict`로 registry 항목을 개별 검증하고,
   `python3 tools/check_freshness.py --strict`로 references 검토 날짜를 확인합니다.
6. commit 후 `vX.Y.Z` 태그를 push합니다.
7. GitHub Actions가 Linux/Windows 테스트 후 Release와 Pages catalog를 배포합니다.

### 사용자 업데이트

- 최신 버전: 설치 때와 같은 명령을 `-Force`/`--force`로 다시 실행
- 버전 고정: `US_SLEEP_REG_VERSION=X.Y.Z` 또는 `-Version X.Y.Z`
- clone: `git pull` 후 `--force`/`-Force`
- 확인: `cat .../VERSION`, `reg.py doctor`

## 검증

```bash
python3 -m unittest discover -s tests -v   # 오프라인, 네트워크 불필요
python3 tools/eval_retrieval.py            # 28개 질문 -> 기대 문서 id
python3 tools/check_freshness.py           # references 검토 날짜
bash tools/smoke_test.sh --offline         # 문법, 버전, 레지스트리, KB, eval, MCP, 설치
bash tools/smoke_test.sh                   # + 7개 공식 소스 연결 확인
```

`--offline`은 PR/CI용 모드입니다. `doctor`와 라이브 refresh를 건너뛰므로
FDA 엔드포인트 장애가 머지를 막지 않습니다. 릴리스 워크플로는 네트워크
smoke 테스트와 `windows-latest`의 `install.ps1`까지 실행합니다. 주 1회
`source-canary` 워크플로가 네트워크 스위트와 strict registry·references
검사를 돌리고, 실패 시 이슈를 엽니다.

검사 항목:

- Python 문법
- guidance registry 구조·상태 어휘·bulk verification 경고
- 검색 eval 15문항 (기대 문서 top-k 노출)
- openFDA, eCFR, Federal Register, ClinicalTrials.gov, PubMed, 510(k) PDF (네트워크 모드)
- MCP `initialize` + `tools/list` (16 tools)
- Codex/Claude/OpenCode 설치·삭제 (macOS/Linux)
- Windows `install.ps1` 설치·삭제 (GitHub Actions `windows-latest`)
- `VERSION` / 기본 버전 일치 (VERSION, install.sh, install.ps1, reg.py)

## 라이선스

MIT. FDA, HHS 또는 정부 기관과 제휴하지 않았습니다.
