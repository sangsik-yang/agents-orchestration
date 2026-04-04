# 프로젝트 상태: agents-orchestration

## 현재 상태
본 프로젝트는 LangGraph를 이용한 계층적 에이전트 오케스트레이션 시스템의 기능적 프로토타입입니다.

### 구현된 기능
- **계층적 그래프 구조**: 중앙 관리자가 작업을 라우팅하는 Supervisor-Worker 패턴.
- **Supervisor 에이전트**: 구조화된 출력(`RouteResponse`)을 사용하여 `Researcher`, `Writer`, `SQLQueryer`를 호출하거나 `FINISH`할지 결정합니다.
- **Researcher 에이전트**: 실시간 정보 수집을 위해 DuckDuckGo Search와 통합된 ReAct 기반 에이전트.
- **Writer 에이전트**: 연구 결과를 명확하고 간결한 요약으로 합성하는 데 집중하는 ReAct 기반 에이전트.
- **SQLQueryer 에이전트**: Titanic 데이터셋(SQLite)에 대한 구조화된 데이터 쿼리 및 분석을 수행합니다.
- **환경 관리**: `uv` 및 `python-dotenv` 설정 완료.

### 프로젝트 구조
- `main.py`: LangGraph 워크플로우를 구축하고 실행하는 엔트리 포인트.
- `state.py`: 전역 `AgentState` 정의.
- `agents/`: 전문 에이전트 로직 포함:
  - `supervisor.py`: 작업 라우팅 및 팀 코디네이션.
  - `researcher.py`: 검색 및 데이터 수집 도구.
  - `writer.py`: 콘텐츠 생성 및 요약.

## 향후 계획 / 다음 단계
- [ ] API 실패에 대비한 견고한 에러 핸들링 구현.
- [ ] 더 다양한 전문 워커 추가 (예: 코드 리뷰어, 팩트 체커).
- [ ] 공유 상태 관리 강화 (현재는 `messages`와 `data` 딕셔너리 사용).
- [ ] 에이전트 간 협업을 위한 프롬프트 엔지니어링 개선.
- [ ] 개별 에이전트 노드에 대한 유닛 테스트 추가.

## 환경 요구 사항
- Python >= 3.11
- OpenAI API Key (`.env` 파일에 설정)
- `uv` 또는 `pip install -r requirements.txt`를 통한 의존성 관리.
