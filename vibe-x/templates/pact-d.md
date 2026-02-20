# PACT-D 프롬프트 프레임워크

> 모든 AI 코드 생성 요청 시 이 구조를 따른다.  
> `.cursorrules`에 자동 주입되어 프롬프트 품질을 보장한다.

---

## 사용 방법

아래 템플릿을 복사하여 AI에게 작업을 요청할 때 사용한다.
각 항목을 채운 후 프롬프트에 포함시킨다.

---

## 템플릿

```
## P (Purpose) — 목적
이 코드가 해결하는 문제:
- [ ] 어떤 기능을 구현하는가?
- [ ] 어떤 사용자 문제를 해결하는가?
- [ ] 예상 입력과 출력은 무엇인가?

## A (Architecture) — 아키텍처
관련 컨텍스트:
- [ ] 관련 파일: {파일 경로 목록}
- [ ] 사용할 기존 패턴: {참조할 기존 코드}
- [ ] 참조 ADR: {관련 아키텍처 결정}
- [ ] Layer: {이 작업이 속한 Layer}

## C (Constraints) — 제약 조건
팀 규칙 준수:
- [ ] coding-rules.md의 네이밍 컨벤션 따름
- [ ] 금지 패턴 위반 없음
- [ ] TypeScript strict 모드 호환
- [ ] 보안 체크리스트 충족
- [ ] 추가 제약: {특수 제약 사항}

## T (Test) — 테스트
검증 기준:
- [ ] 성공 시나리오: {정상 동작 기대 결과}
- [ ] 실패 시나리오: {에러 상황 처리}
- [ ] 엣지 케이스: {경계값, 빈 입력 등}
- [ ] 테스트 파일 위치: {파일명.test.ts}

## D (Dependency) — 의존성
팀 작업 조율:
- [ ] 이 작업이 의존하는 모듈/작업: {목록}
- [ ] 이 작업에 의존하는 다른 작업: {목록}
- [ ] 수정 예상 파일: {파일 목록 — 충돌 방지용}
- [ ] 관련 팀원: {이름}
```

---

## 사용 예시

```
## P (Purpose)
Vector DB에서 코드 시맨틱 검색 기능 구현.
- 자연어 질의로 관련 코드 스니펫을 찾는다.
- 입력: 검색 쿼리 (string), 출력: 관련 코드 청크 배열

## A (Architecture)
- 관련 파일: src/layer2-rag/searcher.ts, src/layer2-rag/vector-db.ts
- 사용할 기존 패턴: vector-db.ts의 LanceDB 연결 패턴
- 참조 ADR: ADR-001 (LanceDB 채택 근거)
- Layer: Layer 2 (RAG Memory Engine)

## C (Constraints)
- coding-rules.md의 네이밍 컨벤션 따름
- any 타입 금지, 반환 타입 명시
- 에러 핸들링: RagError 클래스 사용
- 검색 결과 최대 10개 제한

## T (Test)
- 성공: "인증 미들웨어" 검색 → 관련 auth 코드 반환
- 실패: 빈 쿼리 → RagError('RAG_SEARCH_EMPTY_QUERY')
- 엣지: 결과 없음 → 빈 배열 반환

## D (Dependency)
- 의존: vector-db.ts (LanceDB 연결)
- 의존 받음: layer3-agents/review-agent.ts
- 수정 파일: searcher.ts, searcher.test.ts
- 관련 팀원: 백엔드 개발자
```

---

## 간소화 버전 (간단한 작업용)

```
[P] {한 줄 목적}
[A] 관련: {파일}, 패턴: {참조}, ADR: {번호}
[C] 제약: {핵심 제약}
[T] 성공: {기대 결과} / 실패: {에러 처리}
[D] 의존: {모듈} / 수정 파일: {목록}
```

---

> *PACT-D는 AI에게 "알아서 해"가 아니라 "이 맥락에서 이렇게 해"를 전달하는 구조화된 방법이다.*
