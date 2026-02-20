"""M5 - Project Registry.

멀티 프로젝트를 등록·관리·전환하는 레지스트리.
각 프로젝트는 독립된 config, metrics, alerts, work-zone 인스턴스를 가진다.
프로젝트별 멤버 역할(ProjectRole)로 세분화된 접근 제어를 지원한다.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from src.shared.config import VibeXConfig, PathConfig, load_config
from src.shared.logger import get_logger

logger = get_logger("registry")

REGISTRY_FILE = "projects.json"
MAX_PROJECTS = 50
MAX_MEMBERS_PER_PROJECT = 100


class ProjectRole(Enum):
    """프로젝트 스코프 역할."""
    OWNER = "owner"
    MAINTAINER = "maintainer"
    DEVELOPER = "developer"
    VIEWER = "viewer"


PROJECT_ROLE_PERMISSIONS: dict[ProjectRole, set[str]] = {
    ProjectRole.OWNER: {
        "project:manage", "project:delete",
        "member:add", "member:remove", "member:change_role",
        "gate:run", "gate:bypass", "gate:configure",
        "zone:declare", "zone:release", "zone:force_release",
        "alert:manage", "dashboard:read", "dashboard:write",
    },
    ProjectRole.MAINTAINER: {
        "member:add", "member:remove",
        "gate:run", "gate:bypass",
        "zone:declare", "zone:release", "zone:force_release",
        "alert:manage", "dashboard:read", "dashboard:write",
    },
    ProjectRole.DEVELOPER: {
        "gate:run",
        "zone:declare", "zone:release",
        "dashboard:read",
    },
    ProjectRole.VIEWER: {
        "dashboard:read",
    },
}


@dataclass
class ProjectMember:
    """프로젝트 멤버."""

    username: str
    project_role: ProjectRole
    joined_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "project_role": self.project_role.value,
            "joined_at": self.joined_at.isoformat(),
        }

    def has_permission(self, permission: str) -> bool:
        return permission in PROJECT_ROLE_PERMISSIONS.get(
            self.project_role, set(),
        )


@dataclass
class ProjectInfo:
    """프로젝트 메타데이터."""

    project_id: str
    name: str
    root_path: str
    description: str = ""
    team: list[str] = field(default_factory=list)
    members: dict[str, ProjectMember] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "root_path": self.root_path,
            "description": self.description,
            "team": self.team,
            "members": [m.to_dict() for m in self.members.values()],
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "tags": self.tags,
        }


class ProjectRegistry:
    """멀티 프로젝트 레지스트리.

    프로젝트를 등록하면 해당 프로젝트 전용 VibeXConfig가 생성되고,
    독립된 metrics/alerts/work-zone 인스턴스를 관리할 수 있다.
    """

    def __init__(self, global_config: VibeXConfig | None = None) -> None:
        self._global_config = global_config or load_config()
        self._projects: dict[str, ProjectInfo] = {}
        self._configs: dict[str, VibeXConfig] = {}
        self._persist_path = self._global_config.paths.meta_dir / REGISTRY_FILE
        self._load_from_disk()

    def register(
        self,
        project_id: str,
        name: str,
        root_path: str,
        description: str = "",
        team: list[str] | None = None,
        tags: list[str] | None = None,
        owner: str = "admin",
    ) -> dict:
        """프로젝트를 등록한다. owner를 자동으로 OWNER 멤버에 추가한다."""
        if project_id in self._projects:
            return {"success": False, "error": f"이미 등록된 프로젝트: {project_id}"}

        if len(self._projects) >= MAX_PROJECTS:
            return {"success": False, "error": f"프로젝트 상한({MAX_PROJECTS}개) 도달"}

        root = Path(root_path)
        if not root.exists():
            return {"success": False, "error": f"경로 없음: {root_path}"}

        members: dict[str, ProjectMember] = {
            owner: ProjectMember(username=owner, project_role=ProjectRole.OWNER),
        }

        team_list = team or []
        for username in team_list:
            if username not in members:
                members[username] = ProjectMember(
                    username=username,
                    project_role=ProjectRole.DEVELOPER,
                )

        info = ProjectInfo(
            project_id=project_id,
            name=name,
            root_path=str(root.resolve()),
            description=description,
            team=team_list,
            members=members,
            tags=tags or [],
        )
        self._projects[project_id] = info
        self._configs[project_id] = load_config(project_root=root)

        self._save_to_disk()
        logger.info(f"프로젝트 등록: {project_id} ({name}), owner={owner}")
        return {"success": True, "project": info.to_dict()}

    def unregister(self, project_id: str) -> dict:
        """프로젝트를 등록 해제한다 (데이터 삭제 아님)."""
        if project_id not in self._projects:
            return {"success": False, "error": "프로젝트 없음"}

        self._projects[project_id].is_active = False
        self._configs.pop(project_id, None)
        self._save_to_disk()
        logger.info(f"프로젝트 비활성화: {project_id}")
        return {"success": True}

    def get_project(self, project_id: str) -> dict | None:
        """프로젝트 정보를 반환한다."""
        info = self._projects.get(project_id)
        return info.to_dict() if info else None

    def list_projects(self, active_only: bool = True) -> list[dict]:
        """등록된 프로젝트 목록을 반환한다."""
        projects = self._projects.values()
        if active_only:
            projects = [p for p in projects if p.is_active]
        return [p.to_dict() for p in projects]

    def get_config(self, project_id: str) -> VibeXConfig | None:
        """프로젝트 전용 config를 반환한다."""
        if project_id not in self._configs:
            info = self._projects.get(project_id)
            if info and info.is_active:
                self._configs[project_id] = load_config(
                    project_root=Path(info.root_path),
                )
        return self._configs.get(project_id)

    def update_project(
        self,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        team: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """프로젝트 메타데이터를 수정한다."""
        info = self._projects.get(project_id)
        if not info:
            return {"success": False, "error": "프로젝트 없음"}

        if name is not None:
            info.name = name
        if description is not None:
            info.description = description
        if team is not None:
            info.team = team
        if tags is not None:
            info.tags = tags

        self._save_to_disk()
        return {"success": True, "project": info.to_dict()}

    # --- 멤버 관리 ---

    def add_member(
        self,
        project_id: str,
        username: str,
        project_role: ProjectRole = ProjectRole.DEVELOPER,
        requester: str = "",
    ) -> dict:
        """프로젝트에 멤버를 추가한다."""
        info = self._projects.get(project_id)
        if not info:
            return {"success": False, "error": "프로젝트 없음"}

        req_member = info.members.get(requester)
        if requester and req_member and not req_member.has_permission("member:add"):
            return {"success": False, "error": "멤버 추가 권한 없음"}

        if username in info.members:
            return {"success": False, "error": f"이미 멤버입니다: {username}"}

        if len(info.members) >= MAX_MEMBERS_PER_PROJECT:
            return {
                "success": False,
                "error": f"멤버 상한({MAX_MEMBERS_PER_PROJECT}명) 도달",
            }

        if project_role == ProjectRole.OWNER:
            return {"success": False, "error": "OWNER 역할은 직접 부여 불가"}

        member = ProjectMember(username=username, project_role=project_role)
        info.members[username] = member

        if username not in info.team:
            info.team.append(username)

        self._save_to_disk()
        logger.info(f"[{project_id}] 멤버 추가: {username} ({project_role.value})")
        return {"success": True, "member": member.to_dict()}

    def remove_member(
        self,
        project_id: str,
        username: str,
        requester: str = "",
    ) -> dict:
        """프로젝트에서 멤버를 제거한다."""
        info = self._projects.get(project_id)
        if not info:
            return {"success": False, "error": "프로젝트 없음"}

        req_member = info.members.get(requester)
        if requester and req_member and not req_member.has_permission("member:remove"):
            return {"success": False, "error": "멤버 제거 권한 없음"}

        target = info.members.get(username)
        if not target:
            return {"success": False, "error": f"멤버가 아닙니다: {username}"}

        if target.project_role == ProjectRole.OWNER:
            return {"success": False, "error": "OWNER는 제거할 수 없습니다"}

        del info.members[username]
        if username in info.team:
            info.team.remove(username)

        self._save_to_disk()
        logger.info(f"[{project_id}] 멤버 제거: {username}")
        return {"success": True}

    def change_member_role(
        self,
        project_id: str,
        username: str,
        new_role: ProjectRole,
        requester: str = "",
    ) -> dict:
        """프로젝트 멤버의 역할을 변경한다."""
        info = self._projects.get(project_id)
        if not info:
            return {"success": False, "error": "프로젝트 없음"}

        req_member = info.members.get(requester)
        if requester and req_member:
            if not req_member.has_permission("member:change_role"):
                return {"success": False, "error": "역할 변경 권한 없음"}

        target = info.members.get(username)
        if not target:
            return {"success": False, "error": f"멤버가 아닙니다: {username}"}

        if target.project_role == ProjectRole.OWNER:
            return {"success": False, "error": "OWNER 역할은 변경 불가"}

        if new_role == ProjectRole.OWNER:
            return {"success": False, "error": "OWNER로 변경 불가 (이전 필요)"}

        old_role = target.project_role
        target.project_role = new_role
        self._save_to_disk()

        logger.info(
            f"[{project_id}] 역할 변경: {username} "
            f"{old_role.value} -> {new_role.value}",
        )
        return {"success": True, "member": target.to_dict()}

    def get_member(self, project_id: str, username: str) -> dict | None:
        """프로젝트 멤버 정보를 조회한다."""
        info = self._projects.get(project_id)
        if not info:
            return None
        member = info.members.get(username)
        return member.to_dict() if member else None

    def list_members(self, project_id: str) -> list[dict]:
        """프로젝트 멤버 목록을 반환한다."""
        info = self._projects.get(project_id)
        if not info:
            return []
        return [m.to_dict() for m in info.members.values()]

    def check_project_permission(
        self,
        project_id: str,
        username: str,
        permission: str,
    ) -> bool:
        """특정 사용자가 프로젝트에서 권한을 가지는지 검사한다."""
        info = self._projects.get(project_id)
        if not info:
            return False
        member = info.members.get(username)
        if not member:
            return False
        return member.has_permission(permission)

    def transfer_ownership(
        self,
        project_id: str,
        new_owner: str,
        requester: str,
    ) -> dict:
        """프로젝트 소유권을 이전한다. 현재 OWNER만 가능."""
        info = self._projects.get(project_id)
        if not info:
            return {"success": False, "error": "프로젝트 없음"}

        req_member = info.members.get(requester)
        if not req_member or req_member.project_role != ProjectRole.OWNER:
            return {"success": False, "error": "OWNER만 소유권 이전 가능"}

        target = info.members.get(new_owner)
        if not target:
            return {"success": False, "error": f"멤버가 아닙니다: {new_owner}"}

        req_member.project_role = ProjectRole.MAINTAINER
        target.project_role = ProjectRole.OWNER
        self._save_to_disk()

        logger.info(
            f"[{project_id}] 소유권 이전: {requester} -> {new_owner}",
        )
        return {"success": True, "new_owner": target.to_dict()}

    def get_aggregate_summary(self) -> dict:
        """모든 활성 프로젝트의 집계 요약을 반환한다."""
        active = [p for p in self._projects.values() if p.is_active]
        all_members: set[str] = set()
        for p in active:
            all_members.update(p.team)

        return {
            "total_projects": len(active),
            "total_team_members": len(all_members),
            "projects": [
                {
                    "project_id": p.project_id,
                    "name": p.name,
                    "team_size": len(p.team),
                    "tags": p.tags,
                }
                for p in active
            ],
        }

    def _save_to_disk(self) -> None:
        """레지스트리를 JSON 파일에 저장한다."""
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            payload: dict[str, dict] = {}
            for pid, info in self._projects.items():
                data = info.to_dict()
                data["members"] = {
                    m.username: m.to_dict()
                    for m in info.members.values()
                }
                payload[pid] = data
            self._persist_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error(f"레지스트리 저장 실패: {exc}")

    def _load_from_disk(self) -> None:
        """저장된 레지스트리를 복원한다."""
        if not self._persist_path.exists():
            return
        try:
            raw = json.loads(self._persist_path.read_text(encoding="utf-8"))
            for pid, data in raw.items():
                members = self._parse_members(data.get("members", {}))
                info = ProjectInfo(
                    project_id=data["project_id"],
                    name=data["name"],
                    root_path=data["root_path"],
                    description=data.get("description", ""),
                    team=data.get("team", []),
                    members=members,
                    created_at=datetime.fromisoformat(data["created_at"]),
                    is_active=data.get("is_active", True),
                    tags=data.get("tags", []),
                )
                self._projects[pid] = info
                root = Path(info.root_path)
                if info.is_active and root.exists():
                    self._configs[pid] = load_config(project_root=root)
            logger.info(f"프로젝트 {len(self._projects)}개 복원 완료")
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning(f"레지스트리 복원 실패: {exc}")

    @staticmethod
    def _parse_members(
        raw: dict | list,
    ) -> dict[str, ProjectMember]:
        """JSON에서 멤버 목록을 파싱한다. dict/list 양쪽 호환."""
        members: dict[str, ProjectMember] = {}
        items = raw.values() if isinstance(raw, dict) else raw
        for entry in items:
            if isinstance(entry, dict):
                uname = entry.get("username", "")
                if not uname:
                    continue
                role_str = entry.get("project_role", "developer")
                try:
                    role = ProjectRole(role_str)
                except ValueError:
                    role = ProjectRole.DEVELOPER
                joined = datetime.now()
                if "joined_at" in entry:
                    try:
                        joined = datetime.fromisoformat(entry["joined_at"])
                    except ValueError:
                        pass
                members[uname] = ProjectMember(
                    username=uname,
                    project_role=role,
                    joined_at=joined,
                )
            elif isinstance(entry, str):
                members[entry] = ProjectMember(
                    username=entry,
                    project_role=ProjectRole.DEVELOPER,
                )
        return members
