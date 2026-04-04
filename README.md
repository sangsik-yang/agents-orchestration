# 계층적 에이전트 오케스트레이션 (Hierarchical Agent Orchestration)

**LangGraph**와 **Google Gemini**를 사용하여 구축된 지능형 멀티 에이전트 시스템입니다. Supervisor-Worker 패턴을 기반으로 복잡한 작업을 자율적으로 분석하고 해결합니다.

## 주요 특징

- **Supervisor-Worker 아키텍처**: 중앙 관리자 에이전트가 상황을 판단하고 가장 적합한 워커에게 구체적인 지시를 내립니다.
- **Google Gemini 기반**: `gemini-2.0-flash` 모델을 사용하여 강력한 추론 성능을 제공합니다.
- **전문 워커 구성**:
    - **Researcher**: 실시간 웹 검색 (DuckDuckGo Search).
    - **SQLQueryer**: 구조화된 데이터 분석 (SQLite, Titanic 데이터셋).
    - **Writer**: 정보의 요약 및 합성.
- **무한 루프 방지**: Supervisor가 워커에게 `instruction`을 명시적으로 전달하여 불필요한 반복 작업을 방지합니다.
- **대화형 루프**: CLI 환경에서 사용자와 연속적으로 대화하며 복합적인 작업을 수행합니다.

## 아키텍처 흐름

사용자 입력 → **Supervisor** (의사결정 및 지시) → **Worker** (작업 수행) → **Supervisor** (검토 및 다음 단계 결정) → **FINISH**

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
    `.env` 파일을 생성하고 Google API 키를 추가합니다:
    ```env
    GOOGLE_API_KEY=your_api_key_here
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

### 테스트 실행
시스템의 안정성을 검증하기 위해 작성된 테스트를 실행할 수 있습니다:
```bash
PYTHONPATH=. uv run pytest
```

## 사용된 주요 기술
- **LangGraph / LangChain**: 복잡한 에이전트 워크플로우 및 LLM 통합 관리.
- **Google Gemini**: 고성능 생성형 AI 모델.
- **Pandas / SQLAlchemy**: 데이터 정제 및 DB 관리.
- **Pytest**: 유닛 및 통합 테스트 프레임워크.
- **uv**: 현대적인 Python 패키지 관리 도구.
