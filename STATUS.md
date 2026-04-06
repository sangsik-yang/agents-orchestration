# 프로젝트 상태: agents-orchestration

## 현재 상태
본 프로젝트는 LangGraph와 Google Gemini를 기반으로 한 계층적 에이전트 오케스트레이션 시스템의 고도화된 프로토타입입니다. 최근 로깅, 공유 메모리, 실시간 스트리밍, 자가 복구 기능을 추가하여 안정성과 사용자 경험을 크게 개선하였습니다.

### 구현된 기능
- **계층적 그래프 구조**: 중앙 관리자(Supervisor)가 작업을 라우팅하는 Supervisor-Worker 패턴.
- **OpenRouter 통합**: Google Gemini (`stepfun/step-3.5-flash:free`)를 통한 고성능 추론 엔진 사용.
- **지시 기반 라우팅 (Instruction-based Routing)**: Supervisor가 워커에게 명시적인 `instruction`을 전달하여 작업의 정확도를 높임.
- **공유 메모리 (Shared Scratchpad)**: `AgentState["data"]` 필드를 통해 에이전트 간 정제된 데이터(SQL 결과, 검색 내역 등)를 효율적으로 공유.
- **실시간 스트리밍 인터페이스**: CLI에서 에이전트의 작업 단계별 진행 상황을 시각적으로 보여주는 기능 구현.
- **자가 복구 및 에러 핸들링 (Self-Correction)**: 작업 실패 시 에러 메시지를 분석하여 최대 3회까지 자동 재시도 및 수정 지시 수행.
- **구조화된 컬러 로깅**: `colorlog`를 활용하여 터미널에서 에이전트 실행 흐름을 쉽게 파악할 수 있는 로깅 시스템 구축.
- **LangSmith 연동**: 성능 모니터링 및 디버깅을 위한 추적(Tracing) 인프라 준비 완료.
- **SQLQueryer 에이전트**: SQLite 기반 Titanic 데이터셋을 분석하는 전용 워커.
- **테스트 환경 구축**: `pytest`를 이용한 개별 노드 유닛 테스트 및 전체 그래프 통합 테스트 완료.

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
- [ ] 더 다양한 데이터 소스 및 API 연동 (예: Notion, Slack).
- [ ] 웹 기반 UI (Streamlit 등) 추가.
- [ ] 다중 사용자 세션 관리 및 영속성(Persistence) 강화.
- [ ] 에이전트 간의 동적 도구(Tool) 할당 및 관리 자동화.

## 환경 요구 사항
- Python >= 3.11
- OPENROUTER_API_KEY (`.env` 파일에 설정)
- `uv` 패키지 매니저 사용 권장.
