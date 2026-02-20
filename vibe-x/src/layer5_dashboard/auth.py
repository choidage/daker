"""VIBE-X 인증/권한 시스템.

팀원별 로그인, 역할 기반 접근 제어(RBAC)를 관리한다.
JWT 토큰 기반 인증 + 역할(Role) 기반 권한을 구현한다.
"""

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger

logger = get_logger("auth")


class Role(Enum):
    """팀원 역할 정의."""
    ADMIN = "admin"          # 전체 관리자 (모든 권한)
    LEAD = "lead"            # 팀 리드 (설정 변경, 리뷰 승인)
    DEVELOPER = "developer"  # 개발자 (코드 작성, 게이트 실행)
    VIEWER = "viewer"        # 뷰어 (대시보드 조회만 가능)


# 역할별 허용 작업
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "dashboard:read", "dashboard:write",
        "gate:run", "gate:bypass", "gate:configure",
        "zone:declare", "zone:release", "zone:force_release",
        "report:read", "report:generate",
        "user:manage", "config:write",
    },
    Role.LEAD: {
        "dashboard:read", "dashboard:write",
        "gate:run", "gate:bypass",
        "zone:declare", "zone:release", "zone:force_release",
        "report:read", "report:generate",
        "user:manage",
    },
    Role.DEVELOPER: {
        "dashboard:read",
        "gate:run",
        "zone:declare", "zone:release",
        "report:read",
    },
    Role.VIEWER: {
        "dashboard:read",
        "report:read",
    },
}


@dataclass
class User:
    """팀원 정보."""
    username: str
    password_hash: str
    role: Role
    display_name: str = ""
    email: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    last_login: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "role": self.role.value,
            "display_name": self.display_name or self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


@dataclass
class TokenPayload:
    """JWT 유사 토큰 페이로드."""
    username: str
    role: str
    exp: float  # 만료 Unix timestamp
    iat: float  # 발급 시간

    def is_expired(self) -> bool:
        return time.time() > self.exp


class AuthManager:
    """인증 관리자.

    기능:
    - 사용자 등록/수정/삭제
    - 비밀번호 해싱 및 검증
    - 토큰 발급/검증
    - 역할 기반 권한 검사
    """

    TOKEN_EXPIRY_HOURS = 24
    SECRET_KEY_LENGTH = 64

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._users: dict[str, User] = {}
        self._secret_key = secrets.token_hex(self.SECRET_KEY_LENGTH)
        self._revoked_tokens: set[str] = set()

        # 기본 admin 계정 생성
        self._create_default_admin()

        # 저장된 사용자 정보 로드
        self._load_users()

    def _create_default_admin(self) -> None:
        """기본 관리자 계정을 생성한다."""
        if "admin" not in self._users:
            self._users["admin"] = User(
                username="admin",
                password_hash=self._hash_password("admin"),
                role=Role.ADMIN,
                display_name="Administrator",
            )

    def register_user(
        self,
        username: str,
        password: str,
        role: Role = Role.DEVELOPER,
        display_name: str = "",
        email: str = "",
        requester_role: Role = Role.ADMIN,
    ) -> dict:
        """새 사용자를 등록한다.

        Args:
            username: 사용자 ID
            password: 비밀번호
            role: 역할 (기본: DEVELOPER)
            display_name: 표시 이름
            email: 이메일
            requester_role: 요청자의 역할 (권한 검사용)

        Returns:
            등록 결과
        """
        # 권한 검사: ADMIN 또는 LEAD만 사용자 등록 가능
        if requester_role not in (Role.ADMIN, Role.LEAD):
            return {"success": False, "error": "권한 부족: 사용자 관리 권한이 없습니다"}

        # LEAD는 ADMIN 역할 부여 불가
        if requester_role == Role.LEAD and role == Role.ADMIN:
            return {"success": False, "error": "권한 부족: ADMIN 역할 부여 불가"}

        if username in self._users:
            return {"success": False, "error": f"이미 존재하는 사용자: {username}"}

        if len(password) < 6:
            return {"success": False, "error": "비밀번호는 최소 6자 이상이어야 합니다"}

        self._users[username] = User(
            username=username,
            password_hash=self._hash_password(password),
            role=role,
            display_name=display_name or username,
            email=email,
        )

        self._save_users()
        logger.info(f"사용자 등록: {username} ({role.value})")

        return {
            "success": True,
            "user": self._users[username].to_dict(),
        }

    def login(self, username: str, password: str) -> dict:
        """로그인하여 토큰을 발급한다.

        Args:
            username: 사용자 ID
            password: 비밀번호

        Returns:
            토큰 및 사용자 정보
        """
        # 공백 제거 (입력 오류 방지)
        username = (username or "").strip()
        password = (password or "").strip()

        # 기본 계정 admin/admin 은 항상 허용 (로컬 대시보드 편의)
        if username.lower() == "admin" and password == "admin":
            if "admin" not in self._users:
                self._create_default_admin()
            user = self._users["admin"]
            if not user.is_active:
                user.is_active = True
                self._save_users()
            token = self._generate_token(user)
            user.last_login = datetime.now()
            logger.info("로그인 성공: admin (기본 계정)")
            return {
                "success": True,
                "token": token,
                "user": user.to_dict(),
            }

        # admin 계정은 대소문자 구분 없이 조회
        lookup = username if username in self._users else ("admin" if username.lower() == "admin" else None)
        user = self._users.get(lookup) if lookup else None
        if not user:
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        if not user.is_active:
            return {"success": False, "error": "비활성화된 계정입니다"}

        if not self._verify_password(password, user.password_hash):
            return {"success": False, "error": "비밀번호가 일치하지 않습니다"}

        # 토큰 생성
        token = self._generate_token(user)
        user.last_login = datetime.now()

        logger.info(f"로그인 성공: {username}")
        return {
            "success": True,
            "token": token,
            "user": user.to_dict(),
        }

    def verify_token(self, token: str) -> TokenPayload | None:
        """토큰을 검증하고 페이로드를 반환한다."""
        if token in self._revoked_tokens:
            return None

        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # 서명 검증
            header_payload = f"{parts[0]}.{parts[1]}"
            expected_sig = self._sign(header_payload)
            if not hmac.compare_digest(parts[2], expected_sig):
                return None

            # 페이로드 디코딩
            payload_json = self._b64_decode(parts[1])
            data = json.loads(payload_json)

            payload = TokenPayload(
                username=data["username"],
                role=data["role"],
                exp=data["exp"],
                iat=data["iat"],
            )

            if payload.is_expired():
                return None

            return payload

        except (json.JSONDecodeError, KeyError, IndexError):
            return None

    def check_permission(self, token: str, permission: str) -> bool:
        """토큰의 사용자가 특정 권한을 가지고 있는지 검사한다."""
        payload = self.verify_token(token)
        if not payload:
            return False

        try:
            role = Role(payload.role)
        except ValueError:
            return False

        return permission in ROLE_PERMISSIONS.get(role, set())

    def logout(self, token: str) -> bool:
        """토큰을 만료시킨다 (로그아웃)."""
        self._revoked_tokens.add(token)
        return True

    def get_user(self, username: str) -> dict | None:
        """사용자 정보를 조회한다."""
        user = self._users.get(username)
        if user:
            return user.to_dict()
        return None

    def list_users(self) -> list[dict]:
        """전체 사용자 목록을 반환한다."""
        return [u.to_dict() for u in self._users.values()]

    def update_role(self, username: str, new_role: Role, requester_role: Role) -> dict:
        """사용자 역할을 변경한다."""
        if requester_role != Role.ADMIN:
            return {"success": False, "error": "ADMIN만 역할 변경 가능"}

        user = self._users.get(username)
        if not user:
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        old_role = user.role
        user.role = new_role
        self._save_users()

        logger.info(f"역할 변경: {username} {old_role.value} -> {new_role.value}")
        return {"success": True, "user": user.to_dict()}

    def deactivate_user(self, username: str, requester_role: Role) -> dict:
        """사용자를 비활성화한다."""
        if requester_role not in (Role.ADMIN, Role.LEAD):
            return {"success": False, "error": "권한 부족"}

        if username == "admin":
            return {"success": False, "error": "기본 관리자 계정은 비활성화할 수 없습니다"}

        user = self._users.get(username)
        if not user:
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        user.is_active = False
        self._save_users()
        return {"success": True}

    def activate_user(self, username: str, requester_role: Role) -> dict:
        """사용자를 활성화한다."""
        if requester_role not in (Role.ADMIN, Role.LEAD):
            return {"success": False, "error": "권한 부족"}

        user = self._users.get(username)
        if not user:
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        user.is_active = True
        self._save_users()
        logger.info(f"사용자 활성화: {username}")
        return {"success": True, "user": user.to_dict()}

    def update_user_info(
        self,
        username: str,
        display_name: str | None = None,
        email: str | None = None,
        requester_role: Role = Role.ADMIN,
    ) -> dict:
        """사용자 정보(표시이름, 이메일)를 수정한다."""
        if requester_role not in (Role.ADMIN, Role.LEAD):
            return {"success": False, "error": "권한 부족"}

        user = self._users.get(username)
        if not user:
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        if display_name is not None:
            user.display_name = display_name
        if email is not None:
            user.email = email

        self._save_users()
        logger.info(f"사용자 정보 수정: {username}")
        return {"success": True, "user": user.to_dict()}

    def reset_password(
        self, username: str, new_password: str, requester_role: Role
    ) -> dict:
        """비밀번호를 초기화한다. (ADMIN만 가능)"""
        if requester_role != Role.ADMIN:
            return {"success": False, "error": "ADMIN만 비밀번호 초기화 가능"}

        user = self._users.get(username)
        if not user:
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        if len(new_password) < 6:
            return {"success": False, "error": "비밀번호는 최소 6자 이상"}

        user.password_hash = self._hash_password(new_password)
        self._save_users()
        logger.info(f"비밀번호 초기화: {username}")
        return {"success": True}

    def delete_user(self, username: str, requester_role: Role) -> dict:
        """사용자를 완전히 삭제한다. (ADMIN만 가능)"""
        if requester_role != Role.ADMIN:
            return {"success": False, "error": "ADMIN만 사용자 삭제 가능"}

        if username == "admin":
            return {"success": False, "error": "기본 관리자 계정은 삭제할 수 없습니다"}

        user = self._users.get(username)
        if not user:
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        del self._users[username]
        self._save_users()
        logger.info(f"사용자 삭제: {username}")
        return {"success": True}

    # --- 프로젝트 스코프 권한 ---

    def resolve_project_permission(
        self,
        token: str,
        project_id: str,
        permission: str,
        registry: object | None = None,
    ) -> dict:
        """전역 역할 + 프로젝트 멤버 역할을 종합하여 권한을 판정한다.

        판정 우선순위:
        1. 전역 ADMIN → 모든 프로젝트에서 모든 권한 허용
        2. 프로젝트 멤버이면 프로젝트 역할로 권한 판정
        3. 전역 역할이 LEAD 이상이면 dashboard:read 허용
        4. 그 외 → 거부

        Returns:
            {"allowed": bool, "reason": str, "global_role": str, "project_role": str | None}
        """
        payload = self.verify_token(token)
        if not payload:
            return {
                "allowed": False,
                "reason": "유효하지 않은 토큰",
                "global_role": "",
                "project_role": None,
            }

        username = payload.username
        global_role_str = payload.role

        try:
            global_role = Role(global_role_str)
        except ValueError:
            return {
                "allowed": False,
                "reason": f"알 수 없는 전역 역할: {global_role_str}",
                "global_role": global_role_str,
                "project_role": None,
            }

        if global_role == Role.ADMIN:
            return {
                "allowed": True,
                "reason": "전역 ADMIN",
                "global_role": global_role_str,
                "project_role": "owner",
            }

        project_role_str: str | None = None
        project_allowed = False

        if registry is not None:
            from src.layer5_dashboard.project_registry import ProjectRegistry
            if isinstance(registry, ProjectRegistry):
                member_data = registry.get_member(project_id, username)
                if member_data:
                    project_role_str = member_data.get("project_role")
                    project_allowed = registry.check_project_permission(
                        project_id, username, permission,
                    )

        if project_allowed:
            return {
                "allowed": True,
                "reason": f"프로젝트 멤버 ({project_role_str})",
                "global_role": global_role_str,
                "project_role": project_role_str,
            }

        if project_role_str:
            return {
                "allowed": False,
                "reason": f"프로젝트 역할 {project_role_str}에 {permission} 권한 없음",
                "global_role": global_role_str,
                "project_role": project_role_str,
            }

        if global_role in (Role.LEAD,) and permission == "dashboard:read":
            return {
                "allowed": True,
                "reason": "전역 LEAD - 대시보드 읽기 허용",
                "global_role": global_role_str,
                "project_role": None,
            }

        return {
            "allowed": False,
            "reason": "프로젝트 멤버가 아닙니다",
            "global_role": global_role_str,
            "project_role": None,
        }

    # --- 내부 메서드 ---

    def _hash_password(self, password: str) -> str:
        """비밀번호를 SHA-256으로 해싱한다."""
        salt = "vibe-x-salt-2024"
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """비밀번호를 검증한다."""
        return hmac.compare_digest(
            self._hash_password(password),
            password_hash,
        )

    def _generate_token(self, user: User) -> str:
        """JWT 유사 토큰을 생성한다."""
        header = self._b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}))

        now = time.time()
        payload = self._b64_encode(json.dumps({
            "username": user.username,
            "role": user.role.value,
            "iat": now,
            "exp": now + (self.TOKEN_EXPIRY_HOURS * 3600),
        }))

        signature = self._sign(f"{header}.{payload}")
        return f"{header}.{payload}.{signature}"

    def _sign(self, data: str) -> str:
        """HMAC-SHA256 서명을 생성한다."""
        return hmac.new(
            self._secret_key.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _b64_encode(self, data: str) -> str:
        """Base64 URL-safe 인코딩."""
        import base64
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")

    def _b64_decode(self, data: str) -> str:
        """Base64 URL-safe 디코딩."""
        import base64
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data.encode()).decode()

    def _save_users(self) -> None:
        """사용자 정보를 파일에 저장한다."""
        state_dir = self._config.paths.vibe_x_root / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_dir / "users.json"

        data = {}
        for username, user in self._users.items():
            data[username] = {
                "password_hash": user.password_hash,
                "role": user.role.value,
                "display_name": user.display_name,
                "email": user.email,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
            }

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_users(self) -> None:
        """저장된 사용자 정보를 로드한다."""
        path = self._config.paths.vibe_x_root / ".state" / "users.json"
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for username, info in data.items():
                if username not in self._users:
                    self._users[username] = User(
                        username=username,
                        password_hash=info["password_hash"],
                        role=Role(info["role"]),
                        display_name=info.get("display_name", ""),
                        email=info.get("email", ""),
                        is_active=info.get("is_active", True),
                    )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"사용자 정보 로드 실패: {e}")
