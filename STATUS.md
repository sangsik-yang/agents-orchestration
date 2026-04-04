# 프로젝트 상태: agents-orchestration

## 현재 상태
본 프로젝트는 Google Gemini를 기반으로 한 계층적 에이전트 오케스트레이션 시스템의 고도화된 프로토타입입니다.

### 구현된 기능
- **계층적 그래프 구조**: 중앙 관리자(Supervisor)가 작업을 라우팅하는 Supervisor-Worker 패턴.
- **Google Gemini 통합**: OpenAI에서 Google Gemini(`gemini-2.0-flash`)로 LLM 전환 완료.
- **지시 기반 라우팅 (Instruction-based Routing)**: Supervisor가 워커에게 명시적인 `instruction`을 전달하여 무한 루프를 방지하고 작업의 정확도를 높임.
- **SQLQueryer 에이전트**: SQLite 기반 Titanic 데이터셋을 분석하는 전용 워커 추가.
- **대화형 CLI (Interactive CLI)**: 사용자와 실시간으로 대화하며 연속적인 작업을 수행하는 인터페이스 구현.
- **테스트 환경 구축**: `pytest`를 이용한 개별 노드 유닛 테스트 및 전체 그래프 통합 테스트 완료.
- **환경 관리**: `uv` 패키지 매니저를 통한 의존성 관리 및 `.env` 지원.

### 프로젝트 구조
- `main.py`: 대화형 루프 및 LangGraph 워크플로우 실행 엔트리 포인트.
- `setup_db.py`: Titanic 데이터셋 다운로드 및 SQLite DB 생성 스크립트.
- `state.py`: 전역 `AgentState` 정의.
- `agents/`: 전문 에이전트 로직:
  - `supervisor.py`: 작업 지시 및 라우팅 (RouteResponse에 instruction 필드 포함).
  - `researcher.py`: 웹 검색 (DuckDuckGo).
  - `sql_queryer.py`: 구조화된 데이터(SQL) 분석.
  - `writer.py`: 결과 요약 및 합성.
- `tests/`: 유닛 및 통합 테스트 코드.

## 향후 계획 / 다음 단계
- [ ] 더 다양한 데이터 소스 및 API 연동 (예: Notion, Slack).
- [ ] 에이전트 간의 직접적인 데이터 공유 및 메모리 기능 강화.
- [ ] 웹 기반 UI (Streamlit 등) 추가.
- [ ] 실제 서비스 배포를 위한 에러 핸들링 및 로깅 시스템 고도화.

## 환경 요구 사항
- Python >= 3.11
- Google API Key (`.env` 파일에 설정)
- `uv` 패키지 매니저 사용 권장.
