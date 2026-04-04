# 계층적 에이전트 오케스트레이션 (Hierarchical Agent Orchestration)

**LangGraph**를 사용하여 구축된 계층적(Supervisor-Worker) 패턴의 멀티 에이전트 시스템입니다. 이 프로젝트는 연구 및 작업을 자율적으로 수행하기 위해 여러 전문 에이전트를 어떻게 조율하는지 보여줍니다.

## 아키텍처

이 시스템은 **계층적 오케스트레이션(Hierarchical Orchestration)** 패턴을 사용합니다:
1.  **Supervisor (관리자)**: 관리자 역할을 하며, 작업을 할당받아 전문 워커(Worker)들에게 라우팅합니다.
2.  **Researcher (연구원)**: DuckDuckGo Search를 사용하여 관련 정보를 찾습니다.
3.  **Writer (작가)**: 조사 내용을 처리하여 명확하고 전문적인 요약본으로 합성합니다.

워크플로우는 순환 구조입니다: Supervisor → Worker → Supervisor. 이를 통해 관리자는 다음 단계로 진행하거나 작업을 종료하기 전에 워커의 결과물을 검토할 수 있습니다.

## 시작하기

### 사전 준비
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (권장) 또는 `pip`

### 설치 방법
1.  저장소 클론:
    ```bash
    git clone https://github.com/sangsik-yang/agents-orchestration.git
    cd agents-orchestration
    ```
2.  의존성 설치:
    ```bash
    uv sync
    # 또는
    pip install -r requirements.txt
    ```
3.  환경 변수 설정:
    `.env` 파일을 생성하고 OpenAI API 키를 추가합니다:
    ```env
    OPENAI_API_KEY=your_api_key_here
    ```

### 사용법
메인 스크립트를 실행하여 오케스트레이션이 작동하는 것을 확인하세요:
```bash
python main.py
```
기본 작업은 2024년 최신 AI 돌파구를 조사하고 요약하는 것입니다.

## 프로젝트 구조
- `main.py`: 그래프 구축 및 실행 로직.
- `state.py`: 공유 상태(State) 정의.
- `agents/`: Supervisor, Researcher, Writer 구현체.
- `STATUS.md`: 현재 개발 상태 및 로드맵.

## 사용된 기술
- **LangGraph**: 복잡한 에이전트 워크플로우 관리.
- **LangChain**: LLM 통합 및 도구 호출.
- **OpenAI GPT-4o**: 에이전트를 구동하는 기본 모델.
- **DuckDuckGo Search**: 실시간 정보 수집.
- **uv**: 현대적인 Python 패키지 관리.
