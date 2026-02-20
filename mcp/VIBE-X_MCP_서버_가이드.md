# VIBE-X MCP 서버 가이드

## 개요

VIBE-X를 **MCP (Model Context Protocol) 서버**로 만들어, Cursor/Claude 등 AI 어시스턴트가
코딩 중 자동으로 품질 검사, 코드 검색, 아키텍처 검증을 수행할 수 있게 합니다.

```
┌─────────────────────────────────────────────────────────┐
│  AI 어시스턴트 (Cursor, Claude Desktop 등)              │
│                                                         │
│  "이 코드 보안 문제 있어?"  →  security_review 호출     │
│  "인증 관련 코드 찾아줘"    →  code_search 호출         │
│  "커밋해도 될까?"           →  pipeline 호출            │
│                                                         │
│          ↕  MCP Protocol (stdio / SSE)                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  VIBE-X MCP Server (mcp_server.py)              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │    │
│  │  │Gate 1~6  │ │RAG Search│ │Work Zone Mgr │    │    │
│  │  │Pipeline  │ │Indexer   │ │Decision Ext. │    │    │
│  │  └──────────┘ └──────────┘ └──────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 1. 사전 준비

```bash
# 의존성 설치
cd vibe-x
pip install -r requirements.txt
```

`requirements.txt`에 `mcp>=1.0.0`이 포함되어 있습니다.

---

## 2. Cursor에서 사용하기

### 2-1. 설정 파일 (이미 생성됨)

`.cursor/mcp.json` 파일:

```json
{
  "mcpServers": {
    "vibe-x": {
      "command": "python",
      "args": [
        "c:\\Users\\USER\\OneDrive\\Desktop\\daker\\mcp\\mcp_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "VIBE_X_NO_WRAP_STDOUT": "1"
      }
    }
  }
}
```

### 2-2. 적용 방법

1. **Cursor를 재시작**합니다.
2. Settings → Features → MCP에서 "vibe-x" 서버가 녹색으로 표시되는지 확인합니다.
3. 이후 AI에게 다음과 같이 요청하면 자동으로 VIBE-X 도구가 호출됩니다:

```
"이 파일의 품질 검사를 해줘"
→ AI가 자동으로 gate_check 또는 pipeline 도구 호출

"보안 취약점 검사해줘"
→ security_review 도구 호출

"인증 관련 코드를 찾아줘"
→ code_search 도구 호출
```

---

## 3. Claude Desktop에서 사용하기

`%APPDATA%\Claude\claude_desktop_config.json` 파일에 추가:

```json
{
  "mcpServers": {
    "vibe-x": {
      "command": "python",
      "args": ["C:\\Users\\USER\\OneDrive\\Desktop\\daker\\mcp\\mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "VIBE_X_NO_WRAP_STDOUT": "1"
      }
    }
  }
}
```

---

## 4. 제공되는 MCP 도구 (9개)

| 도구 | 설명 | 사용 시점 |
|------|------|-----------|
| `gate_check` | 기본 품질 Gate 1(문법), Gate 2(규칙) 실행 | 파일 저장 후 |
| `pipeline` | 6-Gate 전체 파이프라인 실행 | 커밋 전 |
| `security_review` | 보안 취약점 + 성능 안티패턴 검사 | 보안 민감 코드 작성 시 |
| `architecture_check` | Layer 의존성, 네이밍, 구조 검증 | 새 모듈 추가 시 |
| `code_search` | 자연어 기반 시맨틱 코드 검색 | "~하는 함수 어디?" |
| `index_codebase` | 프로젝트 벡터 DB 인덱싱 | 최초 1회 + 주기적 |
| `work_zone` | 팀 작업 영역 선언/해제/조회 | 팀 협업 시 |
| `extract_decisions` | 텍스트에서 설계 결정 ADR 추출 | 리뷰/미팅 후 |
| `project_status` | 프로젝트 전체 상태 요약 | 현황 파악 시 |

---

## 5. 제공되는 MCP 리소스 (2개)

| 리소스 URI | 설명 |
|-----------|------|
| `vibe-x://architecture` | 5-Layer 아키텍처 구조 정보 |
| `vibe-x://coding-rules` | 프로젝트 코딩 규칙 |

---

## 6. 사용 시나리오 예시

### 시나리오 A: 코드 작성 중 품질 검사

```
사용자: "방금 만든 user_service.py 파일 품질 검사해줘"

AI (Cursor): [gate_check 호출]
  → "Gate 1 통과, Gate 2에서 이슈 2개 발견:
     1. 함수명 getUser → get_user (snake_case 규칙)
     2. unused import: os"
```

### 시나리오 B: 커밋 전 전체 파이프라인

```
사용자: "이 파일 커밋해도 될까?"

AI (Cursor): [pipeline 호출]
  → "6-Gate 결과: 전체 PASS
     Gate 1(문법) ✓ | Gate 2(규칙) ✓ | Gate 3(테스트) ✓
     Gate 4(보안) ✓ | Gate 5(아키텍처) ✓ | Gate 6(충돌) ✓
     커밋해도 안전합니다."
```

### 시나리오 C: 코드 검색

```
사용자: "사용자 인증 처리하는 코드가 어디 있지?"

AI (Cursor): [code_search 호출 → query="사용자 인증 처리"]
  → "src/layer5_dashboard/auth.py (관련도 92%)
     - AuthManager.login() 메서드 (line 45-78)
     - verify_token() 메서드 (line 80-95)"
```

### 시나리오 D: 팀 협업

```
사용자: "내가 auth.py 수정할 건데 작업 영역 선언해줘"

AI (Cursor): [work_zone 호출 → action="declare"]
  → "작업 영역 선언 완료: auth.py
     현재 다른 팀원이 수정 중인 파일: 없음 (안전)"
```

---

## 7. 다른 프로젝트에 적용하기

### 7-1. VIBE-X를 다른 프로젝트에서 사용

`mcp.json`의 `args`에 절대 경로를 지정하면 어느 프로젝트에서든 사용 가능:

```json
{
  "mcpServers": {
    "vibe-x": {
      "command": "python",
      "args": ["C:\\경로\\mcp\\mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "VIBE_X_NO_WRAP_STDOUT": "1"
      }
    }
  }
}
```

### 7-2. SSE 모드로 공유 서버 운영

```bash
# 팀 공용 서버로 실행
python mcp_server.py --transport sse
```

팀원들이 같은 MCP 서버에 접속하여 협업 기능을 공유할 수 있습니다.

---

## 8. 기존 CLI와의 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| **CLI** (`python cli.py`) | 직접 제어, 스크립트 자동화 | 수동 실행 필요 |
| **IDE Extension** | UI 통합, 자동 실행 | 설치 필요 |
| **MCP 서버** (신규) | AI가 자동 호출, 자연어 사용 | MCP 지원 클라이언트 필요 |

**MCP가 가장 강력한 이유**: AI가 상황에 맞게 **자동으로 적절한 도구를 선택하여 호출**합니다.
사용자는 "이 코드 괜찮아?" 라고만 물어보면 됩니다.

---

## 9. 트러블슈팅

### MCP 서버가 연결되지 않을 때

1. Python 경로 확인: `python -c "import mcp; print('OK')"`
2. 서버 단독 테스트: `python mcp_server.py` (stdio 모드로 실행되면 성공)
3. Cursor 재시작 후 Settings → MCP 확인

### 한글 깨짐 문제

`mcp.json`의 `env`에 `"PYTHONIOENCODING": "utf-8"` 설정이 있는지 확인합니다.

---

*작성일: 2026-02-12 | 팀 바이브제왕*
