"""Task 3.4 - Work Zone Isolation.

팀원별 작업 영역을 선언/공유/조율하는 협업 모듈.
MCP를 통해 실시간으로 전체 팀에 공유된다.
"""

import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.layer4_collab.mcp_server import McpServer, McpMessage, MessageType

logger = get_logger("workzone")


@dataclass
class WorkZone:
    """팀원의 작업 영역 정보."""
    author: str
    files: list[str]
    description: str = ""
    declared_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "author": self.author,
            "files": self.files,
            "description": self.description,
            "declared_at": self.declared_at.isoformat(),
            "is_active": self.is_active,
        }


class WorkZoneManager:
    """작업 영역 관리자.

    팀원이 작업 시작 시 수정 예정 파일을 선언하면,
    MCP를 통해 전체 팀에 공유하고 영역 중복을 감지한다.
    """

    def __init__(
        self,
        mcp: McpServer | None = None,
        config: VibeXConfig | None = None,
    ) -> None:
        self._config = config or load_config()
        self._mcp = mcp
        self._zones: dict[str, WorkZone] = {}
        self._history: list[dict] = []

    def declare(self, author: str, files: list[str], description: str = "") -> dict:
        """작업 영역을 선언한다.

        Args:
            author: 작업자 식별자
            files: 수정 예정 파일 경로 목록
            description: 작업 설명

        Returns:
            선언 결과 (충돌 정보 포함)
        """
        zone = WorkZone(author=author, files=files, description=description)
        conflicts = self._detect_overlap(author, files)

        self._zones[author] = zone

        # MCP를 통해 팀 전체에 알림
        if self._mcp:
            self._mcp.publish(McpMessage(
                msg_type=MessageType.ZONE_DECLARE,
                sender=author,
                payload=zone.to_dict(),
            ))

        result = {
            "status": "declared",
            "author": author,
            "file_count": len(files),
            "conflicts": conflicts,
        }

        self._history.append({
            "action": "declare",
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })

        if conflicts:
            logger.warning(f"작업 영역 충돌: {author} - {len(conflicts)}건")
        else:
            logger.info(f"작업 영역 선언: {author} - {len(files)}개 파일")

        return result

    def release(self, author: str) -> bool:
        """작업 영역을 해제한다."""
        zone = self._zones.get(author)
        if not zone or not zone.is_active:
            return False

        zone.is_active = False

        if self._mcp:
            self._mcp.publish(McpMessage(
                msg_type=MessageType.ZONE_RELEASE,
                sender=author,
                payload={"author": author},
            ))

        self._history.append({
            "action": "release",
            "author": author,
            "timestamp": datetime.now().isoformat(),
        })

        logger.info(f"작업 영역 해제: {author}")
        return True

    def get_active_zones(self) -> dict[str, WorkZone]:
        """활성 작업 영역을 조회한다."""
        return {k: v for k, v in self._zones.items() if v.is_active}

    def get_zone_map(self) -> dict[str, list[str]]:
        """파일별 작업자 매핑을 반환한다.

        Returns:
            {파일경로: [작업자 목록]}
        """
        file_map: dict[str, list[str]] = {}
        for author, zone in self._zones.items():
            if not zone.is_active:
                continue
            for f in zone.files:
                file_map.setdefault(f, []).append(author)
        return file_map

    def save_state(self) -> Path:
        """현재 상태를 JSON 파일로 저장한다."""
        state_dir = self._config.paths.vibe_x_root / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / "work_zones.json"

        data = {
            "zones": {k: v.to_dict() for k, v in self._zones.items()},
            "saved_at": datetime.now().isoformat(),
        }

        state_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return state_path

    def _detect_overlap(self, author: str, files: list[str]) -> list[dict]:
        """다른 팀원의 작업 영역과 겹치는 파일을 감지한다."""
        conflicts: list[dict] = []
        new_set = set(files)

        for member, zone in self._zones.items():
            if member == author or not zone.is_active:
                continue

            overlap = new_set & set(zone.files)
            if overlap:
                conflicts.append({
                    "conflicting_author": member,
                    "overlapping_files": sorted(overlap),
                    "their_description": zone.description,
                })

        return conflicts
