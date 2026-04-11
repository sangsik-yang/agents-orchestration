# 프로젝트 상태: agents-orchestration

## 현재 상태
본 프로젝트는 LangGraph와 OpenRouter 기반 LLM을 사용하는 계층적 에이전트 오케스트레이션 시스템입니다. 현재는 대화형 실행과 단발성 smoke test 실행을 모두 지원하며, 테스트 기준으로는 안정적으로 동작하는 상태입니다.

### 구현된 기능
- **계층적 그래프 구조**: 중앙 관리자(Supervisor)가 작업을 라우팅하는 Supervisor-Worker 패턴.
- **OpenRouter 통합**: `stepfun/step-3.5-flash:free` 모델을 사용하는 OpenRouter 기반 추론 경로.
- **지시 기반 라우팅**: Supervisor가 워커에게 명시적인 `instruction`을 전달해 작업 정확도를 높임.
- **공유 메모리**: `AgentState["data"]` 필드를 통해 검색 결과와 SQL 결과를 다음 노드에 전달.
- **실시간 스트리밍 인터페이스**: CLI에서 에이전트의 진행 상황과 최종 응답을 출력.
- **자가 복구 및 에러 핸들링**: 작업 실패 시 에러 메시지를 분석해 최대 3회까지 재시도 및 수정 지시 수행.
- **비대화형 smoke mode**: `uv run main.py --smoke-test`로 입력 없이 한 번만 실행하고 종료.
- **구조화된 컬러 로깅**: `colorlog` 기반의 단계별 로그 출력.
- **LangSmith 연동**: `LANGCHAIN_TRACING_V2=true`일 때 추적을 켜도록 구성.
- **SQLQueryer 에이전트**: SQLite 기반 Titanic 데이터셋을 분석하는 전용 워커.
- **테스트 환경**: `pytest` 기준 9개 테스트가 통과하는 상태.

### 최근 검증 결과
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q`
- 결과: `9 passed`
- `main.py`는 모듈 import와 smoke mode 실행 경로를 기준으로 동작 검증 완료

### 프로젝트 구조
- `main.py`: 실시간 스트리밍 루프 및 LangGraph 워크플로우 실행 엔트리 포인트.
- `logger.py`: 중앙 집중식 컬러 로깅 시스템 모듈.
- `setup_db.py`: Titanic 데이터셋 다운로드 및 SQLite DB 생성 스크립트.
- `state.py`: 전역 `AgentState` 정의 (메시지, 공유 데이터, 에러 상태 포함).
- `agents/`: 전문 에이전트 로직:
  - `supervisor.py`: 작업 지시, 에러 분석 및 라우팅.
  - `researcher.py`: 웹 검색 및 결과 누적.
  - `sql_queryer.py`: 구조화된 데이터(SQL) 분석 및 결과 공유.
  - `writer.py`: 공유 데이터를 우선 참조하여 최종 결과 합성.
- `tests/`: 유닛 및 통합 테스트 코드.

## 향후 계획 / 다음 단계
- [ ] LangSmith 추적 경고가 네트워크 의존적이므로, 오프라인 환경용 가드 추가.
- [ ] 더 다양한 데이터 소스 및 API 연동 (예: Notion, Slack).
- [ ] 웹 기반 UI (Streamlit 등) 추가.
- [ ] 다중 사용자 세션 관리 및 영속성(Persistence) 강화.

## 환경 요구 사항
- Python >= 3.11
- OPENROUTER_API_KEY (`.env` 파일에 설정)
- `uv` 패키지 매니저 사용 권장.
