"""Task 3.2 - Gate 3: Integration Agent.

기존 테스트 스위트를 자동 실행하고 영향 범위를 분석한다.
변경 파일의 import 의존성을 추적하여 관련 테스트만 선별 실행한다.
"""

import ast
import re
import subprocess
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import GateResult, GateStatus

logger = get_logger("gate3")

MAX_TEST_TIMEOUT_SECONDS = 120
MAX_IMPACT_DEPTH = 3


class IntegrationAgent:
    """Gate 3: 통합 테스트 자동 실행 Agent.

    변경된 파일의 영향 범위를 분석하고,
    관련 테스트만 선별 실행하여 통과 여부를 검증한다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._project_root = self._config.paths.project_root

    def run(self, changed_files: list[Path]) -> GateResult:
        """Gate 3을 실행한다."""
        impact = self._analyze_impact(changed_files)
        test_files = self._find_related_tests(changed_files, impact)

        if not test_files:
            return GateResult(
                gate_number=3,
                gate_name="Integration Agent",
                status=GateStatus.WARNING,
                message="관련 테스트 파일 없음 - 테스트 작성 권장",
                details=[
                    f"변경: {f.name}" for f in changed_files
                ] + [
                    f"영향 범위: {len(impact)}개 모듈",
                ],
            )

        passed, failed, errors = self._run_tests(test_files)
        details = self._build_report(changed_files, impact, passed, failed, errors)

        if failed:
            return GateResult(
                gate_number=3,
                gate_name="Integration Agent",
                status=GateStatus.FAILED,
                message=f"Gate 3 실패 - {len(failed)}개 테스트 실패",
                details=details,
            )

        return GateResult(
            gate_number=3,
            gate_name="Integration Agent",
            status=GateStatus.PASSED,
            message=f"Gate 3 통과 - {len(passed)}개 테스트 성공 (영향 범위: {len(impact)}개 모듈)",
            details=details,
        )

    def _analyze_impact(self, changed_files: list[Path]) -> list[str]:
        """변경 파일의 영향 범위를 import 의존성으로 분석한다."""
        changed_modules = set()
        for f in changed_files:
            module = self._path_to_module(f)
            if module:
                changed_modules.add(module)

        affected: set[str] = set(changed_modules)
        self._find_reverse_imports(changed_modules, affected, depth=0)
        return sorted(affected)

    def _path_to_module(self, file_path: Path) -> str | None:
        """파일 경로를 Python 모듈 이름으로 변환한다."""
        try:
            rel = file_path.resolve().relative_to(self._project_root.resolve())
            parts = rel.with_suffix("").parts
            if parts:
                return ".".join(parts)
        except (ValueError, TypeError):
            pass
        return None

    def _find_reverse_imports(
        self, targets: set[str], affected: set[str], depth: int
    ) -> None:
        """targets를 import하는 파일들을 재귀적으로 탐색한다."""
        if depth >= MAX_IMPACT_DEPTH:
            return

        src_dir = self._project_root / "src"
        if not src_dir.exists():
            return

        new_targets: set[str] = set()
        for py_file in src_dir.rglob("*.py"):
            module = self._path_to_module(py_file)
            if not module or module in affected:
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for target in targets:
                short = target.split(".")[-1]
                if re.search(
                    rf"(?:from\s+{re.escape(target)}|import\s+{re.escape(target)}"
                    rf"|from\s+\S+\s+import\s+.*\b{re.escape(short)}\b)",
                    content,
                ):
                    affected.add(module)
                    new_targets.add(module)
                    break

        if new_targets:
            self._find_reverse_imports(new_targets, affected, depth + 1)

    def _find_related_tests(
        self, changed_files: list[Path], impact_modules: list[str]
    ) -> list[Path]:
        """변경 파일 + 영향 범위 기반으로 관련 테스트를 탐색한다."""
        test_files: set[Path] = set()
        tests_dir = self._project_root / "tests"

        for file_path in changed_files:
            stem = file_path.stem
            candidates = self._generate_test_candidates(file_path, stem, tests_dir)
            for c in candidates:
                if c.exists() and c not in test_files:
                    test_files.add(c)

        if tests_dir.exists():
            all_test_files = list(tests_dir.rglob("test_*.py"))
            for tf in all_test_files:
                if tf in test_files:
                    continue
                if self._test_imports_affected_module(tf, impact_modules):
                    test_files.add(tf)

        return sorted(test_files)

    def _generate_test_candidates(
        self, file_path: Path, stem: str, tests_dir: Path
    ) -> list[Path]:
        """파일에 대한 테스트 파일 후보 경로를 생성한다."""
        parent = file_path.parent
        return [
            parent / f"test_{stem}.py",
            parent / f"{stem}_test.py",
            tests_dir / f"test_{stem}.py",
            tests_dir / f"test_{stem.replace('_', '')}.py",
        ]

    def _test_imports_affected_module(
        self, test_file: Path, impact_modules: list[str]
    ) -> bool:
        """테스트 파일이 영향받는 모듈을 import하는지 확인한다."""
        try:
            content = test_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return False

        for module in impact_modules:
            parts = module.split(".")
            short_name = parts[-1] if parts else module
            if (
                f"import {module}" in content
                or f"from {module}" in content
                or f"import {short_name}" in content
                or f"from {'.'.join(parts[:-1])}" in content
            ):
                return True
        return False

    def _run_tests(
        self, test_files: list[Path]
    ) -> tuple[list[str], list[str], list[str]]:
        """테스트를 실행하고 결과를 분류한다."""
        passed: list[str] = []
        failed: list[str] = []
        errors: list[str] = []

        for test_file in test_files:
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=MAX_TEST_TIMEOUT_SECONDS,
                    cwd=str(self._project_root),
                )
                if result.returncode == 0:
                    count = self._extract_test_count(result.stdout)
                    passed.append(f"{test_file.name} ({count})")
                else:
                    summary = self._extract_failure_summary(result.stdout)
                    failed.append(f"{test_file.name}: {summary}")
            except FileNotFoundError:
                passed.append(f"{test_file.name} (pytest 미설치 - 파일 존재 확인)")
            except subprocess.TimeoutExpired:
                errors.append(f"{test_file.name}: 타임아웃 ({MAX_TEST_TIMEOUT_SECONDS}s)")
            except Exception as e:
                errors.append(f"{test_file.name}: {e}")

        return passed, failed, errors

    def _extract_test_count(self, output: str) -> str:
        """pytest 출력에서 통과 테스트 수를 추출한다."""
        match = re.search(r"(\d+)\s+passed", output)
        return f"{match.group(1)} passed" if match else "passed"

    def _extract_failure_summary(self, output: str) -> str:
        """pytest 출력에서 실패 요약을 추출한다."""
        match = re.search(r"FAILED\s+(.+?)(?:\s+-|$)", output)
        if match:
            return match.group(1).strip()[:120]
        lines = output.strip().split("\n")
        return lines[-1][:120] if lines else "테스트 실패"

    def _build_report(
        self,
        changed_files: list[Path],
        impact: list[str],
        passed: list[str],
        failed: list[str],
        errors: list[str],
    ) -> list[str]:
        """검증 결과 리포트를 생성한다."""
        report: list[str] = []
        report.append(f"[변경 파일] {len(changed_files)}개")
        for f in changed_files[:5]:
            report.append(f"  - {f.name}")

        report.append(f"[영향 범위] {len(impact)}개 모듈")
        for m in impact[:5]:
            report.append(f"  - {m}")
        if len(impact) > 5:
            report.append(f"  ... 외 {len(impact) - 5}개")

        if passed:
            report.append(f"[통과] {len(passed)}개")
            for p in passed:
                report.append(f"  ✓ {p}")

        if failed:
            report.append(f"[실패] {len(failed)}개")
            for f in failed:
                report.append(f"  ✗ {f}")

        if errors:
            report.append(f"[오류] {len(errors)}개")
            for e in errors:
                report.append(f"  ⚠ {e}")

        return report
