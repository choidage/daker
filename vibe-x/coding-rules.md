# VIBE-X 코딩 규칙

> **팀 바이브제왕** | 버전: v1.0 | 최종 수정: 2026.02.12  
> 이 규칙은 `.cursorrules`에 자동 주입되어 모든 AI 코드 생성에 적용된다.

---

## 1. 네이밍 컨벤션

### 1.1 파일명
| 대상 | 규칙 | 예시 |
|------|------|------|
| 컴포넌트 | PascalCase | `GateRunner.tsx`, `Dashboard.tsx` |
| 유틸/헬퍼 | kebab-case | `vector-db.ts`, `gate-runner.ts` |
| 타입 정의 | kebab-case | `types.ts`, `gate-types.ts` |
| 테스트 | `*.test.ts` | `vector-db.test.ts` |
| 설정 | kebab-case | `tsconfig.json`, `.eslintrc.json` |

### 1.2 변수 및 함수
| 대상 | 규칙 | 예시 |
|------|------|------|
| 변수 | camelCase | `gateResult`, `vectorStore` |
| 상수 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| 함수 | camelCase, 동사로 시작 | `runGate()`, `fetchMetrics()` |
| 클래스 | PascalCase | `VectorSearcher`, `GateRunner` |
| 인터페이스 | PascalCase (I 접두사 금지) | `GateResult`, `TeamMetrics` |
| 타입 | PascalCase | `SearchPayload`, `AgentConfig` |
| Enum | PascalCase | `GateStatus.Passed` |
| 불리언 | is/has/should 접두사 | `isValid`, `hasConflict` |

### 1.3 디렉토리
- Layer별 디렉토리: `layer{N}-{name}/`
- 기능별 하위 디렉토리: 역할 기반 (e.g., `agents/`, `api/`)

---

## 2. 코드 스타일

### 2.1 포매터 & 린터
```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100,
  "arrowParens": "always"
}
```

### 2.2 ESLint 핵심 규칙
- `no-any`: error — any 타입 사용 금지
- `no-console`: warn — console.log 대신 logger 사용
- `no-unused-vars`: error — 미사용 변수 금지
- `prefer-const`: error — 재할당 없으면 const
- `explicit-return-type`: warn — 함수 반환 타입 명시 권장

### 2.3 TypeScript 엄격 모드
```json
// tsconfig.json 핵심
{
  "strict": true,
  "noImplicitAny": true,
  "strictNullChecks": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true
}
```

---

## 3. 금지 패턴 목록

| # | 금지 패턴 | 이유 | 대안 |
|---|----------|------|------|
| 1 | `any` 타입 | 타입 안전성 파괴 | 구체적 타입 또는 `unknown` |
| 2 | `console.log` (프로덕션) | 로그 관리 불가 | `logger.info()` 사용 |
| 3 | 매직 넘버 | 의미 불명 | 상수로 추출 |
| 4 | 중첩 콜백 3단계+ | 가독성 저하 | async/await 사용 |
| 5 | God Function (50줄+) | 단일 책임 위반 | 함수 분리 |
| 6 | 직접 API URL 하드코딩 | 환경 의존성 | config.ts에서 관리 |
| 7 | try-catch 없는 async | 에러 누락 | 반드시 에러 핸들링 |
| 8 | `!important` (CSS) | 스타일 충돌 | 구체적 선택자 사용 |
| 9 | npm install (lock 무시) | 의존성 불일치 | `pnpm install` 사용 |
| 10 | 주석 없는 복잡 로직 | 유지보수 불가 | JSDoc 또는 인라인 주석 |

---

## 4. 에러 핸들링 표준

### 4.1 에러 계층
```typescript
// 기본 에러 클래스
class VibeXError extends Error {
  constructor(
    message: string,
    public code: string,
    public context?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'VibeXError';
  }
}

// Layer별 에러
class RagError extends VibeXError { /* Layer 2 */ }
class GateError extends VibeXError { /* Layer 3 */ }
class McpError extends VibeXError { /* Layer 4 */ }
```

### 4.2 에러 핸들링 원칙
1. **에러는 발생 지점에서 가장 가까운 곳에서 처리**
2. **복구 가능하면 복구, 불가능하면 상위로 전파**
3. **모든 에러는 logger로 기록**
4. **사용자에게는 친화적 메시지, 로그에는 상세 정보**
5. **에러 코드 체계: `{LAYER}_{CATEGORY}_{DETAIL}`** (e.g., `RAG_INDEX_TIMEOUT`)

---

## 5. 보안 체크리스트

| # | 항목 | 검증 방법 |
|---|------|----------|
| 1 | API 키/시크릿은 환경변수로만 관리 | `.env` + Gate 2 자동 검사 |
| 2 | 사용자 입력은 반드시 검증/새니타이즈 | zod 스키마 검증 |
| 3 | SQL/NoSQL 인젝션 방지 | 파라미터 바인딩 필수 |
| 4 | CORS 설정 명시적으로 관리 | 허용 오리진 화이트리스트 |
| 5 | 의존성 취약점 주기적 점검 | `pnpm audit` (CI/CD 통합) |
| 6 | 에러 메시지에 내부 정보 노출 금지 | 프로덕션 에러 필터링 |
| 7 | 인증 토큰 만료 시간 설정 | JWT `exp` 필수 |
| 8 | 민감 데이터 로깅 금지 | logger 필터 적용 |

---

## 6. Git 커밋 규칙

### 6.1 커밋 메시지 형식
```
<type>(<scope>): <subject>

[body]

[footer]
```

### 6.2 Type 목록
| Type | 설명 |
|------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 스타일 (포매팅, 세미콜론 등) |
| `refactor` | 리팩토링 (기능 변경 없음) |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 의존성 등 기타 |

### 6.3 예시
```
feat(layer2-rag): add semantic search with LanceDB

- Implement vector similarity search
- Add chunking strategy for TypeScript files
- Support @Codebase context query

Closes #12
```

---

## 7. 테스트 규칙

| 항목 | 기준 |
|------|------|
| 단위 테스트 | 모든 비즈니스 로직 함수 필수 |
| 통합 테스트 | API 엔드포인트 필수 |
| 커버리지 목표 | 80%+ |
| 테스트 프레임워크 | Vitest |
| 테스트 파일 위치 | 소스 파일과 동일 디렉토리 |
| 테스트 네이밍 | `describe('모듈명') > it('should 동작')` |

---

> *규칙은 제약이 아니라, 팀이 같은 방향으로 달리기 위한 트랙이다.*
