# VIBE-X 구현 가이드

**작성일**: 2026. 02. 11  
**제안자**: 팀 바이브제왕  

---

## Phase 1: 오늘 당장 할 수 있는 것 (비용 $0, 3시간)

별도 개발 없이 **문서 작성만으로** 시작합니다.

| 할 일 | 구체적 행동 |
|-------|-----------|
| 프로젝트 정의서 작성 | `project-definition.md` — 기술 스택, 기능 목록, 담당자 합의 |
| 아키텍처 맵 작성 | `architecture-map.md` — 폴더 구조, ADR(기술 결정 기록), API 계약 |
| 코딩 규칙서 작성 | `coding-rules.md` — 팀 전원이 지켜야 할 규칙 10가지 |
| PACT-D 프롬프트 도입 | AI에게 작업 요청 시 Purpose/Architecture/Constraints/Test/Dependency 명시 |
| memory.md 자동화 | `.cursorrules`에 "매 3회 응답마다 memory.md에 기록하라" 규칙 추가 |

**필요 스킬**: 마크다운 작성 능력만 있으면 됩니다.

---

## Phase 2: 1~2주 안에 세팅할 것 (비용 $0)

기본적인 도구 세팅과 자동화입니다.

| 할 일 | 구체적 행동 | 필요 스킬 |
|-------|-----------|----------|
| RAG 초기 세팅 | Continue.dev 설치 + 코드베이스 임베딩 생성 | VS Code 사용법 |
| Vector DB 구축 | ChromaDB 또는 LanceDB 로컬 설치 | Python 기초 |
| Git Hook 설정 | Husky로 pre-commit 훅 → 린터/타입 검사 자동 실행 | npm/Git 기초 |
| 메타데이터 습관화 | `/gen-with-meta` 커맨드 생성 (코드+의도 동시 생성) | Continue.dev 설정 |

### 실행 예시 — ChromaDB 설치

```bash
pip install chromadb
pip install langchain langchain-community
```

### 실행 예시 — `.cursorrules`에 추가할 내용

```text
매 3회 응답마다, 작업 내용을 .vibe-x/memory.md에 다음 형식으로 기록하세요:
## 변경된 파일
- [파일명]: [변경 내용 한 줄 요약]
## 결정 사항
- [결정 내용]: [이유]
## 현재 상태
- 진행 중: [작업 내용]
- 다음 할 일: [예정 작업]
```

---

## Phase 3: 1~2개월에 걸쳐 개발할 것 (개발 인건비)

여기서부터 **코딩이 필요**합니다.

| 할 일 | 기술 요구사항 | 난이도 |
|-------|-------------|:------:|
| RAG 파이프라인 자동화 | Python + LangChain으로 Git Hook 연동 인덱싱 | 중 |
| Quality Gate Agent 구현 | AST 분석 스크립트 + AI 리뷰 API 호출 | 중~상 |
| MCP 서버 구축 | TypeScript/Python으로 MCP 서버 개발 (팀 컨텍스트 공유) | 상 |
| Decision Extractor | LLM API로 대화에서 설계 결정 자동 추출 | 중 |
| 충돌 감지 스크립트 | Git diff 분석 + 팀 상태 문서 대조 | 중 |

**필요 스킬**: Python, LangChain, MCP SDK, Git 내부 구조 이해

### 실행 예시 — 간단한 RAG 인덱서 뼈대

```python
# update_rag_index.py (Git pre-commit hook에서 호출)
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings

def index_changed_files(file_paths):
    docs = []
    for path in file_paths:
        loader = TextLoader(path)
        docs.extend(loader.load())
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
    chunks = splitter.split_documents(docs)
    
    vectorstore = Chroma.from_documents(
        chunks,
        OpenAIEmbeddings(),
        persist_directory=".vibe-x/vectordb"
    )
    vectorstore.persist()
```

---

## Phase 4: 3~6개월 장기 개발 (플랫폼화)

팀 규모가 커질 때 필요한 단계입니다.

| 할 일 | 기술 요구사항 |
|-------|-------------|
| 팀 대시보드 웹 앱 | React/Next.js + DB (프로젝트 건강 지표 시각화) |
| IDE 플러그인 개발 | VS Code Extension API (Cursor/VSCode 확장) |
| 실시간 팀 동기화 서버 | WebSocket + 상태 관리 서버 (월 $20~50 인프라) |
| 온보딩 자동화 | RAG 기반 프로젝트 브리핑 자동 생성 |

---

## 현실적인 추천 순서

당장 혼자 또는 소규모 팀이라면:

```
1단계 (오늘)    → Phase 1 문서 작성 + .cursorrules 설정
2단계 (이번 주)  → Continue.dev + ChromaDB 설치, @Codebase 활용 시작
3단계 (다음 주)  → Git Hook으로 Gate 1~2 자동화 (린터/타입 검사)
4단계 (1개월 후) → RAG 파이프라인 + Decision Extractor 개발
5단계 (필요 시)  → MCP 서버 + 대시보드 (팀이 5명 이상일 때)
```

> **가장 중요한 것은 Phase 1을 오늘 시작하는 것입니다.**  
> 문서 3개(`project-definition.md`, `architecture-map.md`, `coding-rules.md`)를 만들고  
> `.cursorrules`에 memory.md 자동 기록 규칙을 넣는 것만으로도  
> 바이브 코딩의 품질이 체감할 수 있을 만큼 달라집니다.

---

*팀 바이브제왕 | 2026. 02. 11*
