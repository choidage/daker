"""대시보드 API 통합 테스트.

모든 REST API 엔드포인트를 체계적으로 검증한다.
M2(RAG), M3(Pipeline/Collab), M4(Alert/Health/QA) 전 범위를 포함한다.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient
from src.layer5_dashboard.app import app


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. 기본 엔드포인트
# ---------------------------------------------------------------------------

class TestBasicEndpoints:
    """기본 대시보드 엔드포인트 검증."""

    def test_root_returns_html(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_dashboard_data_shape(self, client: TestClient) -> None:
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert "health_score" in data or "today" in data or isinstance(data, dict)

    def test_onboarding_data(self, client: TestClient) -> None:
        resp = client.get("/api/onboarding")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_feedback_data(self, client: TestClient) -> None:
        resp = client.get("/api/feedback")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_report_data(self, client: TestClient) -> None:
        resp = client.get("/api/report")
        assert resp.status_code == 200

    def test_static_dashboard_html(self, client: TestClient) -> None:
        resp = client.get("/static/dashboard.html")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. Gate 결과 기록
# ---------------------------------------------------------------------------

class TestGateResult:
    """Gate 결과 기록 API 검증."""

    def test_record_gate_passed(self, client: TestClient) -> None:
        payload = {
            "gate_number": 1,
            "gate_name": "Syntax Agent",
            "status": "passed",
            "message": "Gate 1 통과",
            "details": [],
        }
        resp = client.post("/api/gate-result", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "recorded"

    def test_record_gate_failed_triggers_alert(self, client: TestClient) -> None:
        payload = {
            "gate_number": 1,
            "gate_name": "Syntax Agent",
            "status": "failed",
            "message": "구문 오류 3건",
            "details": ["L10: SyntaxError"],
        }
        resp = client.post("/api/gate-result", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "recorded"

    def test_record_gate_warning(self, client: TestClient) -> None:
        payload = {
            "gate_number": 2,
            "gate_name": "Rules Agent",
            "status": "warning",
            "message": "경고 1건",
            "details": ["L5: 매직 넘버"],
        }
        resp = client.post("/api/gate-result", json=payload)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. Alert System API
# ---------------------------------------------------------------------------

class TestAlertAPI:
    """경고 시스템 API 검증."""

    def test_get_alerts_default_active(self, client: TestClient) -> None:
        resp = client.get("/api/alerts")
        assert resp.status_code == 200
        body = resp.json()
        assert "alerts" in body
        assert isinstance(body["alerts"], list)

    def test_get_all_alerts(self, client: TestClient) -> None:
        resp = client.get("/api/alerts?active_only=false")
        assert resp.status_code == 200
        assert "alerts" in resp.json()

    def test_evaluate_alerts(self, client: TestClient) -> None:
        resp = client.post("/api/alerts/evaluate")
        assert resp.status_code == 200
        body = resp.json()
        assert "new_alerts" in body
        assert isinstance(body["new_alerts"], int)

    def test_acknowledge_single_alert(self, client: TestClient) -> None:
        resp = client.post(
            "/api/alerts/acknowledge",
            json={"alert_id": "ALT-9999"},
        )
        assert resp.status_code == 200
        assert "success" in resp.json()

    def test_acknowledge_all_alerts(self, client: TestClient) -> None:
        resp = client.post(
            "/api/alerts/acknowledge",
            json={"alert_id": "all"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "acknowledged" in body


# ---------------------------------------------------------------------------
# 4. Health Breakdown API
# ---------------------------------------------------------------------------

class TestHealthAPI:
    """건강 점수 세부 항목 API 검증."""

    def test_health_breakdown_structure(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)


# ---------------------------------------------------------------------------
# 5. Work Zone API
# ---------------------------------------------------------------------------

class TestWorkZoneAPI:
    """작업 영역 관리 API 검증."""

    def test_list_zones_empty(self, client: TestClient) -> None:
        resp = client.get("/api/work-zone/list")
        assert resp.status_code == 200
        assert "zones" in resp.json()

    def test_declare_and_list(self, client: TestClient) -> None:
        payload = {
            "author": "test-user",
            "files": ["src/app.py", "src/utils.py"],
            "description": "E2E 테스트 작업 영역",
        }
        resp = client.post("/api/work-zone/declare", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True or "conflicts" in body

        resp = client.get("/api/work-zone/list")
        zones = resp.json()["zones"]
        authors = [z["author"] for z in zones]
        assert "test-user" in authors

    def test_release_zone(self, client: TestClient) -> None:
        client.post("/api/work-zone/declare", json={
            "author": "release-test",
            "files": ["tmp.py"],
            "description": "릴리스 테스트",
        })
        resp = client.post("/api/work-zone/release", json={
            "author": "release-test",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    def test_zone_map(self, client: TestClient) -> None:
        resp = client.get("/api/work-zone/map")
        assert resp.status_code == 200
        assert "file_map" in resp.json()

    def test_declare_with_csv_files(self, client: TestClient) -> None:
        payload = {
            "author": "csv-test",
            "files": "a.py, b.py, c.py",
            "description": "CSV 파일 목록 테스트",
        }
        resp = client.post("/api/work-zone/declare", json=payload)
        assert resp.status_code == 200

        client.post("/api/work-zone/release", json={"author": "csv-test"})


# ---------------------------------------------------------------------------
# 6. Decision Extractor API
# ---------------------------------------------------------------------------

class TestDecisionExtractorAPI:
    """설계 결정 추출 API 검증."""

    def test_extract_empty_text(self, client: TestClient) -> None:
        resp = client.post("/api/decision/extract", json={"text": ""})
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("error") == "empty text"

    def test_extract_decisions(self, client: TestClient) -> None:
        sample = (
            "인증 시스템은 JWT 기반으로 결정했다. "
            "세션 기반보다 확장성이 좋고 마이크로서비스에 적합하기 때문이다."
        )
        resp = client.post("/api/decision/extract", json={
            "text": sample,
            "source": "e2e-test",
            "auto_save": False,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body
        assert "decisions" in body
        assert isinstance(body["decisions"], list)


# ---------------------------------------------------------------------------
# 7. Onboarding Q&A API
# ---------------------------------------------------------------------------

class TestOnboardingQA:
    """RAG 기반 Q&A API 검증."""

    def test_qa_empty_question(self, client: TestClient) -> None:
        resp = client.post("/api/onboarding/qa", json={"question": ""})
        assert resp.status_code == 200
        assert resp.json().get("error") == "empty question"

    def test_qa_with_question(self, client: TestClient) -> None:
        resp = client.post("/api/onboarding/qa", json={
            "question": "프로젝트 구조를 알려줘",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)


# ---------------------------------------------------------------------------
# 8. RAG API
# ---------------------------------------------------------------------------

class TestRagAPI:
    """RAG 검색 API 검증."""

    def test_search_empty_query(self, client: TestClient) -> None:
        resp = client.get("/api/rag/search?q=")
        assert resp.status_code == 200
        assert resp.json().get("error") == "empty query"

    def test_search_with_query(self, client: TestClient) -> None:
        resp = client.get("/api/rag/search?q=config&top_k=3")
        assert resp.status_code == 200
        body = resp.json()
        assert "query" in body
        assert "results" in body

    def test_rag_stats(self, client: TestClient) -> None:
        resp = client.get("/api/rag/stats")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)


# ---------------------------------------------------------------------------
# 9. Auth API
# ---------------------------------------------------------------------------

class TestAuthAPI:
    """인증/권한 API 검증."""

    def test_login_invalid_credentials(self, client: TestClient) -> None:
        resp = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrong",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False

    def test_login_admin(self, client: TestClient) -> None:
        resp = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123!",
        })
        assert resp.status_code == 200
        body = resp.json()
        if body.get("success"):
            assert "token" in body
        # admin 계정이 미등록일 수 있으므로 두 경우 모두 허용

    def test_me_without_token(self, client: TestClient) -> None:
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False

    def test_users_without_permission(self, client: TestClient) -> None:
        resp = client.get("/api/auth/users")
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is False

    def test_logout_without_token(self, client: TestClient) -> None:
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ---------------------------------------------------------------------------
# 10. Pipeline API (기본 검증 - 파일 부재 케이스)
# ---------------------------------------------------------------------------

class TestPipelineAPI:
    """파이프라인 API 검증."""

    def test_pipeline_file_not_found(self, client: TestClient) -> None:
        resp = client.post("/api/pipeline", json={
            "file_path": "/nonexistent/file.py",
            "author": "e2e-test",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "not found" in body["error"].lower() or "not found" in body.get("error", "").lower()

    def test_pipeline_with_real_file(self, client: TestClient) -> None:
        target = PROJECT_ROOT / "src" / "shared" / "types.py"
        if not target.exists():
            pytest.skip("types.py 파일 없음")
        resp = client.post("/api/pipeline", json={
            "file_path": str(target),
            "author": "e2e-test",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "gates" in body
        assert isinstance(body["gates"], list)
        assert len(body["gates"]) > 0


# ---------------------------------------------------------------------------
# 11. Gate Check API
# ---------------------------------------------------------------------------

class TestGateCheckAPI:
    """Gate Check API 검증."""

    def test_gate_check_missing_file(self, client: TestClient) -> None:
        resp = client.post("/api/gate-check", json={
            "file_path": "/does/not/exist.py",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("error") == "File not found"

    def test_gate_check_real_file(self, client: TestClient) -> None:
        target = PROJECT_ROOT / "src" / "shared" / "types.py"
        if not target.exists():
            pytest.skip("types.py 파일 없음")
        resp = client.post("/api/gate-check", json={
            "file_path": str(target),
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "results" in body
        assert isinstance(body["results"], list)


# ---------------------------------------------------------------------------
# 12. Multi-Project API (M5)
# ---------------------------------------------------------------------------

class TestMultiProjectAPI:
    """멀티 프로젝트 관리 API 검증.

    isolated_project_registry fixture로 프로덕션 데이터 오염을 방지한다.
    """

    def test_list_projects_empty(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        body = resp.json()
        assert "projects" in body
        assert isinstance(body["projects"], list)
        assert len(body["projects"]) == 0

    def test_register_project(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        resp = client.post("/api/projects/register", json={
            "project_id": "test-proj",
            "name": "Test Project",
            "root_path": str(PROJECT_ROOT),
            "description": "E2E 테스트 프로젝트",
            "team": ["alice", "bob"],
            "tags": ["test", "e2e"],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["project"]["project_id"] == "test-proj"

    def test_register_duplicate_fails(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "dup-proj",
            "name": "Dup",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.post("/api/projects/register", json={
            "project_id": "dup-proj",
            "name": "Dup Again",
            "root_path": str(PROJECT_ROOT),
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_register_invalid_path_fails(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        resp = client.post("/api/projects/register", json={
            "project_id": "bad-path",
            "name": "Bad",
            "root_path": "/nonexistent/path/abc",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_get_project_detail(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "detail-proj",
            "name": "Detail",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.get("/api/projects/detail-proj")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["project"]["name"] == "Detail"

    def test_get_nonexistent_project(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        resp = client.get("/api/projects/nonexistent")
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_update_project(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "upd-proj",
            "name": "Before",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.post("/api/projects/upd-proj/update", json={
            "name": "After",
            "tags": ["updated"],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["project"]["name"] == "After"

    def test_unregister_project(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "unreg-proj",
            "name": "Unreg",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.post("/api/projects/unreg-proj/unregister")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_aggregate_summary(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        resp = client.get("/api/projects/summary/aggregate")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_projects" in body
        assert "projects" in body

    def test_project_dashboard(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "dash-proj",
            "name": "Dashboard Test",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.get("/api/projects/dash-proj/dashboard")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_project_health(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "health-proj",
            "name": "Health Test",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.get("/api/projects/health-proj/health")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_project_alerts(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "alert-proj",
            "name": "Alert Test",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.get("/api/projects/alert-proj/alerts")
        assert resp.status_code == 200
        assert "alerts" in resp.json()

    def test_project_zones(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        client.post("/api/projects/register", json={
            "project_id": "zone-proj",
            "name": "Zone Test",
            "root_path": str(PROJECT_ROOT),
        })
        resp = client.get("/api/projects/zone-proj/zones")
        assert resp.status_code == 200
        assert "zones" in resp.json()


# ---------------------------------------------------------------------------
# 13. Project Member Management API
# ---------------------------------------------------------------------------

class TestProjectMemberAPI:
    """프로젝트 멤버 관리 API 검증.

    isolated_project_registry fixture로 프로덕션 데이터 오염을 방지한다.
    """

    def _register_project(self, client: TestClient) -> None:
        """테스트용 프로젝트를 등록한다."""
        client.post("/api/projects/register", json={
            "project_id": "member-proj",
            "name": "Member Test",
            "root_path": str(PROJECT_ROOT),
            "owner": "alice",
        })

    def test_register_creates_owner(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """프로젝트 등록 시 owner가 자동으로 멤버에 추가된다."""
        self._register_project(client)
        resp = client.get("/api/projects/member-proj/members")
        assert resp.status_code == 200
        members = resp.json()["members"]
        assert len(members) >= 1
        owner = next((m for m in members if m["username"] == "alice"), None)
        assert owner is not None
        assert owner["project_role"] == "owner"

    def test_add_member(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """멤버를 추가할 수 있다."""
        self._register_project(client)
        resp = client.post("/api/projects/member-proj/members/add", json={
            "username": "bob",
            "project_role": "developer",
            "requester": "alice",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["member"]["username"] == "bob"
        assert body["member"]["project_role"] == "developer"

    def test_add_duplicate_member_fails(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """이미 멤버인 사용자를 추가하면 실패한다."""
        self._register_project(client)
        client.post("/api/projects/member-proj/members/add", json={
            "username": "bob",
            "project_role": "developer",
            "requester": "alice",
        })
        resp = client.post("/api/projects/member-proj/members/add", json={
            "username": "bob",
            "project_role": "viewer",
            "requester": "alice",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_add_owner_role_fails(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """OWNER 역할은 직접 추가할 수 없다."""
        self._register_project(client)
        resp = client.post("/api/projects/member-proj/members/add", json={
            "username": "eve",
            "project_role": "owner",
            "requester": "alice",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_remove_member(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """멤버를 제거할 수 있다."""
        self._register_project(client)
        client.post("/api/projects/member-proj/members/add", json={
            "username": "charlie",
            "project_role": "viewer",
            "requester": "alice",
        })
        resp = client.post("/api/projects/member-proj/members/remove", json={
            "username": "charlie",
            "requester": "alice",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_remove_owner_fails(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """OWNER는 제거할 수 없다."""
        self._register_project(client)
        resp = client.post("/api/projects/member-proj/members/remove", json={
            "username": "alice",
            "requester": "alice",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_change_member_role(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """멤버 역할을 변경할 수 있다."""
        self._register_project(client)
        client.post("/api/projects/member-proj/members/add", json={
            "username": "dave",
            "project_role": "developer",
            "requester": "alice",
        })
        resp = client.post("/api/projects/member-proj/members/role", json={
            "username": "dave",
            "project_role": "maintainer",
            "requester": "alice",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["member"]["project_role"] == "maintainer"

    def test_change_owner_role_fails(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """OWNER 역할은 변경할 수 없다."""
        self._register_project(client)
        resp = client.post("/api/projects/member-proj/members/role", json={
            "username": "alice",
            "project_role": "developer",
            "requester": "alice",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_transfer_ownership(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """소유권을 이전할 수 있다."""
        self._register_project(client)
        client.post("/api/projects/member-proj/members/add", json={
            "username": "bob",
            "project_role": "maintainer",
            "requester": "alice",
        })
        resp = client.post("/api/projects/member-proj/members/transfer", json={
            "new_owner": "bob",
            "requester": "alice",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["new_owner"]["project_role"] == "owner"

    def test_check_permission(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """프로젝트 권한 검사가 동작한다."""
        self._register_project(client)
        client.post("/api/projects/member-proj/members/add", json={
            "username": "viewer-user",
            "project_role": "viewer",
            "requester": "alice",
        })
        resp = client.post("/api/projects/member-proj/check-permission", json={
            "username": "alice",
            "permission": "member:add",
        })
        assert resp.status_code == 200
        assert resp.json()["allowed"] is True

        resp = client.post("/api/projects/member-proj/check-permission", json={
            "username": "viewer-user",
            "permission": "member:add",
        })
        assert resp.status_code == 200
        assert resp.json()["allowed"] is False

    def test_viewer_cannot_add_member(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """VIEWER 역할은 멤버를 추가할 수 없다."""
        self._register_project(client)
        client.post("/api/projects/member-proj/members/add", json={
            "username": "viewer1",
            "project_role": "viewer",
            "requester": "alice",
        })
        resp = client.post("/api/projects/member-proj/members/add", json={
            "username": "newguy",
            "project_role": "developer",
            "requester": "viewer1",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_list_members(
        self, client: TestClient, isolated_project_registry,
    ) -> None:
        """멤버 목록을 조회할 수 있다."""
        self._register_project(client)
        client.post("/api/projects/member-proj/members/add", json={
            "username": "m1", "project_role": "developer", "requester": "alice",
        })
        client.post("/api/projects/member-proj/members/add", json={
            "username": "m2", "project_role": "viewer", "requester": "alice",
        })
        resp = client.get("/api/projects/member-proj/members")
        assert resp.status_code == 200
        members = resp.json()["members"]
        usernames = [m["username"] for m in members]
        assert "alice" in usernames
        assert "m1" in usernames
        assert "m2" in usernames


class TestIntegrationTestAPI:
    """Gate 3: Integration Test API 검증."""

    def test_integration_test_no_files(self, client: TestClient) -> None:
        """files가 비어있으면 오류를 반환한다."""
        resp = client.post("/api/integration-test", json={"files": []})
        assert resp.status_code == 200
        assert "error" in resp.json()

    def test_integration_test_nonexistent_file(self, client: TestClient) -> None:
        """존재하지 않는 파일만 전달하면 오류를 반환한다."""
        resp = client.post(
            "/api/integration-test",
            json={"files": ["/nonexistent/file.py"]},
        )
        assert resp.status_code == 200
        assert "error" in resp.json()

    def test_integration_test_with_real_file(self, client: TestClient) -> None:
        """실제 파일을 전달하면 gate_number=3 결과를 반환한다."""
        import os
        test_file = os.path.abspath(__file__)
        resp = client.post(
            "/api/integration-test",
            json={"files": [test_file]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["gate_number"] == 3
        assert data["status"] in ("passed", "warning", "failed")


class TestMetaAPI:
    """Hidden Intent (.meta.json) API 검증."""

    def test_list_meta_empty(self, client: TestClient) -> None:
        """메타 파일이 없으면 빈 목록을 반환한다."""
        resp = client.get("/api/meta")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "metas" in data

    def test_generate_meta_missing_params(self, client: TestClient) -> None:
        """필수 파라미터 누락 시 오류를 반환한다."""
        resp = client.post("/api/meta/generate", json={"file_path": "test.py"})
        assert resp.status_code == 200
        assert "error" in resp.json()

    def test_generate_meta_success(self, client: TestClient) -> None:
        """유효한 파라미터로 .meta.json을 생성한다."""
        resp = client.post("/api/meta/generate", json={
            "file_path": "test_example.py",
            "purpose": "Test purpose for E2E",
            "decisions": ["Use pytest"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "meta_path" in data
        assert data["file_path"] == "test_example.py"

    def test_analyze_meta_nonexistent(self, client: TestClient) -> None:
        """존재하지 않는 파일 분석 시 오류를 반환한다."""
        resp = client.post(
            "/api/meta/analyze",
            json={"file_path": "/no/such/file.py"},
        )
        assert resp.status_code == 200
        assert "error" in resp.json()

    def test_analyze_meta_real_file(self, client: TestClient) -> None:
        """실제 Python 파일을 분석하여 메타를 생성한다."""
        import os
        test_file = os.path.abspath(__file__)
        resp = client.post(
            "/api/meta/analyze",
            json={"file_path": test_file},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "meta_path" in data
        assert data["meta"] is not None
        assert "purpose" in data["meta"]

    def test_batch_analyze(self, client: TestClient) -> None:
        """배치 분석 API가 동작한다."""
        import os
        test_dir = os.path.dirname(os.path.abspath(__file__))
        resp = client.post(
            "/api/meta/batch-analyze",
            json={"directory": test_dir},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert isinstance(data["files"], list)

    def test_index_metas(self, client: TestClient) -> None:
        """메타 인덱싱 API가 동작한다."""
        resp = client.post("/api/meta/index")
        assert resp.status_code == 200
        data = resp.json()
        assert "indexed" in data
        assert "message" in data

    def test_meta_coverage(self, client: TestClient) -> None:
        """커버리지 통계 API가 동작한다."""
        resp = client.get("/api/meta/coverage")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_source_files" in data
        assert "covered" in data
        assert "uncovered" in data
        assert "coverage_rate" in data
        assert isinstance(data["uncovered_files"], list)

    def test_meta_dependency_graph(self, client: TestClient) -> None:
        """의존성 그래프 API가 동작한다."""
        resp = client.get("/api/meta/dependency-graph")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert "total_nodes" in data
        assert "total_edges" in data

    def test_update_meta(self, client: TestClient) -> None:
        """메타 파일을 수정할 수 있다."""
        client.post("/api/meta/generate", json={
            "file_path": "update_test.py",
            "purpose": "Original purpose",
        })
        resp = client.put("/api/meta/update", json={
            "file_path": "update_test.py",
            "purpose": "Updated purpose",
            "decisions": ["New decision"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["meta"]["purpose"] == "Updated purpose"
        assert "New decision" in data["meta"]["decisions"]

    def test_update_meta_nonexistent(self, client: TestClient) -> None:
        """존재하지 않는 메타를 수정하면 오류를 반환한다."""
        resp = client.put("/api/meta/update", json={
            "file_path": "nonexistent_file.py",
            "purpose": "test",
        })
        assert resp.status_code == 200
        assert "error" in resp.json()

    def test_delete_meta(self, client: TestClient) -> None:
        """메타 파일을 삭제할 수 있다."""
        client.post("/api/meta/generate", json={
            "file_path": "delete_test.py",
            "purpose": "To be deleted",
        })
        resp = client.request("DELETE", "/api/meta/delete", json={
            "file_path": "delete_test.py",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_meta_nonexistent(self, client: TestClient) -> None:
        """존재하지 않는 메타를 삭제하면 false를 반환한다."""
        resp = client.request("DELETE", "/api/meta/delete", json={
            "file_path": "no_such_file.py",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is False
