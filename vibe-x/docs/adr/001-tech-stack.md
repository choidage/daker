# ADR-001: 기술 스택 선정

> **상태:** 승인  
> **작성일:** 2026.02.12  
> **작성자:** 팀 바이브제왕  
> **관련 태스크:** Task 1.1, Task 1.4

---

## 컨텍스트

VIBE-X 통합 협업 플랫폼을 구축하기 위한 기술 스택을 결정해야 한다.
- 5-Layer 아키텍처를 지원할 수 있어야 함
- RAG 파이프라인(Python 생태계)과 웹 서비스(Node.js)를 모두 다뤄야 함
- 팀 규모 2~15명의 소~중규모 팀에 적합해야 함
- 비용을 최소화하면서 확장 가능해야 함

## 고려한 대안

### 대안 1: 풀 Python (FastAPI + Streamlit)
- **장점:** ML/RAG 파이프라인과 통일, 학습 곡선 낮음
- **단점:** 프론트엔드 품질 제한 (Streamlit), 대시보드 커스터마이징 어려움
- **비용:** $0

### 대안 2: 풀 TypeScript (Next.js + Express)
- **장점:** 풀스택 통일, Next.js 대시보드 품질 높음
- **단점:** Python ML 생태계 활용 불가, RAG 구현 복잡
- **비용:** $0

### 대안 3: 하이브리드 (FastAPI + Next.js + Express)
- **장점:** 각 도메인 최적 도구 사용, RAG는 Python, 웹은 TypeScript
- **단점:** 두 언어 관리 필요, 통신 오버헤드
- **비용:** $0

## 결정

**대안 3: 하이브리드 (FastAPI + Next.js + Express)**를 채택한다.

## 근거

1. **RAG/임베딩은 Python 생태계가 압도적** — LangChain, LlamaIndex, Voyage-code-3 모두 Python 네이티브
2. **대시보드/IDE 플러그인은 TypeScript가 필수** — Next.js, VSCode Extension API
3. **MCP 서버는 Express.js가 적합** — 경량, WebSocket, MCP SDK 지원
4. **두 언어 관리 비용 < 잘못된 도구 선택 비용** — 각 Layer가 독립적이므로 경계가 명확

## 결과

- **변경되는 것:** Layer 2(RAG)는 Python, Layer 3~5는 TypeScript로 구현
- **영향받는 모듈:** 전체
- **주의할 점:** Python ↔ TypeScript 통신은 REST API + MCP로 표준화

## 참고

- Vector DB: LanceDB (Python/TypeScript 모두 지원)
- 임베딩: Voyage-code-3 (Python SDK 우선, REST API 대안)
