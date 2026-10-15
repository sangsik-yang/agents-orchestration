# 계층적 에이전트 오케스트레이션 (Hierarchical Agent Orchestration)

**LangGraph**와 **OpenRouter**를 사용하여 구축된 지능형 멀티 에이전트 시스템입니다. Supervisor-Worker 패턴을 기반으로 복잡한 작업을 자율적으로 분석하고 해결합니다. 현재는 대화형 실행과 단발성 smoke test 실행을 모두 지원합니다.

## 주요 특징

- **Supervisor-Worker 아키텍처**: 중앙 관리자 에이전트가 상황을 판단하고 가장 적합한 워커에게 구체적인 지시를 내립니다.
- **공유 메모리 (Shared Scratchpad)**: `AgentState` 내의 `data` 필드를 통해 에이전트 간 정제된 정보를 공유하여 협업 능력을 극대화합니다.
- **실시간 스트리밍 & 시각적 피드백**: CLI 환경에서 에이전트의 현재 작업 상태와 중간 결과물을 직관적으로 보여줍니다.
- **자가 복구 (Self-Correction)**: 작업 중 에러 발생 시 Supervisor가 원인을 분석하여 최대 3회까지 자동 수정 및 재시도를 지시합니다.
- **구조화된 로깅 (Logging & Observability)**: `colorlog`를 통한 단계별 컬러 로깅과 LangSmith 연동을 지원하여 시스템 흐름을 명확하게 파악할 수 있습니다.
- **OpenRouter 기반**: 기본적으로 `openrouter/free` 무료 라우터를 활용하여 추론합니다.
- **중앙 설정 모듈**: `config.py`에서 모델, 호출 지연, `TITANIC_DB_PATH`를 관리합니다.
- **전문 워커 구성**:
    - **Researcher**: DuckDuckGo를 이용한 실시간 웹 검색 및 정보 누적.
    - **SQLQueryer**: SQLite 기반 Titanic 데이터셋 분석 및 결과 데이터화.
    - **Writer**: 공유 메모리 데이터를 참조하여 최종 보고서 합성.

## 아키텍처 흐름

사용자 입력 또는 `--smoke-test` → **Supervisor** (의사결정 및 지시) → **Worker** (작업 수행 / 에러 시 자동 피드백) → **Shared Memory** (결과 저장) → **Supervisor** (검토 및 다음 단계 결정) → **Writer** (최종 결과 작성) → **FINISH**

## 시작하기

### 사전 준비
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (권장)

### 설치 및 설정
1.  저장소 클론:
    ```bash
    git clone https://github.com/sangsik-yang/agents-orchestration.git
    cd agents-orchestration
    ```
2.  의존성 설치:
    ```bash
    uv sync
    ```
3.  환경 변수 설정:
    `.env` 파일을 생성하고 OpenRouter API 키를 추가합니다:
    ```env
    OPENROUTER_API_KEY=your_openrouter_api_key_here
    OPENROUTER_MODEL=openrouter/free
    OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

    # Optional: minimum seconds to wait between LLM calls.
    # Useful when the free tier rate limits are too aggressive.
    # Default: 0 (no enforced delay)
    MIN_API_DELAY_SECONDS=1.5
    TITANIC_DB_PATH=titanic.db
    
    # LangSmith (옵션: 추적 기능을 사용하려면 추가)
    LANGCHAIN_TRACING_V2=false
    LANGCHAIN_API_KEY=your_langchain_api_key_here
    ```
   - `OPENROUTER_MODEL`은 기본값으로 `openrouter/free`를 사용합니다. 무료 라우터는 요청에 맞는 무료 모델을 선택하므로 호출마다 모델이 달라질 수 있습니다.
   - 기존 `.env`에 `openai/gpt-oss-120b:free`가 지정되어 있으면 `openrouter/free`로 바꿔 주세요. 2026-10-15 실제 호출에서 기존 무료 모델은 404를 반환했습니다. 유료 모델로 자동 전환하지 않습니다.
   - `MIN_API_DELAY_SECONDS`는 Supervisor, Researcher, Writer, SQLQueryer가 만드는 LLM 호출 사이의 최소 간격을 강제합니다.
   - 값이 비어 있거나 설정되지 않으면 기본값은 `0`입니다.
   - 내부 tool 호출 로그는 그대로 출력되지만, 실제 지연은 LLM 호출에만 적용됩니다.

### 실행 방법
1.  데이터베이스 초기화 (최초 1회):
    ```bash
    uv run setup_db.py
    ```
   - 커스텀 CSV와 DB 경로 지정:
     ```bash
     uv run setup_db.py --csv-url ./data/titanic.csv --db-path ./data/titanic.db --table-name titanic
     ```
   - 커스텀 CSV/DB/table 지정:
     ```bash
     uv run setup_db.py --csv-url ./data/titanic.csv --db-path ./data/titanic.db --table-name titanic
     ```
2.  에이전트 시스템 실행:
    ```bash
    uv run main.py
    ```
   - 단발성 smoke test:
     ```bash
     uv run main.py --smoke-test
     ```
   - 네트워크가 제한된 환경에서 LangSmith 추적만 끄고 smoke test:
     ```bash
     uv run main.py --smoke-test --disable-tracing
     ```
   - 한 번만 실행할 커스텀 질의:
     ```bash
     uv run main.py --query "Analyze the Titanic dataset."
     ```
   - API 호출 간 최소 지연 지정:
     ```bash
     uv run main.py --min-api-delay 1.5
     ```
   - `--smoke-test` 또는 `--query` 같은 비대화형 실행은 작업 실패 시 exit code `1`을 반환합니다.
   - 최종 Writer 응답이 없거나 비어 있는 경우도 실패로 처리합니다.
   - 기존 `--llm-call-delay-seconds`는 `--min-api-delay`의 별칭이며, `MIN_API_DELAY_SECONDS`가 없으면 `OPENROUTER_LLM_CALL_DELAY_SECONDS`도 사용합니다.
   - 수동 API 점검: `uv run python -m scripts.check_openrouter_api` 또는 `uv run python -m scripts.check_openrouter_structured_output`.
   - `TITANIC_DB_PATH`는 실행 전 DB 점검과 SQL 워커 모두에 적용됩니다.

### 추적과 오프라인 실행
- 추적은 기본적으로 꺼져 있습니다. `LANGCHAIN_TRACING_V2=true` 또는 `LANGSMITH_TRACING_V2=true`로 켤 수 있습니다.
- 추적 요청 시 시작 단계에서 endpoint의 `/info`를 2초 timeout으로 확인합니다. 연결에 실패하면 해당 실행은 추적 없이 계속합니다.
- `--disable-tracing`은 환경 변수와 관계없이 현재 실행의 추적을 끕니다. 실행이 끝나면 이전 추적 context로 돌아갑니다.
- 이 fallback은 LangSmith에만 적용됩니다. 실제 LLM 질의와 웹 검색에는 네트워크 연결이 필요합니다. 실행 도중 추적 서비스가 끊기는 경우의 전송 재시도는 SDK 정책을 따릅니다.
- 단위·통합 테스트는 추적을 끄고 실행하므로 `.env`의 설정과 관계없이 외부 추적 요청을 보내지 않습니다.

### 현재 검증 상태
- `.venv/bin/python -m pytest -q` 기준 32개 테스트 통과 (2026-10-15)
- 무료 라우터로 실제 Titanic SQL 분석 → Writer 요약 → FINISH 검증: 여성 314명 중 233명 생존, 생존율 74.2%
- `uv run main.py --smoke-test`로 비대화형 1회 실행 가능
- 실행 시작 시 `titanic.db`와 `titanic` 테이블을 preflight로 확인
- `.env`의 `OPENROUTER_API_KEY`를 사용해 OpenRouter API에 연결
- `MIN_API_DELAY_SECONDS` 또는 `--min-api-delay`로 LLM 호출 간 최소 지연을 설정 가능
- `--disable-tracing`으로 현재 실행에서 LangSmith 추적을 비활성화 가능

## 사용된 주요 기술
- **LangGraph / LangChain**: 복잡한 에이전트 워크플로우 및 LLM 통합 관리.
- **OpenRouter / openrouter/free**: 현재 런타임의 기본 무료 라우터.
- **colorlog**: 시각적인 터미널 로그 시스템.
- **SQLAlchemy**: 데이터베이스 관리 및 SQL 분석 엔진.
- **Pytest**: 시스템의 안정성 검증을 위한 테스트 프레임워크.
- **uv**: 현대적이고 빠른 Python 패키지 관리 도구.

## 개발 메모
- Supervisor 노드는 전역 인스턴스 없이 그래프별로 주입됩니다.
- 워커 노드는 입력 `AgentState`를 직접 수정하지 않고, 갱신할 partial state를 반환합니다.
- `TITANIC_DB_PATH`를 사용해 테스트/로컬 DB 경로를 분리할 수 있습니다.
- `setup_db.py`는 `--csv-url`, `--db-path`, `--table-name` 옵션을 지원하며 실패 시 non-zero exit code를 반환합니다.
