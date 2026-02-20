"""Task 4.1 + 4.2 - FastAPI Dashboard Server.

팀 인텔리전스 대시보드 백엔드.
REST API + WebSocket 실시간 데이터 제공.
"""

import sys
from pathlib import Path

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from fastapi import Request, Header
from fastapi.middleware.cors import CORSMiddleware

from src.shared.config import load_config
from src.layer5_dashboard.metrics import MetricsCollector
from src.layer5_dashboard.onboarding import OnboardingBriefing
from src.layer5_dashboard.feedback_loop import FeedbackLoop
from src.layer5_dashboard.auth import AuthManager, Role
from src.layer4_collab.work_zone import WorkZoneManager
from src.layer4_collab.decision_extractor import DecisionExtractor
from src.layer5_dashboard.alert_system import AlertSystem
from src.layer5_dashboard.project_registry import (
    ProjectRegistry,
    ProjectRole,
)
from src.layer5_dashboard.project_context import ProjectContextManager

app = FastAPI(title="VIBE-X Dashboard", version="2.0.0")

# CORS 허용 (IDE Extension에서 접근)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 서비스 인스턴스
_config = load_config(project_root=PROJECT_ROOT.parent)
_metrics = MetricsCollector(_config)
_onboarding = OnboardingBriefing(_config)
_feedback = FeedbackLoop(_config, metrics_collector=_metrics)
_auth = AuthManager(_config)
_work_zone = WorkZoneManager(config=_config)
_decision_extractor = DecisionExtractor(_config)
_alert_system = AlertSystem(_config)

# M5: 멀티 프로젝트 지원
_project_registry = ProjectRegistry(_config)
_project_ctx = ProjectContextManager()

# WebSocket 연결 관리
_ws_clients: list[WebSocket] = []


# --- 인증 API ---

@app.post("/api/auth/login")
async def auth_login(data: dict):
    """로그인하여 JWT 토큰을 발급한다."""
    username = data.get("username", "")
    password = data.get("password", "")
    return _auth.login(username, password)


@app.post("/api/auth/register")
async def auth_register(data: dict, authorization: str = Header(default="")):
    """새 사용자를 등록한다. (ADMIN/LEAD 권한 필요)"""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}

    requester_role = Role(payload.role)
    role_str = data.get("role", "developer")
    try:
        role = Role(role_str)
    except ValueError:
        role = Role.DEVELOPER

    return _auth.register_user(
        username=data.get("username", ""),
        password=data.get("password", ""),
        role=role,
        display_name=data.get("display_name", ""),
        email=data.get("email", ""),
        requester_role=requester_role,
    )


@app.post("/api/auth/logout")
async def auth_logout(authorization: str = Header(default="")):
    """로그아웃 (토큰 무효화)."""
    token = authorization.replace("Bearer ", "")
    _auth.logout(token)
    return {"success": True}


@app.get("/api/auth/me")
async def auth_me(authorization: str = Header(default="")):
    """현재 로그인된 사용자 정보."""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}
    user = _auth.get_user(payload.username)
    return {"success": True, "user": user}


@app.get("/api/auth/users")
async def auth_users(authorization: str = Header(default="")):
    """전체 사용자 목록 (ADMIN/LEAD 권한 필요)."""
    token = authorization.replace("Bearer ", "")
    if not _auth.check_permission(token, "user:manage"):
        return {"success": False, "error": "권한 부족"}
    return {"success": True, "users": _auth.list_users()}


@app.post("/api/auth/role")
async def auth_update_role(data: dict, authorization: str = Header(default="")):
    """사용자 역할 변경 (ADMIN 권한 필요)."""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}

    return _auth.update_role(
        username=data.get("username", ""),
        new_role=Role(data.get("role", "developer")),
        requester_role=Role(payload.role),
    )


@app.post("/api/auth/deactivate")
async def auth_deactivate(data: dict, authorization: str = Header(default="")):
    """사용자 비활성화 (ADMIN/LEAD 권한 필요)."""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}
    return _auth.deactivate_user(
        username=data.get("username", ""),
        requester_role=Role(payload.role),
    )


@app.post("/api/auth/activate")
async def auth_activate(data: dict, authorization: str = Header(default="")):
    """사용자 활성화 (ADMIN/LEAD 권한 필요)."""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}
    return _auth.activate_user(
        username=data.get("username", ""),
        requester_role=Role(payload.role),
    )


@app.post("/api/auth/update-user")
async def auth_update_user(data: dict, authorization: str = Header(default="")):
    """사용자 정보 수정 (ADMIN/LEAD 권한 필요)."""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}
    return _auth.update_user_info(
        username=data.get("username", ""),
        display_name=data.get("display_name"),
        email=data.get("email"),
        requester_role=Role(payload.role),
    )


@app.post("/api/auth/delete")
async def auth_delete_user(data: dict, authorization: str = Header(default="")):
    """사용자 삭제 (ADMIN 권한 필요)."""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}
    return _auth.delete_user(
        username=data.get("username", ""),
        requester_role=Role(payload.role),
    )


@app.post("/api/auth/reset-password")
async def auth_reset_password(data: dict, authorization: str = Header(default="")):
    """비밀번호 초기화 (ADMIN 권한 필요)."""
    token = authorization.replace("Bearer ", "")
    payload = _auth.verify_token(token)
    if not payload:
        return {"success": False, "error": "인증 필요"}
    return _auth.reset_password(
        username=data.get("username", ""),
        new_password=data.get("new_password", ""),
        requester_role=Role(payload.role),
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """메인 대시보드 페이지."""
    html_path = Path(__file__).parent / "static" / "dashboard.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# --- RAG Search API ---

@app.get("/api/rag/search")
async def rag_search(q: str = "", top_k: int = 10, lang: str = ""):
    """자연어 코드 검색. Layer 2 RAG Engine을 사용한다."""
    if not q.strip():
        return {"results": [], "query": q, "error": "empty query"}

    from src.layer2_rag.searcher import CodeSearcher

    searcher = CodeSearcher(_config)
    results = searcher.search(
        query=q,
        top_k=top_k,
        language_filter=lang if lang else None,
    )

    return {
        "query": q,
        "total": len(results),
        "results": [
            {
                "file_path": r.file_path,
                "start_line": r.start_line,
                "end_line": r.end_line,
                "score": round(r.relevance_score, 3),
                "content": r.content[:1000],
                "name": r.metadata.get("name", ""),
                "chunk_type": r.metadata.get("chunk_type", ""),
                "language": r.metadata.get("language", ""),
            }
            for r in results
        ],
    }


@app.get("/api/rag/stats")
async def rag_stats():
    """벡터 DB 상태 및 통계."""
    from src.layer2_rag.vector_db import VectorStore

    store = VectorStore(_config)
    stats = store.get_stats()
    return stats


@app.post("/api/rag/index")
async def rag_index(data: dict):
    """수동 인덱싱 트리거. path 미지정 시 프로젝트 루트를 인덱싱한다."""
    from src.layer2_rag.indexer import CodebaseIndexer

    indexer = CodebaseIndexer(_config)
    target = Path(data.get("path", str(PROJECT_ROOT.parent)))

    if not target.exists():
        return {"success": False, "error": f"Path not found: {target}"}

    stats = indexer.index_project(target)
    return {
        "success": True,
        "total_files": stats.total_files,
        "indexed_files": stats.indexed_files,
        "total_chunks": stats.total_chunks,
        "skipped_files": stats.skipped_files,
        "errors": stats.errors[:10],
        "duration_seconds": stats.duration_seconds,
    }


@app.get("/api/dashboard")
async def get_dashboard():
    """대시보드 전체 데이터."""
    return _metrics.get_dashboard_data()


@app.get("/api/onboarding")
async def get_onboarding():
    """온보딩 브리핑 데이터."""
    return _onboarding.generate_briefing()


@app.get("/api/feedback")
async def get_feedback():
    """피드백 루프 분석 결과."""
    return _feedback.analyze_failure_patterns()


@app.get("/api/report")
async def get_monthly_report():
    """월별 리포트 생성."""
    return _feedback.generate_monthly_report()


@app.get("/api/meta")
async def list_meta():
    """모든 .meta.json 목록 조회."""
    from src.layer2_rag.meta_generator import MetaGenerator

    gen = MetaGenerator(_config)
    metas = gen.list_all()
    return {"count": len(metas), "metas": [m.to_dict() for m in metas]}


@app.post("/api/meta/generate")
async def generate_meta(data: dict):
    """특정 파일에 대한 .meta.json 수동 생성."""
    from src.layer2_rag.meta_generator import MetaGenerator

    file_path = data.get("file_path", "")
    purpose = data.get("purpose", "")
    if not file_path or not purpose:
        return {"error": "file_path와 purpose가 필요합니다."}

    gen = MetaGenerator(_config)
    meta_path = gen.generate(
        file_path=file_path,
        purpose=purpose,
        decisions=data.get("decisions", []),
        alternatives=data.get("alternatives", []),
        constraints=data.get("constraints", []),
        dependencies=data.get("dependencies", []),
    )
    return {"meta_path": str(meta_path), "file_path": file_path}


@app.post("/api/meta/analyze")
async def analyze_and_generate_meta(data: dict):
    """파일을 자동 분석하여 .meta.json 생성."""
    from src.layer2_rag.meta_generator import MetaGenerator

    file_path_str = data.get("file_path", "")
    file_path = Path(file_path_str) if file_path_str else None
    if not file_path or not file_path.exists():
        return {"error": "존재하는 file_path가 필요합니다."}

    gen = MetaGenerator(_config)
    result = gen.analyze_and_generate(file_path)
    if not result:
        return {"error": "분석 실패 또는 지원하지 않는 파일 형식입니다."}

    meta = gen.read(file_path_str)
    return {
        "meta_path": str(result),
        "meta": meta.to_dict() if meta else None,
    }


@app.post("/api/meta/batch-analyze")
async def batch_analyze_meta(data: dict):
    """디렉토리 전체 자동 분석 + 메타 생성."""
    from src.layer2_rag.meta_generator import MetaGenerator

    directory = data.get("directory", "")
    dir_path = Path(directory) if directory else _config.paths.project_root / "src"
    if not dir_path.exists():
        return {"error": "존재하는 디렉토리가 필요합니다."}

    gen = MetaGenerator(_config)
    generated = gen.batch_analyze(dir_path)
    return {"count": len(generated), "files": [str(p) for p in generated]}


@app.post("/api/meta/index")
async def index_metas():
    """모든 .meta.json을 Vector DB에 인덱싱."""
    from src.layer2_rag.meta_generator import MetaGenerator
    from src.layer2_rag.vector_db import VectorStore

    gen = MetaGenerator(_config)
    chunks = gen.index_all_metas()
    if not chunks:
        return {"indexed": 0, "message": "인덱싱할 메타 파일 없음"}

    store = VectorStore(_config)
    for chunk in chunks:
        store.delete_by_file(chunk.file_path)
    count = store.add_chunks(chunks)
    return {"indexed": count, "message": f"{count}개 메타 청크 인덱싱 완료"}


@app.get("/api/meta/coverage")
async def meta_coverage():
    """소스 파일 대비 메타 파일 커버리지 통계."""
    from src.layer2_rag.meta_generator import MetaGenerator

    gen = MetaGenerator(_config)
    return gen.get_coverage()


@app.get("/api/meta/dependency-graph")
async def meta_dependency_graph():
    """메타 데이터 기반 의존성 그래프."""
    from src.layer2_rag.meta_generator import MetaGenerator

    gen = MetaGenerator(_config)
    return gen.get_dependency_graph()


@app.put("/api/meta/update")
async def update_meta(data: dict):
    """메타 파일 수정."""
    from src.layer2_rag.meta_generator import MetaGenerator

    file_path = data.get("file_path", "")
    if not file_path:
        return {"error": "file_path가 필요합니다."}

    gen = MetaGenerator(_config)
    updated = gen.update_meta(
        file_path=file_path,
        purpose=data.get("purpose"),
        decisions=data.get("decisions"),
        alternatives=data.get("alternatives"),
        constraints=data.get("constraints"),
        dependencies=data.get("dependencies"),
    )
    if not updated:
        return {"error": "해당 파일의 메타를 찾을 수 없습니다."}
    return {"success": True, "meta": updated.to_dict()}


@app.delete("/api/meta/delete")
async def delete_meta(data: dict):
    """메타 파일 삭제."""
    from src.layer2_rag.meta_generator import MetaGenerator

    file_path = data.get("file_path", "")
    if not file_path:
        return {"error": "file_path가 필요합니다."}

    gen = MetaGenerator(_config)
    deleted = gen.delete_meta(file_path)
    return {"success": deleted}


@app.post("/api/gate-check")
async def gate_check(data: dict):
    """IDE Extension에서 호출 - 특정 파일에 대해 Gate를 실행한다."""
    from src.layer2_rag.gate_basic import BasicGate
    from src.layer3_agents.review_agent import ReviewAgent
    from src.layer3_agents.arch_agent import ArchitectureAgent

    file_path = Path(data.get("file_path", ""))
    if not file_path.exists():
        return {"results": [], "error": "File not found"}

    results = []
    gate = BasicGate(_config)
    for r in gate.run_all(file_path):
        results.append({
            "gate_number": r.gate_number,
            "gate_name": r.gate_name,
            "status": r.status.value,
            "message": r.message,
            "details": r.details,
        })

    review = ReviewAgent(_config)
    r = review.run(file_path)
    results.append({
        "gate_number": r.gate_number,
        "gate_name": r.gate_name,
        "status": r.status.value,
        "message": r.message,
        "details": r.details,
    })

    arch = ArchitectureAgent(_config)
    r = arch.run(file_path)
    results.append({
        "gate_number": r.gate_number,
        "gate_name": r.gate_name,
        "status": r.status.value,
        "message": r.message,
        "details": r.details,
    })

    return {"results": results}


@app.post("/api/integration-test")
async def run_integration_test(data: dict):
    """Gate 3: 변경 파일 기반 통합 테스트 선별 실행."""
    from src.layer3_agents.integration_agent import IntegrationAgent

    files = data.get("files", [])
    if not files:
        return {"error": "files 목록이 필요합니다."}

    changed = [Path(f) for f in files if Path(f).exists()]
    if not changed:
        return {"error": "존재하는 파일이 없습니다."}

    agent = IntegrationAgent(_config)
    result = agent.run(changed)
    return {
        "gate_number": result.gate_number,
        "gate_name": result.gate_name,
        "status": result.status.value,
        "message": result.message,
        "details": result.details,
    }


def _resolve_file_path(file_path_str: str) -> Path | None:
    """파일 경로를 해석하여 존재하는 Path를 반환한다."""
    file_path = Path(file_path_str)
    if file_path.exists():
        return file_path
    abs_try = PROJECT_ROOT / file_path_str
    return abs_try if abs_try.exists() else None


def _gate_result_to_dict(gr) -> dict:
    """GateResult를 직렬화 가능한 dict로 변환한다."""
    return {
        "gate_number": gr.gate_number,
        "gate_name": gr.gate_name,
        "status": gr.status.value,
        "message": gr.message,
        "details": gr.details,
    }


@app.post("/api/pipeline")
async def run_pipeline(data: dict):
    """6-Gate 전체 파이프라인을 실행하고 결과를 기록한다."""
    from src.layer3_agents.gate_runner import GateChainRunner, FailPolicy

    file_path_str = data.get("file_path", "")
    author = data.get("author", "dashboard")
    bypass = data.get("bypass", False)

    file_path = _resolve_file_path(file_path_str)
    if not file_path:
        return {"success": False, "error": f"File not found: {file_path_str}"}

    runner = GateChainRunner(_config)
    if bypass:
        for g in range(1, 7):
            runner.set_policy(g, FailPolicy.BYPASS)

    result = runner.run_all(file_path, author=author)

    gate_results = []
    for gr in result.gate_results:
        gate_results.append(_gate_result_to_dict(gr))
        _metrics.record_gate_result(gr)

    response_data = {
        "success": True,
        "overall_status": result.overall_status.value,
        "summary": result.summary,
        "total_time": round(result.total_time_seconds, 2),
        "stopped_at": result.stopped_at,
        "gates": gate_results,
    }

    for ws in _ws_clients:
        try:
            await ws.send_json({"type": "pipeline_result", "data": response_data})
        except Exception:
            pass

    return response_data


# --- Work Zone API ---

@app.post("/api/work-zone/declare")
async def declare_work_zone(data: dict):
    """작업 영역을 선언한다."""
    author = data.get("author", "unknown")
    files = data.get("files", [])
    description = data.get("description", "")

    if isinstance(files, str):
        files = [f.strip() for f in files.split(",") if f.strip()]

    result = _work_zone.declare(author=author, files=files, description=description)
    _work_zone.save_state()
    return result


@app.post("/api/work-zone/release")
async def release_work_zone(data: dict):
    """작업 영역을 해제한다."""
    author = data.get("author", "")
    ok = _work_zone.release(author)
    _work_zone.save_state()
    return {"success": ok, "author": author}


@app.get("/api/work-zone/list")
async def list_work_zones():
    """활성 작업 영역 목록을 반환한다."""
    zones = _work_zone.get_active_zones()
    return {
        "zones": [
            {
                "author": k,
                "files": v.files,
                "description": v.description,
                "declared_at": v.declared_at.isoformat(),
            }
            for k, v in zones.items()
        ]
    }


@app.get("/api/work-zone/map")
async def get_zone_map():
    """파일별 작업자 매핑을 반환한다."""
    return {"file_map": _work_zone.get_zone_map()}


# --- Decision Extractor API ---

@app.post("/api/decision/extract")
async def extract_decisions(data: dict):
    """텍스트에서 설계 결정을 추출한다."""
    text = data.get("text", "")
    source = data.get("source", "dashboard")
    auto_save = data.get("auto_save", False)

    if not text.strip():
        return {"decisions": [], "error": "empty text"}

    decisions = _decision_extractor.extract_from_text(text, source)

    results = []
    for d in decisions:
        entry = {
            "title": d.title,
            "context": d.context,
            "decision": d.decision[:500],
            "rationale": d.rationale,
            "confidence": round(d.confidence, 2),
            "source": d.source,
        }
        if auto_save and d.confidence >= 0.5:
            adr_path = _decision_extractor.save_as_adr(d)
            entry["adr_path"] = str(adr_path) if adr_path else None
        results.append(entry)

    return {"total": len(results), "decisions": results}


# --- Alert System API ---

@app.get("/api/alerts")
async def get_alerts(active_only: bool = True):
    """경고 목록을 반환한다."""
    if active_only:
        return {"alerts": _alert_system.get_active_alerts()}
    return {"alerts": _alert_system.get_all_alerts()}


@app.post("/api/alerts/acknowledge")
async def acknowledge_alert(data: dict):
    """경고를 확인(dismiss)한다."""
    alert_id = data.get("alert_id", "")
    if alert_id == "all":
        count = _alert_system.acknowledge_all()
        return {"success": True, "acknowledged": count}
    ok = _alert_system.acknowledge_alert(alert_id)
    return {"success": ok}


@app.post("/api/alerts/evaluate")
async def evaluate_alerts():
    """현재 메트릭을 기반으로 경고를 평가한다."""
    dashboard_data = _metrics.get_dashboard_data()
    new_alerts = _alert_system.evaluate_metrics(dashboard_data)

    for alert in new_alerts:
        for ws in _ws_clients:
            try:
                await ws.send_json({
                    "type": "alert",
                    "data": alert.to_dict(),
                })
            except Exception:
                pass

    return {
        "new_alerts": len(new_alerts),
        "alerts": [a.to_dict() for a in new_alerts],
    }


# --- Onboarding Q&A API ---

@app.post("/api/onboarding/qa")
async def onboarding_qa(data: dict):
    """RAG 기반 프로젝트 질의응답."""
    question = data.get("question", "")
    if not question.strip():
        return {"error": "empty question"}
    return _onboarding.answer_question(question)


# --- Health Breakdown API ---

@app.get("/api/health")
async def get_health_breakdown():
    """건강 점수 세부 항목을 반환한다."""
    return _metrics.get_health_breakdown()


@app.post("/api/gate-result")
async def record_gate(data: dict):
    """Gate 결과를 기록한다."""
    from src.shared.types import GateResult, GateStatus

    result = GateResult(
        gate_number=data.get("gate_number", 0),
        gate_name=data.get("gate_name", ""),
        status=GateStatus(data.get("status", "passed")),
        message=data.get("message", ""),
        details=data.get("details", []),
    )
    _metrics.record_gate_result(result)

    new_alerts = _alert_system.evaluate_gate_result(
        gate_number=result.gate_number,
        status=result.status.value,
        details=result.details,
    )

    for ws in _ws_clients:
        try:
            await ws.send_json({"type": "gate_result", "data": data})
            for alert in new_alerts:
                await ws.send_json({"type": "alert", "data": alert.to_dict()})
        except Exception:
            pass

    return {"status": "recorded"}


# --- M5: Multi-Project API ---

@app.get("/api/projects")
async def list_projects(active_only: bool = True):
    """등록된 프로젝트 목록을 반환한다."""
    return {"projects": _project_registry.list_projects(active_only)}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """프로젝트 상세 정보를 반환한다."""
    info = _project_registry.get_project(project_id)
    if not info:
        return {"success": False, "error": "프로젝트 없음"}
    return {"success": True, "project": info}


@app.post("/api/projects/register")
async def register_project(data: dict):
    """프로젝트를 등록한다."""
    return _project_registry.register(
        project_id=data.get("project_id", ""),
        name=data.get("name", ""),
        root_path=data.get("root_path", ""),
        description=data.get("description", ""),
        team=data.get("team", []),
        tags=data.get("tags", []),
        owner=data.get("owner", "admin"),
    )


@app.post("/api/projects/{project_id}/update")
async def update_project(project_id: str, data: dict):
    """프로젝트 메타데이터를 수정한다."""
    return _project_registry.update_project(
        project_id=project_id,
        name=data.get("name"),
        description=data.get("description"),
        team=data.get("team"),
        tags=data.get("tags"),
    )


@app.post("/api/projects/{project_id}/unregister")
async def unregister_project(project_id: str):
    """프로젝트를 비활성화한다."""
    _project_ctx.remove(project_id)
    return _project_registry.unregister(project_id)


@app.get("/api/projects/summary/aggregate")
async def get_aggregate_summary():
    """전체 프로젝트 집계 요약을 반환한다."""
    registry_summary = _project_registry.get_aggregate_summary()

    for proj in registry_summary.get("projects", []):
        pid = proj["project_id"]
        cfg = _project_registry.get_config(pid)
        if cfg:
            svc = _project_ctx.get_services(pid, cfg)
            dash = svc.metrics.get_dashboard_data()
            proj["health_score"] = dash.get("health_score", 0)
            proj["today_gate_runs"] = dash.get("today", {}).get("gate_runs", 0)
            proj["today_pass_rate"] = dash.get("today", {}).get("pass_rate", 0)
            proj["active_alerts"] = len(svc.alerts.get_active_alerts())

    return registry_summary


@app.get("/api/projects/{project_id}/dashboard")
async def get_project_dashboard(project_id: str):
    """특정 프로젝트의 대시보드 데이터를 반환한다."""
    cfg = _project_registry.get_config(project_id)
    if not cfg:
        return {"error": "프로젝트 없음 또는 비활성"}
    svc = _project_ctx.get_services(project_id, cfg)
    return svc.metrics.get_dashboard_data()


@app.get("/api/projects/{project_id}/health")
async def get_project_health(project_id: str):
    """특정 프로젝트의 건강 점수를 반환한다."""
    cfg = _project_registry.get_config(project_id)
    if not cfg:
        return {"error": "프로젝트 없음 또는 비활성"}
    svc = _project_ctx.get_services(project_id, cfg)
    return svc.metrics.get_health_breakdown()


@app.get("/api/projects/{project_id}/alerts")
async def get_project_alerts(project_id: str, active_only: bool = True):
    """특정 프로젝트의 경고를 반환한다."""
    cfg = _project_registry.get_config(project_id)
    if not cfg:
        return {"alerts": [], "error": "프로젝트 없음"}
    svc = _project_ctx.get_services(project_id, cfg)
    if active_only:
        return {"alerts": svc.alerts.get_active_alerts()}
    return {"alerts": svc.alerts.get_all_alerts()}


# --- 프로젝트 멤버 관리 API ---

@app.get("/api/projects/{project_id}/members")
async def list_project_members(project_id: str):
    """프로젝트 멤버 목록을 반환한다."""
    members = _project_registry.list_members(project_id)
    return {"members": members}


@app.post("/api/projects/{project_id}/members/add")
async def add_project_member(project_id: str, data: dict):
    """프로젝트에 멤버를 추가한다."""
    username = data.get("username", "").strip()
    role_str = data.get("project_role", "developer")
    requester = data.get("requester", "")

    if not username:
        return {"success": False, "error": "username 필수"}

    try:
        project_role = ProjectRole(role_str)
    except ValueError:
        return {"success": False, "error": f"유효하지 않은 역할: {role_str}"}

    return _project_registry.add_member(
        project_id=project_id,
        username=username,
        project_role=project_role,
        requester=requester,
    )


@app.post("/api/projects/{project_id}/members/remove")
async def remove_project_member(project_id: str, data: dict):
    """프로젝트에서 멤버를 제거한다."""
    username = data.get("username", "").strip()
    requester = data.get("requester", "")

    if not username:
        return {"success": False, "error": "username 필수"}

    return _project_registry.remove_member(
        project_id=project_id,
        username=username,
        requester=requester,
    )


@app.post("/api/projects/{project_id}/members/role")
async def change_member_role(project_id: str, data: dict):
    """프로젝트 멤버의 역할을 변경한다."""
    username = data.get("username", "").strip()
    role_str = data.get("project_role", "")
    requester = data.get("requester", "")

    if not username or not role_str:
        return {"success": False, "error": "username, project_role 필수"}

    try:
        new_role = ProjectRole(role_str)
    except ValueError:
        return {"success": False, "error": f"유효하지 않은 역할: {role_str}"}

    return _project_registry.change_member_role(
        project_id=project_id,
        username=username,
        new_role=new_role,
        requester=requester,
    )


@app.post("/api/projects/{project_id}/members/transfer")
async def transfer_ownership(project_id: str, data: dict):
    """프로젝트 소유권을 이전한다."""
    new_owner = data.get("new_owner", "").strip()
    requester = data.get("requester", "").strip()

    if not new_owner or not requester:
        return {"success": False, "error": "new_owner, requester 필수"}

    return _project_registry.transfer_ownership(
        project_id=project_id,
        new_owner=new_owner,
        requester=requester,
    )


@app.post("/api/projects/{project_id}/check-permission")
async def check_project_permission(project_id: str, data: dict):
    """프로젝트 권한을 검사한다."""
    username = data.get("username", "")
    permission = data.get("permission", "")

    if not username or not permission:
        return {"allowed": False, "reason": "username, permission 필수"}

    allowed = _project_registry.check_project_permission(
        project_id, username, permission,
    )
    member = _project_registry.get_member(project_id, username)
    return {
        "allowed": allowed,
        "project_role": member.get("project_role") if member else None,
    }


@app.get("/api/projects/{project_id}/zones")
async def get_project_zones(project_id: str):
    """특정 프로젝트의 작업 영역을 반환한다."""
    cfg = _project_registry.get_config(project_id)
    if not cfg:
        return {"zones": [], "error": "프로젝트 없음"}
    svc = _project_ctx.get_services(project_id, cfg)
    zones = svc.work_zone.get_active_zones()
    return {
        "zones": [
            {
                "author": k,
                "files": v.files,
                "description": v.description,
                "declared_at": v.declared_at.isoformat(),
            }
            for k, v in zones.items()
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 스트리밍 WebSocket."""
    await websocket.accept()
    _ws_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                })
            elif data == "refresh":
                dashboard = _metrics.get_dashboard_data()
                await websocket.send_json({
                    "type": "dashboard_update",
                    "data": dashboard,
                })
    except WebSocketDisconnect:
        _ws_clients.remove(websocket)
