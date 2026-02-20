"""Task 3.3 - Gate 6: Collision Agent.

팀원 작업 간 충돌을 사전에 감지하고 경고한다.
"""

from datetime import datetime
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import GateResult, GateStatus

logger = get_logger("gate6")


class CollisionAgent:
    """Gate 6: 팀 작업 충돌 감지 Agent.

    파일 수준/함수 수준에서 팀원 간 동시 수정을 감지한다.
    Work Zone 데이터를 참조하여 충돌 가능성을 판단한다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        # 활성 작업 영역: {팀원: [파일 목록]}
        self._zones: dict[str, dict] = {}

    def run(self, changed_files: list[Path], author: str = "current") -> GateResult:
        """Gate 6을 실행한다.

        Args:
            changed_files: 변경 예정 파일 목록
            author: 작업자 식별자

        Returns:
            충돌 감지 결과
        """
        issues: list[str] = []
        changed_set = {str(f) for f in changed_files}

        # 다른 팀원의 작업 영역과 겹치는지 확인
        for member, zone_info in self._zones.items():
            if member == author:
                continue

            if not zone_info.get("active", False):
                continue

            member_files = set(zone_info.get("files", []))
            overlap = changed_set & member_files

            if overlap:
                for file_path in sorted(overlap):
                    issues.append(
                        f"[COLLISION] '{file_path}' - "
                        f"'{member}'도 수정 중 (선언 시각: {zone_info.get('declared_at', '?')})"
                    )

        if not issues:
            return GateResult(
                gate_number=6,
                gate_name="Collision Agent",
                status=GateStatus.PASSED,
                message="Gate 6 통과 - 충돌 없음",
            )

        return GateResult(
            gate_number=6,
            gate_name="Collision Agent",
            status=GateStatus.WARNING,
            message=f"Gate 6 경고 - {len(issues)}개 파일 충돌 감지",
            details=issues,
        )

    def declare_zone(self, author: str, files: list[str]) -> dict:
        """작업 영역을 선언한다.

        Args:
            author: 작업자 식별자
            files: 수정 예정 파일 경로 목록

        Returns:
            충돌 정보 (겹치는 파일 목록)
        """
        now = datetime.now().isoformat()
        conflicts: dict[str, list[str]] = {}

        # 기존 영역과 충돌 확인
        new_set = set(files)
        for member, zone_info in self._zones.items():
            if member == author or not zone_info.get("active", False):
                continue

            member_files = set(zone_info.get("files", []))
            overlap = new_set & member_files
            if overlap:
                conflicts[member] = sorted(overlap)

        # 영역 등록
        self._zones[author] = {
            "files": files,
            "declared_at": now,
            "active": True,
        }

        if conflicts:
            logger.warning(f"작업 영역 충돌 감지: {author} vs {list(conflicts.keys())}")
        else:
            logger.info(f"작업 영역 선언: {author} - {len(files)}개 파일")

        return {"author": author, "files": files, "conflicts": conflicts}

    def release_zone(self, author: str) -> bool:
        """작업 영역을 해제한다."""
        if author in self._zones:
            self._zones[author]["active"] = False
            logger.info(f"작업 영역 해제: {author}")
            return True
        return False

    def get_active_zones(self) -> dict[str, dict]:
        """활성 작업 영역 목록을 반환한다."""
        return {
            k: v for k, v in self._zones.items() if v.get("active", False)
        }
