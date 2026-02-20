"""Task 2.4 - 기본 품질 게이트 (Gate 1, 2).

커밋 시점에 자동 실행되는 기본 코드 검증.
Gate 1: 문법/구조 검사
Gate 2: 팀 코딩 규칙 준수 검사
"""

import re
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import GateResult, GateStatus

logger = get_logger("gate")


class BasicGate:
    """Gate 1 + Gate 2 기본 품질 검증기.

    Gate 1 (Syntax): 파일 구조, 인코딩, 기본 문법 검사
    Gate 2 (Rules): coding-rules.md 기반 규칙 준수 검사
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()

    def run_gate1(self, file_path: Path) -> GateResult:
        """Gate 1: Syntax Agent - 기본 문법/구조 검사."""
        issues: list[str] = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return GateResult(
                gate_number=1,
                gate_name="Syntax Agent",
                status=GateStatus.FAILED,
                message=f"인코딩 오류: {file_path}",
            )

        lines = content.split("\n")

        # 빈 파일 검사
        if not content.strip():
            issues.append("빈 파일")

        # 초장문 라인 검사 (200자 초과)
        for i, line in enumerate(lines, 1):
            if len(line) > 200:
                issues.append(f"L{i}: 라인 길이 {len(line)}자 (200자 초과)")

        # 탭/스페이스 혼용 검사
        has_tabs = any("\t" in line for line in lines)
        has_spaces = any(line.startswith("  ") for line in lines)
        if has_tabs and has_spaces:
            issues.append("탭과 스페이스 인덴트 혼용")

        # trailing whitespace 검사
        trailing_count = sum(
            1 for line in lines if line != line.rstrip() and line.strip()
        )
        if trailing_count > 5:
            issues.append(f"trailing whitespace: {trailing_count}개 라인")

        status = GateStatus.PASSED if not issues else GateStatus.WARNING
        return GateResult(
            gate_number=1,
            gate_name="Syntax Agent",
            status=status,
            message=f"Gate 1 {'통과' if not issues else f'{len(issues)}개 이슈'}",
            details=issues,
        )

    def run_gate2(self, file_path: Path) -> GateResult:
        """Gate 2: Rules Agent - 팀 코딩 규칙 준수 검사."""
        issues: list[str] = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return GateResult(
                gate_number=2,
                gate_name="Rules Agent",
                status=GateStatus.SKIPPED,
                message=f"파일 읽기 불가: {file_path}",
            )

        lines = content.split("\n")
        suffix = file_path.suffix

        # 금지 패턴 검사
        for pattern in self._config.gate.forbidden_patterns:
            for i, line in enumerate(lines, 1):
                if pattern in line:
                    issues.append(f"L{i}: 금지 패턴 '{pattern}' 발견")

        # Python/TypeScript 전용 검사
        if suffix in (".py", ".ts", ".tsx", ".js", ".jsx"):
            issues.extend(self._check_code_rules(lines, suffix))

        # 함수 길이 검사
        issues.extend(self._check_function_length(lines, suffix))

        if not issues:
            status = GateStatus.PASSED
            message = "Gate 2 통과 - 규칙 준수 확인"
        elif len(issues) <= 3:
            status = GateStatus.WARNING
            message = f"Gate 2 경고 - {len(issues)}개 이슈"
        else:
            status = GateStatus.FAILED
            message = f"Gate 2 실패 - {len(issues)}개 규칙 위반"

        return GateResult(
            gate_number=2,
            gate_name="Rules Agent",
            status=status,
            message=message,
            details=issues,
        )

    def run_all(self, file_path: Path) -> list[GateResult]:
        """Gate 1 + Gate 2를 순차 실행한다."""
        return [self.run_gate1(file_path), self.run_gate2(file_path)]

    def _check_code_rules(self, lines: list[str], suffix: str) -> list[str]:
        """코드 파일 전용 규칙을 검사한다."""
        issues: list[str] = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 매직 넘버 검사 (단독 숫자 사용)
            if re.search(r"[=<>]\s*\d{3,}", stripped) and "port" not in stripped.lower():
                issues.append(f"L{i}: 매직 넘버 의심 - 상수로 추출 권장")

            # any 타입 검사 (TypeScript)
            if suffix in (".ts", ".tsx") and ": any" in stripped:
                issues.append(f"L{i}: 'any' 타입 사용 - 구체적 타입 또는 'unknown' 사용")

        return issues

    def _check_function_length(self, lines: list[str], suffix: str) -> list[str]:
        """함수 길이 제한을 검사한다."""
        issues: list[str] = []
        max_lines = self._config.gate.max_function_lines

        # Python 함수 길이 검사
        if suffix == ".py":
            func_start: int | None = None
            func_name = ""
            indent_level = 0

            for i, line in enumerate(lines):
                match = re.match(r"^(\s*)(async\s+)?def\s+(\w+)", line)
                if match:
                    if func_start is not None:
                        length = i - func_start
                        if length > max_lines:
                            issues.append(
                                f"L{func_start + 1}: '{func_name}' 함수 "
                                f"{length}줄 (최대 {max_lines}줄)"
                            )
                    func_start = i
                    func_name = match.group(3)
                    indent_level = len(match.group(1))

        return issues
