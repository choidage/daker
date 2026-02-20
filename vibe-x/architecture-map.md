# VIBE-X 아키텍처 맵

> **팀 바이브제왕** | 버전: v1.0 | 최종 수정: 2026.02.12

---

## 1. 5-Layer 아키텍처 개요

```
┌─────────────────────────────────────────────────────┐
│  Layer 5: 팀 인텔리전스 대시보드                       │
│  (프로젝트 건강 지표, 비용 관리, 온보딩 자동화)          │
├─────────────────────────────────────────────────────┤
│  Layer 4: 협업 오케스트레이터                          │
│  (팀 컨텍스트 동기화, 충돌 감지, 작업 영역 분리)         │
├─────────────────────────────────────────────────────┤
│  Layer 3: 멀티 Agent 품질 게이트                      │
│  (6-Gate 자율 검증 체인)                              │
├─────────────────────────────────────────────────────┤
│  Layer 2: Living RAG Memory Engine                   │
│  (Vector DB, 임베딩, 코드베이스 지식화)                 │
├─────────────────────────────────────────────────────┤
│  Layer 1: 구조화 프롬프트 & 스캐폴딩                   │
│  (PACT-D, 팀 문서, coding-rules)                     │
└─────────────────────────────────────────────────────┘
  ↕ MCP (Model Context Protocol) — 전 Layer 관통 통신 ↕
```

---

## 2. 디렉토리 구조 표준

```
vibe-x/
├── project-definition.md        # 프로젝트 정의서
├── architecture-map.md          # 이 문서
├── coding-rules.md              # 코딩 규칙
├── memory.md                    # AI 컨텍스트 기록
│
├── docs/
│   └── adr/                     # Architecture Decision Records
│       ├── template.md          # ADR 템플릿
│       └── 001-tech-stack.md    # 첫 번째 ADR
│
├── templates/
│   └── pact-d.md                # PACT-D 프롬프트 템플릿
│
├── src/
│   ├── layer1-scaffold/         # Layer 1: 프롬프트 & 스캐폴딩
│   │   ├── prompt-builder.ts    # PACT-D 프롬프트 자동 생성
│   │   └── rules-injector.ts    # 코딩 규칙 자동 주입
│   │
│   ├── layer2-rag/              # Layer 2: RAG Memory Engine
│   │   ├── vector-db.ts         # LanceDB 연결 및 관리
│   │   ├── embedder.ts          # Voyage-code-3 임베딩
│   │   ├── chunker.ts           # 코드 청킹 전략
│   │   ├── indexer.ts           # 자동 인덱싱 파이프라인
│   │   ├── searcher.ts          # 시맨틱 검색 엔진
│   │   └── meta-generator.ts   # .meta.json 생성기
│   │
│   ├── layer3-agents/           # Layer 3: 멀티 Agent 품질 게이트
│   │   ├── gate-runner.ts       # 6-Gate 파이프라인 오케스트레이터
│   │   ├── syntax-agent.ts      # Gate 1: 린터 + 타입 검사
│   │   ├── rules-agent.ts       # Gate 2: 코딩 규칙 검증
│   │   ├── integration-agent.ts # Gate 3: 테스트 실행
│   │   ├── review-agent.ts      # Gate 4: AI 코드 리뷰
│   │   ├── arch-agent.ts        # Gate 5: ADR 정합성
│   │   └── collision-agent.ts   # Gate 6: 충돌 감지
│   │
│   ├── layer4-collab/           # Layer 4: 협업 오케스트레이터
│   │   ├── mcp-server.ts        # MCP 서버 코어
│   │   ├── context-sync.ts      # 팀 컨텍스트 동기화
│   │   ├── work-zone.ts         # 작업 영역 분리
│   │   ├── decision-extractor.ts# 설계 결정 자동 추출
│   │   └── handoff.ts           # 자동 핸드오프
│   │
│   ├── layer5-dashboard/        # Layer 5: 대시보드
│   │   ├── app/                 # Next.js App Router
│   │   ├── components/          # UI 컴포넌트
│   │   ├── api/                 # API 라우트
│   │   └── lib/                 # 유틸리티
│   │
│   └── shared/                  # 공유 모듈
│       ├── types.ts             # 공통 타입 정의
│       ├── config.ts            # 환경 설정
│       └── logger.ts            # 로깅 유틸
│
├── hooks/                       # Git Hooks (Husky)
│   ├── pre-commit               # Gate 1, 2 실행
│   └── pre-push                 # Gate 3, 4, 5 실행
│
├── .cursorrules                 # Cursor AI 규칙 (VIBE-X 통합)
├── package.json
├── tsconfig.json
└── .gitignore
```

---

## 3. 모듈 간 의존성

```
Layer 1 (Scaffold)
    │
    ▼ rules, prompts
Layer 2 (RAG Memory)  ←──── .meta.json, Git Hooks
    │
    ▼ context, knowledge
Layer 3 (Agent Gates)
    │
    ▼ validation results
Layer 4 (Collaboration) ←── MCP protocol
    │
    ▼ team metrics, alerts
Layer 5 (Dashboard)
```

### 모듈 간 인터페이스

| From | To | 인터페이스 | 데이터 |
|------|----|-----------|--------|
| L1 → L2 | rules-injector → indexer | `IndexRequest` | 규칙 문서, ADR |
| L2 → L3 | searcher → gate-runner | `ContextPayload` | 관련 코드 컨텍스트 |
| L3 → L4 | gate-runner → mcp-server | `GateResult` | 검증 결과 (pass/fail) |
| L4 → L5 | context-sync → dashboard API | `TeamMetrics` | 팀 상태, 지표 |
| L4 → L3 | collision-agent → gate-runner | `CollisionAlert` | 충돌 감지 알림 |
| L2 → L4 | meta-generator → decision-extractor | `IntentMeta` | 설계 의도 메타데이터 |

---

## 4. 데이터 흐름도

```
[개발자] ──프롬프트──▶ [PACT-D Builder] ──구조화 프롬프트──▶ [LLM]
                                                              │
                              ┌────────────────────────────────┘
                              ▼
                      [코드 + .meta.json]
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
              [Git Hook]  [Indexer]  [Gate Runner]
                    │         │         │
                    ▼         ▼         ▼
              [Lint/Type] [Vector DB] [6-Gate 검증]
                                        │
                              ┌─────────┼─────────┐
                              ▼         ▼         ▼
                        [MCP 공유] [ADR 반영] [팀 알림]
                              │
                              ▼
                        [Dashboard]
```

---

## 5. API 엔드포인트 명세 (Phase 4)

### 5.1 RAG API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/rag/query` | 자연어 코드 검색 |
| POST | `/api/rag/index` | 수동 인덱싱 트리거 |
| GET | `/api/rag/status` | 인덱싱 상태 조회 |

### 5.2 Agent API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/gate/run` | 6-Gate 파이프라인 실행 |
| GET | `/api/gate/status/:id` | Gate 실행 결과 조회 |
| GET | `/api/gate/history` | Gate 이력 조회 |

### 5.3 Collaboration API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/zone/declare` | 작업 영역 선언 |
| GET | `/api/zone/active` | 활성 작업 영역 조회 |
| GET | `/api/decisions` | 설계 결정 목록 |
| POST | `/api/decisions` | 설계 결정 등록 |

### 5.4 Dashboard API
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/metrics/overview` | 프로젝트 건강 지표 |
| GET | `/api/metrics/cost` | AI 비용 현황 |
| GET | `/api/metrics/quality` | 코드 품질 추이 |
| WS | `/ws/realtime` | 실시간 상태 스트림 |

---

## 6. 상태 관리 전략

| 영역 | 전략 | 도구 |
|------|------|------|
| 클라이언트 상태 | Zustand Store | `useProjectStore`, `useGateStore` |
| 서버 상태 | React Query | API 캐싱, 자동 리프레시 |
| 실시간 상태 | WebSocket | 팀 활동, Gate 결과, 알림 |
| 영속 상태 | Vector DB + File System | 코드 인덱스, ADR, memory.md |

---

> *아키텍처는 고정이 아닌 진화한다. 모든 변경은 ADR로 기록한다.*
