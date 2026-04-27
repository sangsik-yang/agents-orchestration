# 계층적 에이전트 오케스트레이션 (Hierarchical Agent Orchestration)

**LangGraph**와 **OpenRouter API**를 사용하여 구축된 지능형 멀티 에이전트 시스템입니다. Supervisor-Worker 패턴을 기반으로 복잡한 작업을 자율적으로 분석하고 해결합니다. 현재는 대화형 실행과 단발성 smoke test 실행을 모두 지원합니다.

## 주요 특징

- **Supervisor-Worker 아키텍처**: 중앙 관리자 에이전트가 상황을 판단하고 가장 적합한 워커에게 구체적인 지시를 내립니다.
- **공유 메모리 (Shared Scratchpad)**: `AgentState` 내의 `data` 필드를 통해 에이전트 간 정제된 정보를 공유하여 협업 능력을 극대화합니다.
- **실시간 스트리밍 & 시각적 피드백**: CLI 환경에서 에이전트의 현재 작업 상태와 중간 결과물을 직관적으로 보여줍니다.
- **자가 복구 (Self-Correction)**: 작업 중 에러 발생 시 Supervisor가 원인을 분석하여 최대 3회까지 자동 수정 및 재시도를 지시합니다.
- **구조화된 로깅 (Logging & Observability)**: `colorlog`를 통한 단계별 컬러 로깅과 LangSmith 연동을 지원하여 시스템 흐름을 명확하게 파악할 수 있습니다.
- **OpenRouter 기반**: `z-ai/glm-4.5-air:free` 모델을 기본값으로 사용합니다.
- **중앙 설정 모듈**: OpenRouter, 호출 지연, Titanic DB 경로를 `config.py`에서 관리합니다.
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
    OPENROUTER_MODEL=z-ai/glm-4.5-air:free
    # 선택: 기본값은 titanic.db
    TITANIC_DB_PATH=titanic.db
    # 선택: RPM 완화를 위해 LLM 호출 사이에 추가 지연을 넣습니다.
    OPENROUTER_LLM_CALL_DELAY_SECONDS=4
    
    # LangSmith (옵션: 추적 기능을 사용하려면 추가)
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_API_KEY=your_langchain_api_key_here
    ```

### 실행 방법
1.  데이터베이스 초기화 (최초 1회):
    ```bash
    uv run setup_db.py
    ```
2.  에이전트 시스템 실행:
    ```bash
    uv run main.py
    ```
   - 단발성 smoke test:
     ```bash
     uv run main.py --smoke-test
     ```
   - 한 번만 실행할 커스텀 질의:
     ```bash
     uv run main.py --query "Analyze the Titanic dataset."
     ```
   - LLM 호출 사이에 지연 추가:
     ```bash
     uv run main.py --llm-call-delay-seconds 4
     ```
   - OpenRouter 연결 수동 확인:
     ```bash
     uv run python -m scripts.check_openrouter_api
     uv run python -m scripts.check_openrouter_structured_output
     ```

### 현재 검증 상태
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` 기준 `11 passed`
- `uv run main.py --smoke-test`로 비대화형 1회 실행 가능
- `.env`의 `OPENROUTER_API_KEY`를 사용해 OpenRouter API에 연결

## 사용된 주요 기술
- **LangGraph / LangChain**: 복잡한 에이전트 워크플로우 및 LLM 통합 관리.
- **OpenRouter / z-ai/glm-4.5-air:free**: 현재 런타임에서 사용하는 기본 추론 모델.
- **colorlog**: 시각적인 터미널 로그 시스템.
- **SQLAlchemy**: 데이터베이스 관리 및 SQL 분석 엔진.
- **Pytest**: 시스템의 안정성 검증을 위한 테스트 프레임워크.
- **uv**: 현대적이고 빠른 Python 패키지 관리 도구.

## 개발 메모
- Supervisor 노드는 전역 인스턴스 없이 그래프별로 주입됩니다.
- 워커 노드는 입력 `AgentState`를 직접 수정하지 않고, 갱신할 partial state를 반환합니다.
- `TITANIC_DB_PATH`를 사용해 테스트/로컬 DB 경로를 분리할 수 있습니다.
