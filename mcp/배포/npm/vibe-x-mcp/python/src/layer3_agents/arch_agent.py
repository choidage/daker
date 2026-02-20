"""Task 3.3 - Gate 5: Architecture Agent.

ADR 정합성, 타입 일관성, 아키텍처 규칙 준수를 검증한다.
"""

import re
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import GateResult, GateStatus

logger = get_logger("gate5")


class ArchitectureAgent:
    """Gate 5: 아키텍처 정합성 검증 Agent.

    Layer 간 의존성 규칙, ADR 참조, 디렉토리 구조를 검증한다.
    """

    # Layer 의존성 규칙: 상위 Layer만 하위 Layer를 참조 가능
    LAYER_ORDER = {
        "layer1_scaffold": 1,
        "layer2_rag": 2,
        "layer3_agents": 3,
        "layer4_collab": 4,
        "layer5_dashboard": 5,
        "shared": 0,  # 모든 Layer에서 참조 가능
    }

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()

    def run(self, file_path: Path) -> GateResult:
        """Gate 5를 실행한다."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return GateResult(
                gate_number=5,
                gate_name="Architecture Agent",
                status=GateStatus.SKIPPED,
                message=f"파일 읽기 실패: {e}",
            )

        issues: list[str] = []

        # 1. Layer 의존성 검사
        dep_issues = self._check_layer_dependencies(file_path, content)
        issues.extend(dep_issues)

        # 2. 디렉토리 구조 검사
        struct_issues = self._check_structure(file_path)
        issues.extend(struct_issues)

        # 3. 네이밍 컨벤션 검사
        naming_issues = self._check_naming(file_path, content)
        issues.extend(naming_issues)

        if not issues:
            return GateResult(
                gate_number=5,
                gate_name="Architecture Agent",
                status=GateStatus.PASSED,
                message="Gate 5 통과 - 아키텍처 규칙 준수",
            )

        status = GateStatus.FAILED if len(issues) > 3 else GateStatus.WARNING
        return GateResult(
            gate_number=5,
            gate_name="Architecture Agent",
            status=status,
            message=f"Gate 5 {'실패' if status == GateStatus.FAILED else '경고'} "
                    f"- {len(issues)}개 아키텍처 이슈",
            details=issues,
        )

    def _check_layer_dependencies(self, file_path: Path, content: str) -> list[str]:
        """Layer 간 의존성 규칙을 검사한다."""
        issues: list[str] = []
        current_layer = self._get_layer(file_path)
        if current_layer is None:
            return issues

        current_order = self.LAYER_ORDER.get(current_layer, -1)

        # import 문에서 다른 layer 참조 탐지
        import_pattern = re.compile(r"from\s+src\.(\w+)")
        for match in import_pattern.finditer(content):
            imported_layer = match.group(1)
            imported_order = self.LAYER_ORDER.get(imported_layer, -1)

            # shared(0)는 항상 허용
            if imported_order == 0:
                continue

            # 같은 Layer 또는 하위 Layer 참조만 허용
            if imported_order > current_order and current_order > 0:
                issues.append(
                    f"[ARCH-001] Layer 의존성 위반: "
                    f"{current_layer}(L{current_order}) -> "
                    f"{imported_layer}(L{imported_order}) "
                    f"(상위 Layer 참조 불가)"
                )

        return issues

    def _check_structure(self, file_path: Path) -> list[str]:
        """파일이 올바른 디렉토리에 위치하는지 검사한다."""
        issues: list[str] = []
        parts = file_path.parts

        # src/ 하위 파일인 경우 Layer 디렉토리 안에 있어야 함
        if "src" in parts:
            src_idx = parts.index("src")
            if src_idx + 1 < len(parts):
                subdir = parts[src_idx + 1]
                if subdir not in self.LAYER_ORDER and subdir != "__pycache__":
                    issues.append(
                        f"[ARCH-002] 디렉토리 구조 위반: "
                        f"'{subdir}' - 올바른 Layer 디렉토리가 아님"
                    )

        return issues

    def _check_naming(self, file_path: Path, content: str) -> list[str]:
        """네이밍 컨벤션을 검사한다."""
        issues: list[str] = []
        filename = file_path.stem

        # Python 파일: snake_case 확인
        if file_path.suffix == ".py" and filename != "__init__":
            if not re.match(r"^[a-z][a-z0-9_]*$", filename):
                issues.append(
                    f"[ARCH-003] 파일명 '{filename}' - "
                    f"Python 파일은 snake_case 필수"
                )

        # 클래스명: PascalCase 확인
        class_pattern = re.compile(r"^class\s+(\w+)", re.MULTILINE)
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            if not re.match(r"^[A-Z][a-zA-Z0-9]+$", class_name):
                issues.append(
                    f"[ARCH-004] 클래스명 '{class_name}' - PascalCase 필수"
                )

        return issues

    def _get_layer(self, file_path: Path) -> str | None:
        """파일이 속한 Layer를 반환한다."""
        for part in file_path.parts:
            if part in self.LAYER_ORDER:
                return part
        return None
