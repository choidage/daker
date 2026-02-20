"""인증/권한 시스템 테스트."""

import time
from src.layer5_dashboard.auth import AuthManager, Role, ROLE_PERMISSIONS


class TestAuthManager:
    """AuthManager 전체 테스트."""

    def test_default_admin_exists(self, config):
        auth = AuthManager(config)
        users = auth.list_users()
        admin_users = [u for u in users if u["role"] == "admin"]
        assert len(admin_users) >= 1

    def test_login_admin(self, config):
        auth = AuthManager(config)
        result = auth.login("admin", "admin")
        assert result["success"] is True
        assert "token" in result
        assert result["user"]["role"] == "admin"

    def test_login_wrong_password(self, config):
        auth = AuthManager(config)
        result = auth.login("admin", "wrong")
        assert result["success"] is False

    def test_login_nonexistent_user(self, config):
        auth = AuthManager(config)
        result = auth.login("nobody", "pass")
        assert result["success"] is False

    def test_register_user(self, config):
        auth = AuthManager(config)
        result = auth.register_user(
            username="dev1",
            password="secret123",
            role=Role.DEVELOPER,
            display_name="Developer 1",
            email="dev1@team.com",
            requester_role=Role.ADMIN,
        )
        assert result["success"] is True
        assert result["user"]["username"] == "dev1"
        assert result["user"]["role"] == "developer"

    def test_register_duplicate_user(self, config):
        auth = AuthManager(config)
        auth.register_user("dev2", "pass123", Role.DEVELOPER, requester_role=Role.ADMIN)
        result = auth.register_user("dev2", "pass123", Role.DEVELOPER, requester_role=Role.ADMIN)
        assert result["success"] is False
        assert "이미 존재" in result["error"]

    def test_register_short_password(self, config):
        auth = AuthManager(config)
        result = auth.register_user("dev3", "ab", Role.DEVELOPER, requester_role=Role.ADMIN)
        assert result["success"] is False
        assert "6자" in result["error"]

    def test_register_by_developer_fails(self, config):
        auth = AuthManager(config)
        result = auth.register_user("dev4", "pass123", Role.DEVELOPER, requester_role=Role.DEVELOPER)
        assert result["success"] is False
        assert "권한 부족" in result["error"]

    def test_register_by_lead_ok(self, config):
        auth = AuthManager(config)
        result = auth.register_user("dev5", "pass123", Role.DEVELOPER, requester_role=Role.LEAD)
        assert result["success"] is True

    def test_lead_cannot_create_admin(self, config):
        auth = AuthManager(config)
        result = auth.register_user("dev6", "pass123", Role.ADMIN, requester_role=Role.LEAD)
        assert result["success"] is False

    def test_token_verify(self, config):
        auth = AuthManager(config)
        result = auth.login("admin", "admin")
        token = result["token"]
        payload = auth.verify_token(token)
        assert payload is not None
        assert payload.username == "admin"
        assert payload.role == "admin"
        assert not payload.is_expired()

    def test_token_invalid(self, config):
        auth = AuthManager(config)
        assert auth.verify_token("invalid.token.here") is None
        assert auth.verify_token("") is None
        assert auth.verify_token("onlyonepart") is None

    def test_check_permission_admin(self, config):
        auth = AuthManager(config)
        result = auth.login("admin", "admin")
        token = result["token"]

        assert auth.check_permission(token, "dashboard:read") is True
        assert auth.check_permission(token, "gate:bypass") is True
        assert auth.check_permission(token, "config:write") is True

    def test_check_permission_developer(self, config):
        auth = AuthManager(config)
        auth.register_user("devuser", "pass123", Role.DEVELOPER, requester_role=Role.ADMIN)
        result = auth.login("devuser", "pass123")
        token = result["token"]

        assert auth.check_permission(token, "dashboard:read") is True
        assert auth.check_permission(token, "gate:run") is True
        assert auth.check_permission(token, "gate:bypass") is False
        assert auth.check_permission(token, "config:write") is False

    def test_check_permission_viewer(self, config):
        auth = AuthManager(config)
        auth.register_user("viewer1", "pass123", Role.VIEWER, requester_role=Role.ADMIN)
        result = auth.login("viewer1", "pass123")
        token = result["token"]

        assert auth.check_permission(token, "dashboard:read") is True
        assert auth.check_permission(token, "report:read") is True
        assert auth.check_permission(token, "gate:run") is False
        assert auth.check_permission(token, "zone:declare") is False

    def test_logout_revokes_token(self, config):
        auth = AuthManager(config)
        result = auth.login("admin", "admin")
        token = result["token"]

        assert auth.verify_token(token) is not None
        auth.logout(token)
        assert auth.verify_token(token) is None

    def test_update_role(self, config):
        auth = AuthManager(config)
        auth.register_user("roleuser", "pass123", Role.DEVELOPER, requester_role=Role.ADMIN)

        result = auth.update_role("roleuser", Role.LEAD, Role.ADMIN)
        assert result["success"] is True
        assert result["user"]["role"] == "lead"

    def test_update_role_non_admin_fails(self, config):
        auth = AuthManager(config)
        auth.register_user("roleuser2", "pass123", Role.DEVELOPER, requester_role=Role.ADMIN)

        result = auth.update_role("roleuser2", Role.LEAD, Role.DEVELOPER)
        assert result["success"] is False

    def test_deactivate_user(self, config):
        auth = AuthManager(config)
        auth.register_user("deact_user", "pass123", Role.DEVELOPER, requester_role=Role.ADMIN)

        result = auth.deactivate_user("deact_user", Role.ADMIN)
        assert result["success"] is True

        # 비활성화된 사용자는 로그인 불가
        login_result = auth.login("deact_user", "pass123")
        assert login_result["success"] is False

    def test_cannot_deactivate_admin(self, config):
        auth = AuthManager(config)
        result = auth.deactivate_user("admin", Role.ADMIN)
        assert result["success"] is False

    def test_get_user(self, config):
        auth = AuthManager(config)
        user = auth.get_user("admin")
        assert user is not None
        assert user["username"] == "admin"

    def test_get_nonexistent_user(self, config):
        auth = AuthManager(config)
        assert auth.get_user("nobody") is None


class TestRolePermissions:
    """역할별 권한 정의 테스트."""

    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        assert "config:write" in admin_perms
        assert "user:manage" in admin_perms
        assert "gate:bypass" in admin_perms

    def test_viewer_minimal_permissions(self):
        viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]
        assert "dashboard:read" in viewer_perms
        assert "gate:run" not in viewer_perms
        assert "config:write" not in viewer_perms

    def test_developer_cannot_bypass_gate(self):
        dev_perms = ROLE_PERMISSIONS[Role.DEVELOPER]
        assert "gate:run" in dev_perms
        assert "gate:bypass" not in dev_perms

    def test_lead_can_force_release_zone(self):
        lead_perms = ROLE_PERMISSIONS[Role.LEAD]
        assert "zone:force_release" in lead_perms

    def test_all_roles_have_dashboard_read(self):
        for role in Role:
            assert "dashboard:read" in ROLE_PERMISSIONS[role]
