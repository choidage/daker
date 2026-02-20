# VIBE-X Memory Log

> 이 파일은 AI 세션 간 컨텍스트를 보존하기 위해 자동으로 기록된다.  
> 매 3회 대화마다 시스템이 아래 양식으로 기록을 추가한다.

---

## 기록 형식

```
### [YYYY.MM.DD HH:mm] Session #{번호}

**결정사항:**
- {이번 세션에서 내린 설계/구현 결정}

**선택 근거:**
- {왜 이 방법을 선택했는지}

**주의사항:**
- {다음 세션에서 주의할 점}

**변경 파일:**
- {이번 세션에서 수정/생성한 파일 목록}

**다음 작업:**
- {이어서 진행할 작업}
```

---

## 기록

### [2026.02.12] Session #1 — 프로젝트 초기화

**결정사항:**
- VIBE-X 프로젝트 구조 확정 (5-Layer 아키텍처)
- 하이브리드 기술 스택 채택 (Python RAG + TypeScript 웹)
- Phase 1 산출물 6종 작성 시작

**선택 근거:**
- ADR-001 참고: RAG는 Python 생태계가 압도적, 웹은 TypeScript 필수
- Phase 순서 준수: 문서 기반 → RAG → Agent → 플랫폼

**주의사항:**
- Phase 1 문서는 모든 후속 작업의 기반. 꼼꼼히 작성 필요
- coding-rules.md가 확정되면 .cursorrules에 즉시 반영할 것

**변경 파일:**
- `project-definition.md` (생성)
- `architecture-map.md` (생성)
- `coding-rules.md` (생성)
- `docs/adr/template.md` (생성)
- `docs/adr/001-tech-stack.md` (생성)
- `templates/pact-d.md` (생성)
- `memory.md` (생성)

**다음 작업:**
- .cursorrules에 VIBE-X 규칙 통합
- Phase 2 — Vector DB 환경 구축 착수

### [2026.02.20] Session #2 — M2: RAG Engine 구축 완료

**결정사항:**
- ChromaDB 컬렉션에 코사인 유사도(hnsw:space=cosine) 적용
- SearchResult.relevance_score를 코사인 거리(0~2) 기반 변환 공식으로 수정
- 대시보드에 RAG Search 전용 탭 추가 (자연어 검색 + 언어 필터 + DB 통계)
- FastAPI에 3개 RAG API 엔드포인트 추가 (/api/rag/search, /api/rag/stats, /api/rag/index)

**선택 근거:**
- L2 거리는 스케일이 불명확하여 코사인(0~2 범위) 채택 → 검색 점수 0% → 62~76%로 대폭 개선
- 대시보드 통합은 M4(Platform) 선행 작업이지만, RAG 검증 목적으로 M2에서 함께 진행
- MCP Gate Check로 수정 파일 전체 Gate 1+2 통과 확인 (품질 보장)

**주의사항:**
- ChromaDB 컬렉션 메트릭 변경 시 반드시 reset → 재인덱싱 필요
- 현재 임베딩은 ChromaDB 기본 모델(all-MiniLM-L6-v2) 사용 — Voyage-code-3 전환은 별도 작업
- 대시보드 HTML이 2400줄+ 대형 파일. 향후 Next.js 컴포넌트 분리 필요

**변경 파일:**
- `src/layer2_rag/vector_db.py` (코사인 유사도 적용)
- `src/shared/types.py` (relevance_score 계산식 수정)
- `src/layer5_dashboard/app.py` (RAG API 3개 추가)
- `src/layer5_dashboard/static/dashboard.html` (RAG Search 탭 + CSS + JS + i18n)

**다음 작업:**
- Voyage-code-3 또는 sentence-transformers 커스텀 임베딩 적용 (검색 품질 추가 향상)
- 증분 인덱싱 + file watcher 연동 (파일 저장 시 자동 재인덱싱)
- M3: Agent Chain — 6-Gate 자동화 파이프라인 고도화

### [2026.02.20] Session #3 — M3: Agent Chain 고도화 완료

**결정사항:**
- 대시보드에 Pipeline Runner 전용 탭 추가 (6-Gate 실행 + 결과 시각화 + Bypass 모드)
- Collaboration 탭 신설: Work Zone 관리 + Decision Extractor 통합
- Pipeline API (`POST /api/pipeline`) 추가 — 파일 경로/작업자/바이패스 설정 가능
- Work Zone API 4종 추가: declare, release, list, map — 싱글턴 인스턴스로 상태 유지
- Decision Extractor API (`POST /api/decision/extract`) 추가 — ADR 자동 저장 옵션 포함
- Work Zone 상태를 `.state/work_zones.json`에 영속화하여 서버 재시작 간 보존

**선택 근거:**
- Pipeline Runner를 Gate Analysis와 분리하여 "실행"과 "분석"을 명확히 구분
- Work Zone을 싱글턴으로 유지하여 API 호출 간 충돌 감지 상태를 보존 (이전: 매 호출마다 새 인스턴스)
- Decision Extractor를 대시보드에 통합하여 비개발자도 미팅 노트에서 설계 결정 추출 가능
- `_resolve_file_path`/`_gate_result_to_dict` 헬퍼 분리로 Gate 2(50줄 규칙) 준수

**주의사항:**
- Gate 4(Review Agent)의 SEC-006 정규식이 `input|user` 키워드에 과도하게 반응 — 향후 수정 필요
- Work Zone 상태는 인메모리 + JSON 파일. 다중 서버 환경에서는 DB 또는 Redis 기반 전환 필요
- 대시보드 HTML이 3000줄+ 초과. Next.js 컴포넌트 분리가 점점 시급해짐

**변경 파일:**
- `src/layer5_dashboard/app.py` (Pipeline/WorkZone/Decision API 추가, 헬퍼 함수 분리)
- `src/layer5_dashboard/static/dashboard.html` (Pipeline 탭, Collaboration 탭, CSS, JS, i18n)

**다음 작업:**
- Gate 4 Review Agent 정규식 정밀도 개선 (SEC-006 오탐 수정)
- Work Zone → Collision Agent 양방향 실시간 연동 (현재는 단방향)
- 대시보드 Next.js 마이그레이션 계획 수립

---

### [2026.02.20] Session #4 — M4: Platform 고도화 완료

**결정사항:**
- Alert System 신규 구축 (`alert_system.py`) — 임계값 기반 경고 + WebSocket 실시간 푸시
  - Gate 실패율(30%/50%), AI 비용($5/$20), 건강점수(30/60) 3단계 임계값
  - 개별 Gate 결과 즉시 평가 (Gate 1-2 실패 시 CRITICAL, 아키텍처 위반 3건+ WARNING)
  - Alert 확인(dismiss) 개별/일괄 처리
- Onboarding Q&A 추가 (`onboarding.py` 확장) — RAG 기반 프로젝트 질의응답
  - Vector DB 검색 + 프로젝트 문서(project-definition, architecture-map, coding-rules) 키워드 매칭
  - ADR 컨텍스트 자동 수집 + 통합 답변 생성
- Health Score 4축 분해 (`metrics.py` 확장)
  - Gate 통과율(40%) + 아키텍처 일관성(25%) + 코드 품질(20%) + 활동 지수(15%)
  - 기술 부채 자동 탐지 (반복 실패 패턴 → severity high/medium 분류)
- 신규 API 6개: `/api/alerts`, `/api/alerts/acknowledge`, `/api/alerts/evaluate`, `/api/onboarding/qa`, `/api/health`, `record_gate`에 alert 평가 통합
- Dashboard UI: Alert Bar + 건강 점수 Breakdown Grid + Project Q&A 인터페이스 + i18n (ko/en)

**선택 근거:**
- Alert System을 별도 모듈로 분리하여 SRP 준수 (MetricsCollector와 책임 분리)
- Health Score를 4축 가중치 방식으로 설계하여 한 영역만 나빠져도 전체 점수에 반영
- Q&A에서 Vector DB + 프로젝트 문서 + ADR 3가지 소스를 교차 검색하여 답변 정확도 향상
- Alert 임계값을 Named Constants로 추출하여 향후 설정 파일 외부화 용이

**주의사항:**
- Alert 상태는 현재 인메모리 only — 서버 재시작 시 초기화됨 (지속성이 필요하면 JSON 파일 저장 추가)
- Rules Agent가 상수 정의 라인의 숫자 리터럴도 "매직 넘버"로 오탐 (alert_system.py L57, metrics.py L18)
- 대시보드 HTML 3500줄+ 도달 — Next.js 마이그레이션 우선순위 상승

**변경 파일:**
- `src/layer5_dashboard/alert_system.py` (신규 — Alert System)
- `src/layer5_dashboard/onboarding.py` (Q&A 기능 추가)
- `src/layer5_dashboard/metrics.py` (Health Breakdown + Tech Debt + Named Constants 리팩토링)
- `src/layer5_dashboard/app.py` (Alert/Q&A/Health API 6개 추가 + record_gate alert 통합)
- `src/layer5_dashboard/static/dashboard.html` (Alert Bar, Health Grid, Q&A UI, CSS, JS, i18n)

**다음 작업:**
- M4 Task 4.3: IDE 플러그인(cursor-vibex) 개발 — VSCode Extension API
- Alert 상태 파일 지속성 추가
- M5: Scale-out 전략 수립 (멀티 프로젝트, 팀 간 대시보드 통합)

---

### [2026.02.20] Session #5 — Next.js 마이그레이션 완료

**결정사항:**
- 3500줄+ 단일 HTML → Next.js 16 + TailwindCSS + TypeScript 컴포넌트 아키텍처로 전환
- 7개 라우트 페이지: Overview(`/`), Gates(`/gates`), Pipeline(`/pipeline`), Search(`/search`), Onboarding(`/onboarding`), Feedback(`/feedback`), Collaboration(`/collab`)
- API 서비스 레이어 (`lib/api.ts`) — 모든 FastAPI 엔드포인트를 타입 안전한 함수로 래핑
- WebSocket 커스텀 훅 (`hooks/useWebSocket.ts`) — 자동 재연결 + 상태 관리
- i18n 시스템 (`lib/i18n.ts`) — ko/en 지원, localStorage 영속화
- UI 컴포넌트: Card, StatusBadge, ProgressBar, Sidebar, Header, AlertBar
- Chart.js → react-chartjs-2 마이그레이션 (Line, Bar, Doughnut)
- Next.js rewrites로 API 프록시 (`localhost:3000/api/*` → `localhost:8000/api/*`)

**선택 근거:**
- App Router 선택: 파일 기반 라우팅으로 각 탭을 독립 페이지로 분리하여 코드 스플리팅 자동화
- TailwindCSS v4: 디자인 토큰 일관성 + 다크 테마 네이티브 지원
- 컴포넌트 분리: 단일 HTML의 인라인 CSS/JS를 기능별 컴포넌트로 분해하여 유지보수성 극대화
- API 프록시: CORS 이슈 없이 동일 도메인 통신, 프로덕션에서는 리버스 프록시로 전환 가능

**주의사항:**
- WebSocket은 Next.js rewrite로 프록시 불가 — FastAPI 직접 연결 유지 (포트 8000)
- 기존 `dashboard.html`은 호환성 유지 위해 삭제하지 않음 (레거시 폴백)
- react-chartjs-2 차트는 `'use client'` 필수
- `lucide-react` 아이콘 라이브러리 추가됨

**변경 파일 (신규):**
- `dashboard/` 전체 디렉토리 (Next.js 프로젝트)
  - `src/app/page.tsx` — Overview (Health Score, 차트 4개, 건강 점수 Breakdown)
  - `src/app/gates/page.tsx` — Gate 분석 (통과율 차트, 실행 이력 테이블)
  - `src/app/pipeline/page.tsx` — 6-Gate 파이프라인 실행기
  - `src/app/search/page.tsx` — RAG 시맨틱 검색 + 재인덱싱
  - `src/app/onboarding/page.tsx` — Q&A + 브리핑 + 아키텍처 시각화
  - `src/app/feedback/page.tsx` — 실패 패턴 분석 + 개선 제안
  - `src/app/collab/page.tsx` — Work Zone + Decision Extractor
  - `src/components/` — Sidebar, Header, AlertBar, UI 컴포넌트
  - `src/lib/` — api.ts, i18n.ts
  - `src/hooks/` — useWebSocket.ts

**다음 작업:**
- 프로덕션 배포 설정 (Docker, 리버스 프록시)
- E2E 테스트 추가
- 인증 시스템 Next.js Auth 마이그레이션

---

### [2026.02.20] Session #6 — M4 Task 4.3: IDE 플러그인(cursor-vibex) 완료

**결정사항:**
- `cursor-vibex` VSCode/Cursor Extension 프로젝트 생성 (TypeScript)
- 사이드바 WebView Panel: Health Score + Actions + Alerts + Work Zones 통합 뷰
- 6개 커맨드 구현:
  - `vibex.gateCheck` — 현재 파일 Gate 1-2 빠른 검사
  - `vibex.pipeline` — 현재 파일 6-Gate 전체 파이프라인
  - `vibex.ragSearch` — QuickPick 기반 시맨틱 검색 (결과 클릭 시 파일 이동)
  - `vibex.declareZone` — InputBox로 Work Zone 선언 + 충돌 경고
  - `vibex.insertPactd` — 커서 위치에 PACT-D 템플릿 삽입
  - `vibex.openDashboard` — 대시보드 외부 브라우저 오픈
- Gate Diagnostics: Pipeline 결과를 VSCode Problems 패널에 인라인 표시 (Error/Warning severity)
  - `L숫자:` 패턴 파싱으로 정확한 라인 매핑
- Extension 설정: `vibex.apiUrl`, `vibex.author` (Workspace/User 설정 가능)

**선택 근거:**
- WebView Sidebar: 별도 웹뷰 없이 사이드바에 Health/Alerts/Zones를 한눈에 표시
- QuickPick for RAG Search: VSCode 네이티브 UX 활용, 결과 선택 시 즉시 파일/라인 이동
- Diagnostics Collection: VSCode의 표준 Problems 패널 통합으로 인라인 에러/경고 표시
- PACT-D를 커맨드로 제공하여 프롬프트 작성 시 즉시 구조화 가능

**주의사항:**
- `fetch` API 사용 — Node 18+ 필요 (VSCode 1.85+ 기본 충족)
- VSIX 패키징에는 `@vscode/vsce` 필요 (`npx @vscode/vsce package`)
- 사이드바 WebView는 30초 간격 자동 리프레시 — 서버 미실행 시 graceful 처리

**변경 파일 (신규):**
- `cursor-vibex/package.json` — Extension manifest (commands, views, settings)
- `cursor-vibex/tsconfig.json` — TypeScript 설정
- `cursor-vibex/src/extension.ts` — Entry point, 6개 커맨드 등록
- `cursor-vibex/src/apiClient.ts` — VIBE-X API 타입 안전 클라이언트
- `cursor-vibex/src/gateDiagnostics.ts` — Gate 결과 → VSCode Diagnostics 변환
- `cursor-vibex/src/sidebarProvider.ts` — WebView Sidebar (Health, Actions, Alerts, Zones)
- `cursor-vibex/media/icon.svg` — Activity Bar 아이콘

**M4 전체 완료! 다음 작업:**
- M5: Scale-out — 멀티 프로젝트 지원, 팀 간 대시보드 통합
- VSIX 배포 패키징 + Marketplace 등록
- Docker Compose로 FastAPI + Next.js 통합 배포
- 인증 시스템 Next.js Auth 마이그레이션

---

### [2026.02.20] Session #7 — 옵션 B: 결과물 안정화 완료

**결정사항:**
1. Gate 4 SEC-006 오탐 수정 — 정규식 OR 연산자 그룹화 (lookahead 적용)
2. Alert 상태 영속화 — JSON 파일 기반 저장/복원 (`meta_dir/alerts_store.json`)
3. Backend API E2E 테스트 36개 작성 — 전체 엔드포인트 커버 (11개 클래스)
4. 인증 시스템 Next.js 마이그레이션 — Login/Admin 페이지, AuthContext, 라우트 보호
5. review_agent.py 매직 넘버 상수 추출 + test_types.py cosine 공식 반영
6. 전체 테스트 121/121 통과, Next.js 빌드 성공

**선택 근거:**
- SEC-006 오탐: lookahead 그룹화로 정확한 `assert + 사용자 입력` 패턴만 탐지
- Alert 영속화: WorkZone과 동일 패턴(JSON 파일)으로 아키텍처 일관성 유지
- E2E 테스트: FastAPI TestClient 기반, 서버 기동 없이 빠른 검증

**주의사항:**
- Gate 2 Rules Agent가 상수 정의 자체를 매직 넘버로 탐지 (오탐, 구조적 한계)
- 인증 secret key는 서버 인스턴스 레벨 → 재시작 시 기존 토큰 무효화
- admin/admin 기본 계정은 개발용, 프로덕션 배포 시 환경변수 비밀번호 필수

**변경 파일:**
- `src/layer3_agents/review_agent.py` — SEC-006 정규식 + 상수 추출
- `src/layer5_dashboard/alert_system.py` — JSON 영속화
- `tests/test_dashboard_api.py` — E2E 36개 테스트
- `tests/test_types.py` — cosine distance 기대값 수정
- `dashboard/src/lib/api.ts` — Auth API 추가
- `dashboard/src/lib/i18n.ts` — Auth i18n 문자열
- `dashboard/src/hooks/useAuth.ts` — AuthContext 신규
- `dashboard/src/app/login/page.tsx` — 로그인 페이지 신규
- `dashboard/src/app/admin/page.tsx` — 사용자 관리 페이지 신규
- `dashboard/src/app/AppShell.tsx` — Auth 통합
- `dashboard/src/components/Sidebar.tsx` — Admin 네비게이션
- `dashboard/src/components/Header.tsx` — 사용자 정보/로그아웃 UI

**다음 작업:**
- 옵션 A: M5 Scale-out (멀티 프로젝트, 팀 간 대시보드 통합)
- 옵션 C: Docker Compose 통합 배포 구성
- 옵션 D: VSIX 배포 패키징

---

### [2026.02.20] Session #8 — M5: Scale-out 멀티 프로젝트 지원 완료

**결정사항:**
1. `ProjectRegistry` 모듈 신규 — 프로젝트 등록/해제/수정/조회, JSON 영속화
2. `ProjectContextManager` 모듈 신규 — 프로젝트별 격리된 서비스 인스턴스(Metrics, Alerts, WorkZone 등) lazy-init 관리
3. FastAPI 멀티 프로젝트 API 11개 추가 — `/api/projects/*` (CRUD, aggregate, project-scoped dashboard/health/alerts/zones)
4. Next.js `/projects` 페이지 — 프로젝트 카드 뷰, 건강 점수 바, 집계 요약, 등록 폼
5. Sidebar에 Projects 탭 추가 (Admin/Lead 전용)
6. E2E 테스트 13개 추가 (총 49개 API 테스트, 전체 134개 통과)

**선택 근거:**
- 프로젝트별 격리: 각 프로젝트가 독립된 config/metrics/alerts를 가져 데이터 오염 방지
- Lazy-init: 프로젝트 전환 시에만 서비스 인스턴스를 생성하여 메모리 효율화
- Registry + Context 분리: SRP 원칙 — 메타데이터 관리(Registry)와 런타임 서비스(Context)를 분리

**주의사항:**
- 프로젝트 상한 MAX_PROJECTS = 50 (필요 시 조정)
- 프로젝트 등록 시 root_path가 실제 존재해야 함
- 프로젝트별 ChromaDB는 각 프로젝트의 vibe-x/.chromadb 경로를 사용
- 프로젝트 비활성화는 soft-delete (데이터 보존, config만 제거)

**변경 파일:**
- `src/layer5_dashboard/project_registry.py` — 신규 (Gate 1+2 통과)
- `src/layer5_dashboard/project_context.py` — 신규 (Gate 1+2 통과)
- `src/layer5_dashboard/app.py` — Multi-project API 11개 추가
- `tests/test_dashboard_api.py` — Multi-project 테스트 13개 추가
- `dashboard/src/lib/api.ts` — ProjectInfo 타입 + 프로젝트 API 메서드
- `dashboard/src/lib/i18n.ts` — 프로젝트 관련 i18n 문자열
- `dashboard/src/app/projects/page.tsx` — 멀티 프로젝트 관리 페이지 신규
- `dashboard/src/components/Sidebar.tsx` — Projects 탭 추가

**다음 작업:**
- 옵션 C: Docker Compose 통합 배포 구성 (FastAPI + Next.js)
- 옵션 D: VSIX 배포 패키징 + Marketplace 준비

---

### [2026.02.20] Session #9 — 프로젝트 간 팀원 권한 관리 고도화

**결정사항:**
1. `ProjectRole` Enum 도입: `owner`, `maintainer`, `developer`, `viewer` (전역 Role과 분리)
2. `ProjectMember` 모델: 사용자명 + 프로젝트 역할 + 참여일로 구성
3. 프로젝트 등록 시 `owner` 자동 배정, team 멤버는 `developer`로 추가
4. 프로젝트 스코프 권한 시스템 (`PROJECT_ROLE_PERMISSIONS`) - 전역 RBAC과 독립적
5. 전역 ADMIN은 모든 프로젝트에서 모든 권한 보유 (fallback)
6. OWNER 보호: 제거/역할변경 불가, 소유권 이전만 가능
7. `auth.py`에 `resolve_project_permission` 추가 — 전역+프로젝트 역할 통합 판정
8. 테스트 격리: `isolated_project_registry` fixture로 프로덕션 데이터 오염 방지

**선택 근거:**
- 전역 역할과 프로젝트 역할을 분리하여 "A 프로젝트에서는 maintainer, B에서는 viewer" 시나리오 지원
- OWNER 보호로 프로젝트 소유 의도치 않은 손실 방지
- `_parse_members`에서 dict/list 양쪽 호환하여 기존 데이터 마이그레이션 무중단

**주의사항:**
- OWNER 역할은 직접 부여 불가 — `transfer_ownership`으로만 변경
- 프로젝트 비활성화(unregister)는 멤버 데이터를 삭제하지 않음 (soft delete)
- `MAX_MEMBERS_PER_PROJECT = 100` 상한 존재

**변경 파일:**
- `src/layer5_dashboard/project_registry.py` — ProjectRole, ProjectMember, 멤버 관리 메서드 8개 추가
- `src/layer5_dashboard/auth.py` — resolve_project_permission 메서드 추가
- `src/layer5_dashboard/app.py` — 멤버 관리 API 6개 엔드포인트 추가
- `dashboard/src/lib/api.ts` — ProjectMember 타입 + 멤버 API 5개 추가
- `dashboard/src/lib/i18n.ts` — 멤버 관련 번역 키 16개 추가 (ko/en)
- `dashboard/src/app/projects/page.tsx` — 멤버 관리 UI 패널 추가
- `tests/test_dashboard_api.py` — TestProjectMemberAPI 12개 테스트 추가
- `tests/conftest.py` — isolated_project_registry fixture 추가

**테스트 결과:** 146/146 통과, Next.js 빌드 정상

**다음 작업:**
- 옵션 C: Docker Compose 통합 배포 구성 ✅ 완료

---

### [2026.02.20] Session #10 — 옵션 C: Docker Compose 통합 배포 구성 완료

**결정사항:**
1. FastAPI 백엔드 Dockerfile (`Dockerfile.backend`) — python:3.11-slim 기반, build-essential 포함
2. Next.js 프론트엔드 Dockerfile (`dashboard/Dockerfile`) — node:22-alpine 3-stage 빌드 (deps → builder → runner), standalone 출력
3. Docker Compose (`docker-compose.yml`) — backend + frontend 2-서비스, vibex-net 브릿지 네트워크
4. 네임드 볼륨 3개: vibex-data (.meta), vibex-state (.state), vibex-chromadb (.chromadb)
5. `next.config.ts` — `API_BACKEND_URL` 환경변수 기반 동적 rewrite, `output: 'standalone'`
6. Health check: 백엔드 `urllib.request`, 프론트엔드 `wget --spider`
7. frontend depends_on backend (condition: service_healthy)
8. `.dockerignore` 2개 (루트 + dashboard)

**선택 근거:**
- Multi-stage 빌드로 프론트엔드 이미지 최소화
- standalone 모드로 Next.js 서버 단독 실행
- 환경변수 기반 API URL로 개발/프로덕션 유연 전환
- 네임드 볼륨으로 컨테이너 재시작 시 데이터 보존

**주의사항:**
- 백엔드 이미지 크기가 큼 (torch + sentence-transformers) — CPU-only torch 권장
- npm audit 15개 vulnerability — 주기적 업데이트 필요

**검증 결과:**
- `docker compose build backend` — 성공
- `docker compose build frontend` — 성공
- `docker compose up -d` — backend Healthy, frontend Ready in 83ms
- `curl localhost:8000/api/dashboard` — 200 OK
- `curl localhost:3000/` — 200 OK

**변경 파일:**
- `Dockerfile.backend` (신규)
- `dashboard/Dockerfile` (신규)
- `docker-compose.yml` (신규)
- `.dockerignore` (신규)
- `dashboard/.dockerignore` (신규)
- `dashboard/next.config.ts` (수정)
- `memory.md` (업데이트)

**다음 작업:**
- 옵션 D: VSIX 배포 패키징 + Marketplace 준비
- 옵션 E: CI/CD 파이프라인 (GitHub Actions)
- 옵션 F: 프로덕션 최적화 (torch CPU-only, 이미지 경량화)

---

### [2026.02.20] Session #11 — 잔여 3건 완료 (Gate 3 고도화 + Git Hook + Hidden Intent)

**결정사항:**
1. **Gate 3 (Integration Agent) 고도화**
   - import 의존성 기반 reverse-import 탐색으로 영향 범위 분석 (depth=3)
   - 파일명 매칭 + 의존성 기반 이중 테스트 탐색 전략
   - pytest 출력 파싱 (통과 수, 실패 요약)으로 상세 리포트 생성
   - `/api/integration-test` API 엔드포인트 추가
2. **Git Hook 연동**
   - `.githooks/pre-commit` Python 스크립트: staged된 .py/.ts/.tsx 파일에 Gate 1+2 자동 실행
   - `scripts/setup_hooks.py`: git init + core.hooksPath 자동 설정
   - 실패 시 커밋 차단, `--no-verify`로 바이패스 가능
   - `.gitignore` 생성
3. **Hidden Intent File (.meta.json) 고도화**
   - `analyze_and_generate()`: AST 기반 자동 분석 (Python: ast.parse, TS/TSX: regex)
   - `batch_analyze()`: 디렉토리 전체 일괄 메타 생성
   - `index_meta()` / `index_all_metas()`: .meta.json → CodeChunk 변환 → Vector DB 인덱싱
   - 5개 API 엔드포인트: `/api/meta`, `/api/meta/generate`, `/api/meta/analyze`, `/api/meta/batch-analyze`, `/api/meta/index`
   - Next.js `/meta` 페이지 + TabBar 탭 추가

**선택 근거:**
- Gate 3: 단순 파일명 매칭만으로는 관련 테스트를 놓침 → import 역추적으로 정확도 향상
- Git Hook: Husky(Node) 대신 Python 스크립트 → 백엔드 Python 환경과 통합 용이
- Meta: 수동 입력만으로는 활용도 낮음 → AST 자동 분석으로 즉시 활용 가능

**주의사항:**
- Git Hook은 `python scripts/setup_hooks.py` 실행 후 사용 가능
- Meta batch 분석 시 대규모 프로젝트에서는 시간 소요 가능
- Windows cp949 인코딩 이슈로 스크립트 내 이모지 제거

**변경 파일:**
- `src/layer3_agents/integration_agent.py` — Gate 3 전면 재작성 (영향 범위 분석, 선별 실행)
- `src/layer2_rag/meta_generator.py` — 자동 분석, 배치, Vector DB 인덱싱 추가
- `src/layer5_dashboard/app.py` — 6개 API 엔드포인트 추가 (integration-test, meta*)
- `.githooks/pre-commit` — Git pre-commit 훅 스크립트 (신규)
- `scripts/setup_hooks.py` — Git Hook 설정 자동화 (신규)
- `.gitignore` — Git 무시 파일 (신규)
- `dashboard/src/app/meta/page.tsx` — Meta 관리 페이지 (신규)
- `dashboard/src/components/TabBar.tsx` — Meta 탭 추가
- `dashboard/src/lib/api.ts` — MetaInfo 인터페이스 + 6개 API 메서드 추가
- `dashboard/src/lib/i18n.ts` — meta 관련 번역 키 24개 추가 (ko/en)
- `tests/test_dashboard_api.py` — 10개 E2E 테스트 추가 (총 156개 전체 통과)

**테스트 결과:** 156 passed (전체 통과)

**다음 작업:**
- 옵션 D: VSIX 배포 패키징 + Marketplace 준비
- 옵션 E: CI/CD 파이프라인 (GitHub Actions)
- 옵션 F: 프로덕션 최적화 (torch CPU-only, 이미지 경량화)

### [2026.02.20] Session #12 — 의도 메타 탭 기능 확장

**결정사항:**
1. 의도 메타 탭을 3개 서브탭(메타 목록/커버리지/의존성 그래프)으로 확장
2. 검색/필터, 단일 파일 분석, 인라인 수정/삭제 기능 추가
3. 커버리지 통계 — 소스 파일 대비 메타 보유율(%) 시각화
4. 의존성 그래프 — 파일 간 import 관계를 노드/엣지 테이블로 표시

**선택 근거:**
- 기존 메타 탭은 목록 조회 + 일괄 분석만 가능했음 → 실무에서 개별 편집/삭제/검색이 필수
- 커버리지 통계 없이는 "어떤 파일에 메타가 없는지" 파악 불가
- 의존성 그래프는 코드 구조 이해에 핵심적 — 별도 도구 없이 대시보드에서 확인 가능

**변경 파일:**
- `src/layer2_rag/meta_generator.py` — update_meta, delete_meta, get_coverage, get_dependency_graph 추가
- `src/layer5_dashboard/app.py` — 5개 API 엔드포인트 추가 (coverage, dep-graph, update, delete)
- `dashboard/src/app/meta/page.tsx` — 전면 재작성 (3탭 구조 + 검색 + 수정/삭제)
- `dashboard/src/lib/api.ts` — MetaCoverage, DepGraph 인터페이스 + 4개 API 메서드 추가
- `dashboard/src/lib/i18n.ts` — 22개 i18n 키 추가 (ko/en)
- `tests/test_dashboard_api.py` — 6개 새 테스트 추가
- `docu/사용법.md` — 의도 메타 탭 섹션 업데이트

**테스트 결과:** 162 passed (신규 6건 포함)

**다음 작업:**
- 옵션 D: VSIX 배포 패키징 + Marketplace 준비
- 옵션 E: CI/CD 파이프라인 (GitHub Actions)
- 옵션 F: 프로덕션 최적화 (torch CPU-only, 이미지 경량화)
