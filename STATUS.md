# 프로젝트 상태: agents-orchestration

## 현재 상태
본 프로젝트는 LangGraph와 OpenRouter 기반 LLM을 사용하는 계층적 에이전트 오케스트레이션 시스템입니다. 현재는 대화형 실행과 단발성 smoke test 실행을 모두 지원하며, 테스트 기준으로는 안정적으로 동작하는 상태입니다.

### 구현된 기능
- **계층적 그래프 구조**: 중앙 관리자(Supervisor)가 작업을 라우팅하는 Supervisor-Worker 패턴.
- **OpenRouter 통합**: 기본적으로 `openrouter/free` 무료 라우터를 사용하는 추론 경로.
- **지시 기반 라우팅**: Supervisor가 워커에게 명시적인 `instruction`을 전달해 작업 정확도를 높임.
- **공유 메모리**: `AgentState["data"]` 필드를 통해 검색 결과와 SQL 결과를 다음 노드에 전달.
- **실시간 스트리밍 인터페이스**: CLI에서 에이전트의 진행 상황과 최종 응답을 출력.
- **자가 복구 및 에러 핸들링**: 작업 실패 시 에러 메시지를 분석해 최대 3회까지 재시도 및 수정 지시 수행.
- **비대화형 smoke mode**: `uv run main.py --smoke-test`로 입력 없이 한 번만 실행하고 종료.
- **비대화형 실패 감지**: 실행 실패 또는 최종 Writer 응답 누락 시 exit code `1` 반환.
- **DB preflight**: 실행 시작 시 `titanic.db`와 `titanic` 테이블 존재 및 row count 확인.
- **Tracing 제어 옵션**: `--disable-tracing`으로 현재 실행에서 LangSmith tracing 비활성화 가능.
- **구조화된 컬러 로깅**: `colorlog` 기반의 단계별 로그 출력.
- **LangSmith 연동**: `LANGCHAIN_TRACING_V2=true`일 때 추적을 켜도록 구성.
- **Tracing fallback**: 추적 endpoint 연결 실패 시 추적 없이 실행 지속. 새 환경 설정 예시는 추적을 기본 비활성화.
- **OpenRouter content 정규화**: Supervisor가 문자열 또는 리스트 형태의 모델 출력을 JSON 파싱 가능한 텍스트로 정규화.
- **SQLQueryer 에이전트**: SQLite 기반 Titanic 데이터셋을 분석하는 전용 워커.
- **테스트 환경**: `pytest` 기준 24개 테스트 통과. 테스트 실행은 외부 추적 비활성화.

### 최근 검증 결과 (2026-10-15)
- `.venv/bin/python -m pytest -q`: `24 passed`.
- 실제 무료 라우터 호출로 Supervisor → SQLQueryer → Supervisor → Writer → Supervisor → FINISH 성공, exit code `0`.
- 여성 314명 중 233명 생존, 생존율 74.2%. 읽기 전용 SQLite 직접 조회 결과와 일치.
- 기존 기본 모델 `openai/gpt-oss-120b:free`는 실제 API에서 무료 제공 종료 404 반환. 기본값과 환경 설정 예시를 `openrouter/free`로 교체.
- 회귀 테스트: 추적 연결 실패 fallback, 명시적 추적 해제, 최종 응답 누락 실패, 실제 SQLite 도구와 Writer 그래프 실행.
- 외부 API 실행 성공 검증은 Titanic SQL 경로에 한정. Researcher의 실제 웹 검색은 이번 검증에 포함하지 않음.
- 의존성 경고 2건: LangGraph 직렬화 기본값 변경 예고 및 `create_react_agent` 사용 중단 예고.

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
- [x] LangSmith 기본 실행 정책과 시작 시 연결 실패 fallback 추가.
- [ ] 실행 도중 추적 연결이 끊기는 경우의 SDK 재시도 정책 보완.
- [ ] LangGraph 사용 중단 예정 API 마이그레이션.
- [ ] 더 다양한 데이터 소스 및 API 연동 (예: Notion, Slack).
- [ ] 웹 기반 UI (Streamlit 등) 추가.
- [ ] 다중 사용자 세션 관리 및 영속성(Persistence) 강화.

## 환경 요구 사항
- Python >= 3.11
- OPENROUTER_API_KEY (`.env` 파일에 설정)
- `uv` 패키지 매니저 사용 권장.
