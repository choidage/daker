# VIBE-X: 바이브 코딩의 구조적 한계를 해결하는 통합 협업 플랫폼

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple.svg)](https://modelcontextprotocol.io/)

> **DAKER 공모전 출품작** | 205팀 중 **9위 (상위 4.4%)** | 팀 바이브제왕

---

## 프로젝트 개요

**VIBE-X (Vibe Intelligent Build Environment — eXtended)** 는 바이브 코딩(Vibe Coding)의 구조적 한계를 해결하기 위해 설계된 통합 협업 플랫폼입니다.

AI 코드 생성 도구(Cursor, Copilot 등)의 생산성은 혁명적이지만, **"세션이 끝나면 의도가 증발하는 문제"** 와 **"팀 단위 협업에서 발생하는 아키텍처 분열"** 이라는 두 가지 구조적 한계가 존재합니다.

VIBE-X는 **Agent + MCP + RAG + 협업 프로토콜**을 5-Layer 구조로 통합하여, 이 이중 한계를 동시에 해결합니다.

---

## 공모전 성과

| 항목 | 내용 |
|------|------|
| **대회** | DAKER 공모전 (메가톤급) |
| **상금** | 1,000,000원 |
| **기간** | 2026.01.19 ~ 02.23 |
| **참가 팀** | 205팀 |
| **최종 순위** | **9위 / 205팀 (상위 4.4%)** |
| **제출 건수** | 102건 / 876건 |
| **조회수** | 11,451 |

---

## 문제 정의

### 제1축 — 모델 품질 격차: "Memory-less Generation"
- 세션 종료 시 의도/맥락이 증발하는 "Just-in-Time Intelligence" 구조
- 전체 아키텍처를 고려하지 않은 국소적 AI 수정으로 누더기 코드 발생
- 품질 게이트 없이 AI 생성 코드가 그대로 적용

### 제2축 — 팀 협업의 벽: Opus도 해결 못하는 문제
- **컨텍스트 고립**: 각 개발자의 AI 세션이 완전히 독립적
- **아키텍처 분열**: 각자 다른 패턴/라이브러리로 구현
- **암묵적 결정 소실**: 설계 결정이 AI 대화 속에 매몰
- **동시 작업 충돌**: AI의 대규모 파일 수정으로 충돌 빈발

> **핵심 인사이트**: 모델 품질 문제는 고성능 모델로 부분 완화 가능하지만, 협업 축의 문제는 어떤 모델로도 해결되지 않는다.

---

## 해결 방안: 5-Layer 통합 아키텍처

```
┌───────────────────────────────────────────────────────────┐
│  Layer 5: 팀 인텔리전스 대시보드                              │
│           — 프로젝트 건강 지표, 비용 관리, 온보딩 자동화       │
├───────────────────────────────────────────────────────────┤
│  Layer 4: 협업 오케스트레이터 (MCP 기반)                      │
│           — 팀 컨텍스트 동기화, 충돌 사전 감지                │
├───────────────────────────────────────────────────────────┤
│  Layer 3: 멀티 Agent 6-Gate 품질 검증                        │
│           — 자율 Agent 체인으로 6단계 품질 검증               │
├───────────────────────────────────────────────────────────┤
│  Layer 2: Living RAG Memory Engine                          │
│           — 코드베이스를 질문 가능한 지식 베이스로 전환        │
├───────────────────────────────────────────────────────────┤
│  Layer 1: 구조화 프롬프트 & 프로젝트 스캐폴딩                 │
│           — PACT-D 프레임워크, 팀 설계 청사진                 │
└───────────────────────────────────────────────────────────┘
           ↕ MCP(Model Context Protocol) — 전체를 관통하는 통신 계층 ↕
```

---

## 주요 기능

### 6-Gate 품질 검증 파이프라인

| Gate | Agent | 역할 | 비용 |
|------|-------|------|------|
| Gate 1 | Syntax Agent | 린터/타입 검사 자동 실행 | $0 |
| Gate 2 | Rules Agent | 팀 코딩 규칙 준수 여부 검증 | $0 |
| Gate 3 | Integration Agent | 기존 테스트 통과 확인 | 저 |
| Gate 4 | Review Agent | AI 교차 검증 (보안/성능) | 저 |
| Gate 5 | Architecture Agent | ADR 정합성, 폴더 규약 검사 | $0 |
| Gate 6 | Collision Agent | 팀원 작업 충돌 사전 감지 | $0 |

### Living RAG Memory Engine
- 코드 생성 시 **Hidden Intent File (.meta.json)** 자동 생성
- Git Hook 기반 자동 인덱싱 → Vector DB (ChromaDB)
- 자연어로 코드 의도 질의: "이 함수 왜 이렇게 구현했어?"

### 협업 오케스트레이터
- **Work Zone Isolation**: 작업 영역 선언 → 충돌 사전 방지
- **Decision Extractor**: AI 대화에서 설계 결정 자동 추출 → ADR 반영
- **MCP Hub**: 팀 컨텍스트 실시간 동기화

### 팀 인텔리전스 대시보드 (10개 탭)
| 탭 | 기능 |
|----|------|
| 개요 | 프로젝트 건강 점수, Gate 통과율, AI 비용 |
| Gate 분석 | Gate별 통과율 비교 분석 |
| 파이프라인 | 6-Gate 파이프라인 직접 실행 |
| RAG 검색 | 코드베이스 시맨틱 검색 |
| 온보딩 | 프로젝트 Q&A + 아키텍처 브리핑 |
| 피드백 루프 | Gate 실패 패턴 분석 + 개선 제안 |
| 협업 | 작업 영역 선언 + 설계 결정 추출 |
| 의도 메타 | .meta.json 관리 + Vector DB 인덱싱 |
| 프로젝트 | 멀티 프로젝트 + 팀원 권한 관리 |
| 관리자 | 사용자 계정 + 역할 관리 |

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | Python 3.11+, FastAPI, SQLite |
| **Frontend** | React 18, TailwindCSS, Chart.js |
| **AI/RAG** | LangChain, ChromaDB, Voyage-code-3 |
| **통신 프로토콜** | MCP (Model Context Protocol) |
| **자동화** | Git Hooks (Husky), AST 분석 |
| **IDE 확장** | VS Code Extension API |
| **배포** | Docker Compose |
| **실시간** | WebSocket |

---

## 프로젝트 구조

```
daker/
├── vibe-x/                    # VIBE-X 메인 플랫폼
│   ├── src/
│   │   ├── layer1_scaffold/   # 구조화 프롬프트 & 스캐폴딩
│   │   ├── layer2_rag/        # Living RAG Memory Engine
│   │   ├── layer3_agent/      # 멀티 Agent 6-Gate 품질 검증
│   │   ├── layer4_collab/     # 협업 오케스트레이터 (MCP)
│   │   └── layer5_dashboard/  # 팀 인텔리전스 대시보드
│   ├── dashboard/             # React 프론트엔드
│   └── requirements.txt
├── vibe-x-extension/          # VS Code/Cursor IDE 확장 플러그인
├── mcp/                       # MCP 서버 구현
├── docu/                      # 프로젝트 문서
│   ├── 바이브코딩_개선_아이디어.md       # 메인 제안서
│   ├── codebase_rag_proposal.md        # RAG 기술 제안서
│   ├── VIBE-X_구현_가이드.md            # 구현 가이드
│   ├── VIBE-X_세부작업_기획안.md        # 세부 작업 기획
│   ├── 사용법.md                       # 대시보드 사용법
│   └── VibeCoding_Improvement_Proposal.pdf  # 공모전 제출 제안서
├── dashboard.html             # 대시보드 HTML
└── docker-compose.yml         # Docker 배포 설정
```

---

## 빠른 시작

### Docker Compose (권장)
```bash
git clone https://github.com/choidage/daker.git
cd daker
docker compose up -d
# http://localhost:3000 접속 (admin / admin1234)
```

### 수동 실행
```bash
# 백엔드
cd vibe-x
pip install -r requirements.txt
uvicorn src.layer5_dashboard.app:app --reload --port 8000

# 프론트엔드
cd dashboard
npm install
npm run dev
# http://localhost:3000
```

---

## 비용-효과 분석

| 항목 | Opus x 5명 (시스템 없음) | VIBE-X + Sonnet x 5명 | 절감률 |
|------|------------------------|----------------------|--------|
| 월 총비용 | ~$750 | ~$108 | **86%** |

| 지표 | Opus x 5 (시스템 없음) | VIBE-X + Sonnet x 5 |
|------|----------------------|---------------------|
| 아키텍처 일관성 | 40% | **90%** |
| 통합 충돌률 | 45% | **12%** |
| 설계 결정 추적률 | 10% | **85%** |
| 온보딩 시간 | 2~3주 | **2~3일** |

---

## 팀 정보

| 항목 | 내용 |
|------|------|
| **팀명** | 바이브제왕 (바이브의제왕) |
| **구성** | 2명 핵심 개발 |
| **본인 기여도** | 전체의 약 80% (기획, 설계, 개발, 배포) |
| **역할** | 서비스 기획, 5-Layer 아키텍처 설계, 대시보드 개발, MCP 서버 구축, Docker 배포 |

---

## 문서

| 문서 | 설명 |
|------|------|
| [바이브코딩 개선 아이디어](docu/바이브코딩_개선_아이디어.md) | 문제 분석 + VIBE-X 5-Layer 아키텍처 전체 제안서 |
| [Codebase RAG 제안서](docu/codebase_rag_proposal.md) | Living RAG Memory 기술 상세 아키텍처 |
| [VIBE-X 구현 가이드](docu/VIBE-X_구현_가이드.md) | Phase 1~4 단계별 구현 가이드 |
| [세부작업 기획안](docu/VIBE-X_세부작업_기획안.md) | Task 정의, KPI, 리스크 관리 |
| [대시보드 사용법](docu/사용법.md) | 10개 탭 상세 사용법 |
| [공모전 제안서 PDF](docu/VibeCoding_Improvement_Proposal.pdf) | 공모전 최종 제출 문서 |

---

## 배운 점

- **시스템 설계의 중요성**: 좋은 모델보다 좋은 시스템이 팀 생산성에 더 큰 영향을 준다는 것을 실증
- **MCP 프로토콜 실무 적용**: 표준 통신 프로토콜을 활용한 도구 간 연동 경험
- **RAG 파이프라인 구축**: 코드베이스를 지식 베이스로 전환하는 실무 아키텍처 설계
- **풀사이클 개발 경험**: 기획 → 설계 → 개발 → 배포까지 전 과정을 주도
- **공모전 성과**: 205팀 중 9위 달성으로 아이디어의 실현 가능성 검증

---

## 라이선스

MIT License

---

*팀 바이브제왕 | 2026*