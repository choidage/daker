"""Task 3.2 - Gate 4: Review Agent.

AI 교차 코드 리뷰 - 보안 취약점, 성능 안티패턴을 자동 탐지한다.
"""

import re
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import GateResult, GateStatus

logger = get_logger("gate4")

# 보안 취약점 패턴 (OWASP 기반)
SECURITY_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("SEC-001", "하드코딩된 시크릿 의심",
     re.compile(r"""(?:password|secret|api_key|token)\s*=\s*["'][^"']{8,}["']""", re.I)),
    ("SEC-002", "eval/exec 사용 (코드 인젝션 위험)",
     re.compile(r"\b(?:eval|exec)\s*\(")),
    ("SEC-003", "SQL 인젝션 위험 (문자열 포맷 SQL)",
     re.compile(r"""(?:execute|cursor\.)\w*\(\s*f?["'].*(?:SELECT|INSERT|UPDATE|DELETE)""", re.I)),
    ("SEC-004", "subprocess shell=True (명령 인젝션)",
     re.compile(r"subprocess\.\w+\(.*shell\s*=\s*True")),
    ("SEC-005", "pickle 역직렬화 (원격 코드 실행)",
     re.compile(r"pickle\.loads?\(")),
    ("SEC-006", "assert 프로덕션 사용 (최적화 시 제거됨)",
     re.compile(r"^\s*assert\s+(?=.*\b(?:request|input|user)\b)", re.MULTILINE)),
]

# 성능 안티패턴
PERFORMANCE_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("PERF-001", "루프 내 DB/API 호출 의심 (N+1 문제)",
     re.compile(r"for\s+\w+\s+in\s+.*:\s*\n\s+.*(?:query|fetch|request|get)\(")),
    ("PERF-002", "불필요한 전체 데이터 로드",
     re.compile(r"\.(?:find|select|query)\(\s*\)(?!\s*\.limit)")),
    ("PERF-003", "동기 sleep 사용",
     re.compile(r"time\.sleep\(\s*\d{2,}")),
    ("PERF-004", "중첩 루프 3단계+ (O(n^3) 이상)",
     re.compile(r"for\s+.*:\s*\n\s+for\s+.*:\s*\n\s+for\s+")),
    ("PERF-005", "거대 리스트 복사",
     re.compile(r"list\(\w+\).*len\(.*>\s*\d{4}")),
]


MAX_FILE_LINES = 500
MAX_NESTING_DEPTH = 5
MAX_IMPORT_COUNT = 20


class ReviewAgent:
    """Gate 4: 코드 리뷰 Agent.

    보안 취약점(OWASP 기반)과 성능 안티패턴을 자동으로 탐지한다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()

    def run(self, file_path: Path) -> GateResult:
        """Gate 4를 실행한다."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return GateResult(
                gate_number=4,
                gate_name="Review Agent",
                status=GateStatus.SKIPPED,
                message=f"파일 읽기 실패: {e}",
            )

        lines = content.split("\n")
        issues: list[str] = []

        # 보안 검사
        sec_issues = self._check_security(content, lines)
        issues.extend(sec_issues)

        # 성능 검사
        perf_issues = self._check_performance(content, lines)
        issues.extend(perf_issues)

        # 코드 복잡도 검사
        complexity_issues = self._check_complexity(content, lines)
        issues.extend(complexity_issues)

        if not issues:
            return GateResult(
                gate_number=4,
                gate_name="Review Agent",
                status=GateStatus.PASSED,
                message="Gate 4 통과 - 보안/성능 이슈 없음",
            )

        sec_count = len(sec_issues)
        perf_count = len(perf_issues)
        status = GateStatus.FAILED if sec_count > 0 else GateStatus.WARNING

        return GateResult(
            gate_number=4,
            gate_name="Review Agent",
            status=status,
            message=f"Gate 4 {'실패' if status == GateStatus.FAILED else '경고'} "
                    f"- 보안:{sec_count} 성능:{perf_count} 복잡도:{len(complexity_issues)}",
            details=issues,
        )

    def _check_security(self, content: str, lines: list[str]) -> list[str]:
        """보안 취약점을 검사한다."""
        issues: list[str] = []
        for code, desc, pattern in SECURITY_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                issues.append(f"[{code}] L{line_num}: {desc}")
        return issues

    def _check_performance(self, content: str, lines: list[str]) -> list[str]:
        """성능 안티패턴을 검사한다."""
        issues: list[str] = []
        for code, desc, pattern in PERFORMANCE_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                issues.append(f"[{code}] L{line_num}: {desc}")
        return issues

    def _check_complexity(self, content: str, lines: list[str]) -> list[str]:
        """코드 복잡도를 검사한다."""
        issues: list[str] = []

        if len(lines) > MAX_FILE_LINES:
            issues.append(f"[CMPLX-001] 파일 {len(lines)}줄 - {MAX_FILE_LINES}줄 이하 권장, 모듈 분리 고려")

        # 중첩 깊이 검사
        max_indent = 0
        for i, line in enumerate(lines, 1):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                spaces = indent // 4 if "    " in line[:indent] else indent // 2
                if spaces > max_indent:
                    max_indent = spaces
                if spaces >= MAX_NESTING_DEPTH:
                    issues.append(f"[CMPLX-002] L{i}: 중첩 깊이 {spaces} - 리팩토링 권장")
                    break  # 첫 번째만 보고

        # import 수 검사
        import_count = sum(1 for line in lines if line.strip().startswith(("import ", "from ")))
        if import_count > MAX_IMPORT_COUNT:
            issues.append(f"[CMPLX-003] import {import_count}개 - 의존성 과다, 모듈 분리 고려")

        return issues
