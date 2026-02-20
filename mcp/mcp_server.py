"""VIBE-X MCP Server (v2 — Full Platform).

Model Context Protocol 서버 - AI 어시스턴트(Cursor, Claude 등)가
코딩 중 VIBE-X 전체 기능을 호출할 수 있게 한다.

도구 19개:
  [품질] gate_check, pipeline, security_review, architecture_check
  [RAG]  code_search, index_codebase
  [협업] work_zone, extract_decisions
  [메타] meta_analyze, meta_batch, meta_coverage, meta_dependency_graph
  [분석] feedback_analysis, integration_test
  [운영] project_status, onboarding_qa, get_alerts, acknowledge_alerts
  [관리] list_projects, health_breakdown

사용법:
    python mcp_server.py                     # stdio 모드 (Cursor 연동)
    python mcp_server.py --transport sse     # SSE 모드 (웹 연동)
"""

import sys
import os
import json
import threading
from pathlib import Path
from urllib import request as urllib_request

# 경로 설정
MCP_DIR = Path(__file__).parent                         # mcp/
WORKSPACE_ROOT = MCP_DIR.parent                         # daker/
VIBE_X_ROOT = WORKSPACE_ROOT / "vibe-x"                 # daker/vibe-x/

sys.path.insert(0, str(VIBE_X_ROOT))
os.environ["VIBE_X_NO_WRAP_STDOUT"] = "1"

from mcp.server.fastmcp import FastMCP

from src.shared.config import load_config
from src.shared.types import GateStatus

# 설정 로드
_config = load_config(project_root=WORKSPACE_ROOT)

# 대시보드 연동 URL (로컬 대시보드 서버)
DASHBOARD_API = "http://127.0.0.1:8000"


def _send_to_dashboard(gate_number: int, gate_name: str, status: str,
                        message: str, details: list, file_path: str = "") -> None:
    """Gate 결과를 대시보드 API에 비동기로 전송한다. 실패해도 MCP 응답에 영향 없음."""
    def _post():
        try:
            payload = json.dumps({
                "gate_number": gate_number,
                "gate_name": gate_name,
                "status": status,
                "message": message,
                "details": details[:20],
                "file_path": file_path,
            }).encode("utf-8")
            req = urllib_request.Request(
                f"{DASHBOARD_API}/api/gate-result",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib_request.urlopen(req, timeout=3)
        except Exception:
            pass  # 대시보드가 꺼져 있어도 MCP는 정상 동작
    threading.Thread(target=_post, daemon=True).start()

# MCP 서버 생성
mcp = FastMCP(
    name="VIBE-X",
    instructions=(
        "VIBE-X 전체 플랫폼 MCP 서버 (v2). "
        "코드 품질 6-Gate, 시맨틱 검색, 보안 리뷰, 아키텍처 검증, "
        "팀 협업(Work Zone), Hidden Intent 메타 분석, 피드백 루프, "
        "알림 관리, 온보딩 Q&A, 멀티 프로젝트 관리를 제공합니다."
    ),
)


# ================================================================
# Tool 1: 품질 게이트 실행 (Gate 1-2: 문법 + 규칙)
# ================================================================
@mcp.tool()
def gate_check(file_path: str) -> str:
    """파일에 대해 기본 품질 게이트(Gate 1: 문법, Gate 2: 코딩 규칙)를 실행합니다.
    코드 작성 후 저장할 때 호출하면 좋습니다."""
    from src.layer2_rag.gate_basic import BasicGate

    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"파일을 찾을 수 없습니다: {file_path}"}, ensure_ascii=False)

    gate = BasicGate(_config)
    results = gate.run_all(path)

    output = []
    for r in results:
        output.append({
            "gate": r.gate_number,
            "name": r.gate_name,
            "status": r.status.value,
            "message": r.message,
            "issues": r.details[:10],
        })
        # 대시보드에 결과 전송
        _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                           r.message, r.details, file_path)

    return json.dumps(output, ensure_ascii=False, indent=2)


# ================================================================
# Tool 2: 6-Gate 전체 파이프라인
# ================================================================
@mcp.tool()
def pipeline(file_path: str, author: str = "ai-assistant") -> str:
    """파일에 대해 6-Gate 전체 파이프라인을 실행합니다.
    Gate 1(문법) → Gate 2(규칙) → Gate 3(테스트) → Gate 4(보안/성능) → Gate 5(아키텍처) → Gate 6(충돌감지).
    커밋 전에 반드시 실행하세요."""
    from src.layer3_agents.gate_runner import GateChainRunner

    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"파일을 찾을 수 없습니다: {file_path}"}, ensure_ascii=False)

    runner = GateChainRunner(_config)
    result = runner.run_all(path, author=author)

    gates = []
    for r in result.gate_results:
        gates.append({
            "gate": r.gate_number,
            "name": r.gate_name,
            "status": r.status.value,
            "message": r.message,
            "issues": r.details[:5],
        })
        # 대시보드에 결과 전송
        _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                           r.message, r.details, file_path)

    return json.dumps({
        "overall": result.overall_status.value,
        "summary": result.summary,
        "stopped_at": result.stopped_at,
        "gates": gates,
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 3: 보안/성능 코드 리뷰 (Gate 4)
# ================================================================
@mcp.tool()
def security_review(file_path: str) -> str:
    """파일의 보안 취약점과 성능 안티패턴을 검사합니다.
    OWASP 기반 보안 검사 + N+1 쿼리, 동기 sleep 등 성능 이슈를 탐지합니다."""
    from src.layer3_agents.review_agent import ReviewAgent

    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"파일을 찾을 수 없습니다: {file_path}"}, ensure_ascii=False)

    agent = ReviewAgent(_config)
    r = agent.run(path)

    # 대시보드에 결과 전송
    _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                       r.message, r.details, file_path)

    return json.dumps({
        "status": r.status.value,
        "message": r.message,
        "issues": r.details,
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 4: 아키텍처 검증 (Gate 5)
# ================================================================
@mcp.tool()
def architecture_check(file_path: str) -> str:
    """파일의 아키텍처 규칙 준수를 검증합니다.
    Layer 간 의존성 규칙, 네이밍 컨벤션, 디렉토리 구조를 검사합니다."""
    from src.layer3_agents.arch_agent import ArchitectureAgent

    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"파일을 찾을 수 없습니다: {file_path}"}, ensure_ascii=False)

    agent = ArchitectureAgent(_config)
    r = agent.run(path)

    # 대시보드에 결과 전송
    _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                       r.message, r.details, file_path)

    return json.dumps({
        "status": r.status.value,
        "message": r.message,
        "issues": r.details,
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 5: 시맨틱 코드 검색 (RAG)
# ================================================================
@mcp.tool()
def code_search(query: str, top_k: int = 5) -> str:
    """자연어로 코드베이스를 검색합니다.
    '인증 처리하는 함수', 'DB 연결 설정' 등 의미 기반으로 관련 코드를 찾습니다.
    먼저 index_codebase로 인덱싱이 되어 있어야 합니다."""
    from src.layer2_rag.searcher import CodeSearcher

    searcher = CodeSearcher(_config)
    results = searcher.search(query, top_k=top_k)

    if not results:
        return json.dumps({"message": "검색 결과 없음. 먼저 index_codebase를 실행하세요."}, ensure_ascii=False)

    output = []
    for r in results:
        output.append({
            "file": r.file_path,
            "lines": f"{r.start_line}-{r.end_line}",
            "relevance": f"{r.relevance_score:.0%}",
            "name": r.metadata.get("name", ""),
            "content": r.content[:500],
        })

    return json.dumps(output, ensure_ascii=False, indent=2)


# ================================================================
# Tool 6: 코드베이스 인덱싱
# ================================================================
@mcp.tool()
def index_codebase(path: str = ".") -> str:
    """프로젝트 코드베이스를 벡터 DB에 인덱싱합니다.
    코드 검색(code_search)을 사용하기 전에 먼저 실행해야 합니다."""
    from src.layer2_rag.indexer import CodebaseIndexer

    indexer = CodebaseIndexer(_config)
    target = Path(path).resolve()
    stats = indexer.index_project(target)

    return json.dumps({
        "total_files": stats.total_files,
        "indexed": stats.indexed_files,
        "skipped": stats.skipped_files,
        "chunks": stats.total_chunks,
        "errors": len(stats.errors),
        "duration_seconds": round(stats.duration_seconds, 2),
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 7: Work Zone 관리 (팀 협업)
# ================================================================
@mcp.tool()
def work_zone(action: str, author: str, files: str = "", description: str = "") -> str:
    """팀 작업 영역을 관리합니다.
    action: 'declare'(선언), 'release'(해제), 'list'(조회), 'map'(파일별 매핑)
    files: 쉼표로 구분된 파일 경로 (declare 시 필요)
    동일 파일을 다른 팀원이 수정 중이면 충돌을 경고합니다."""
    from src.layer4_collab.work_zone import WorkZoneManager

    manager = WorkZoneManager(config=_config)

    if action == "declare":
        file_list = [f.strip() for f in files.split(",") if f.strip()]
        if not file_list:
            return json.dumps({"error": "files 파라미터가 필요합니다"}, ensure_ascii=False)
        result = manager.declare(author, file_list, description)
        return json.dumps(result, ensure_ascii=False, indent=2)

    elif action == "release":
        ok = manager.release(author)
        return json.dumps({"released": ok}, ensure_ascii=False)

    elif action == "list":
        zones = manager.get_active_zones()
        return json.dumps({
            name: z.to_dict() for name, z in zones.items()
        }, ensure_ascii=False, indent=2)

    elif action == "map":
        return json.dumps(manager.get_zone_map(), ensure_ascii=False, indent=2)

    return json.dumps({"error": f"알 수 없는 action: {action}"}, ensure_ascii=False)


# ================================================================
# Tool 8: 설계 결정 추출
# ================================================================
@mcp.tool()
def extract_decisions(text: str) -> str:
    """텍스트에서 아키텍처/설계 결정을 자동 추출합니다.
    대화, 코드 리뷰, 미팅 노트 등에서 결정 사항을 ADR로 기록합니다."""
    from src.layer4_collab.decision_extractor import DecisionExtractor

    extractor = DecisionExtractor(_config)
    decisions = extractor.extract_from_text(text, source="mcp-tool")

    if not decisions:
        return json.dumps({"message": "설계 결정이 감지되지 않았습니다."}, ensure_ascii=False)

    output = []
    for d in decisions:
        entry = {
            "title": d.title,
            "decision": d.decision[:300],
            "confidence": f"{d.confidence:.0%}",
        }
        if d.confidence >= 0.5:
            adr_path = extractor.save_as_adr(d)
            if adr_path:
                entry["adr_saved"] = str(adr_path)
        output.append(entry)

    return json.dumps(output, ensure_ascii=False, indent=2)


# ================================================================
# Tool 9: 프로젝트 상태 요약
# ================================================================
@mcp.tool()
def project_status() -> str:
    """현재 VIBE-X 프로젝트의 전체 상태를 요약합니다.
    대시보드 데이터, 온보딩 정보, 피드백 분석을 한번에 조회합니다."""
    from src.layer5_dashboard.metrics import MetricsCollector
    from src.layer5_dashboard.feedback_loop import FeedbackLoop

    metrics = MetricsCollector(_config)
    feedback = FeedbackLoop(_config, metrics_collector=metrics)

    dashboard = metrics.get_dashboard_data()
    fb = feedback.analyze_failure_patterns()

    return json.dumps({
        "dashboard": dashboard,
        "feedback": fb,
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 10: 단일 파일 메타 분석
# ================================================================
@mcp.tool()
def meta_analyze(file_path: str) -> str:
    """소스 파일을 AST로 분석하여 .meta.json(Hidden Intent File)을 자동 생성합니다.
    Python은 AST, TypeScript/TSX는 정규식으로 목적/의존성/설계 결정을 추출합니다."""
    from src.layer2_rag.meta_generator import MetaGenerator

    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"파일을 찾을 수 없습니다: {file_path}"}, ensure_ascii=False)

    gen = MetaGenerator(_config)
    result = gen.analyze_and_generate(path)

    if not result:
        return json.dumps({"error": "분석 실패 또는 지원하지 않는 파일 형식"}, ensure_ascii=False)

    meta = gen.read(file_path)
    return json.dumps({
        "meta_path": str(result),
        "meta": meta.to_dict() if meta else None,
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 11: 일괄 메타 분석 + 인덱싱
# ================================================================
@mcp.tool()
def meta_batch(directory: str = "") -> str:
    """디렉토리 내 모든 소스 파일의 .meta.json을 일괄 생성하고 Vector DB에 인덱싱합니다.
    directory를 비우면 프로젝트 전체(src/)를 대상으로 합니다."""
    from src.layer2_rag.meta_generator import MetaGenerator
    from src.layer2_rag.vector_db import VectorStore

    gen = MetaGenerator(_config)
    target = Path(directory) if directory else VIBE_X_ROOT / "src"
    generated = gen.batch_analyze(target)

    chunks = gen.index_all_metas()
    indexed = 0
    if chunks:
        store = VectorStore(_config)
        for chunk in chunks:
            store.delete_by_file(chunk.file_path)
        indexed = store.add_chunks(chunks)

    return json.dumps({
        "generated": len(generated),
        "indexed": indexed,
        "directory": str(target),
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 12: 메타 커버리지 통계
# ================================================================
@mcp.tool()
def meta_coverage() -> str:
    """소스 파일 대비 .meta.json 보유율 통계를 반환합니다.
    메타가 없는 파일 목록도 함께 제공합니다."""
    from src.layer2_rag.meta_generator import MetaGenerator

    gen = MetaGenerator(_config)
    return json.dumps(gen.get_coverage(), ensure_ascii=False, indent=2)


# ================================================================
# Tool 13: 의존성 그래프
# ================================================================
@mcp.tool()
def meta_dependency_graph() -> str:
    """메타 데이터 기반 파일 간 의존성 그래프를 반환합니다.
    각 파일의 import 관계를 노드/엣지로 시각화합니다."""
    from src.layer2_rag.meta_generator import MetaGenerator

    gen = MetaGenerator(_config)
    return json.dumps(gen.get_dependency_graph(), ensure_ascii=False, indent=2)


# ================================================================
# Tool 14: 피드백 루프 분석
# ================================================================
@mcp.tool()
def feedback_analysis() -> str:
    """Gate 실행 이력을 분석하여 반복 실패 패턴과 개선 제안을 반환합니다."""
    from src.layer5_dashboard.metrics import MetricsCollector
    from src.layer5_dashboard.feedback_loop import FeedbackLoop

    metrics = MetricsCollector(_config)
    fb = FeedbackLoop(_config, metrics_collector=metrics)
    result = fb.analyze_failure_patterns()

    return json.dumps(result, ensure_ascii=False, indent=2)


# ================================================================
# Tool 15: 통합 테스트 실행 (Gate 3)
# ================================================================
@mcp.tool()
def integration_test(files: str) -> str:
    """변경된 파일에 대해 Gate 3(통합 테스트)를 실행합니다.
    Impact Analysis로 영향받는 모듈을 찾고 관련 테스트만 선택 실행합니다.
    files: 쉼표로 구분된 변경 파일 경로."""
    from src.layer3_agents.integration_agent import IntegrationAgent

    file_list = [f.strip() for f in files.split(",") if f.strip()]
    if not file_list:
        return json.dumps({"error": "files 파라미터가 필요합니다"}, ensure_ascii=False)

    agent = IntegrationAgent(_config)
    r = agent.run(file_list)

    _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                       r.message, r.details, files)

    return json.dumps({
        "status": r.status.value,
        "message": r.message,
        "details": r.details,
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 16: 온보딩 Q&A
# ================================================================
@mcp.tool()
def onboarding_qa(question: str) -> str:
    """프로젝트에 대한 질문에 RAG 기반으로 답변합니다.
    예: 'Gate 3이 하는 일은?', 'alerts 시스템 구조는?'"""
    from src.layer5_dashboard.onboarding import OnboardingGuide

    guide = OnboardingGuide(_config)
    result = guide.answer_question(question)

    return json.dumps(result, ensure_ascii=False, indent=2)


# ================================================================
# Tool 17: 알림 조회
# ================================================================
@mcp.tool()
def get_alerts(status: str = "active") -> str:
    """현재 활성 알림을 조회합니다.
    status: 'active'(미처리), 'all'(전체), 'acknowledged'(처리 완료)"""
    from src.layer5_dashboard.metrics import MetricsCollector
    from src.layer5_dashboard.alert_system import AlertManager

    metrics = MetricsCollector(_config)
    alert_mgr = AlertManager(_config, metrics)

    if status == "all":
        alerts = alert_mgr.get_all_alerts()
    elif status == "acknowledged":
        all_a = alert_mgr.get_all_alerts()
        alerts = [a for a in all_a if a.get("acknowledged")]
    else:
        alerts = alert_mgr.get_active_alerts()

    return json.dumps({
        "count": len(alerts),
        "alerts": alerts[:20],
    }, ensure_ascii=False, indent=2)


# ================================================================
# Tool 18: 알림 일괄 해제
# ================================================================
@mcp.tool()
def acknowledge_alerts() -> str:
    """모든 활성 알림을 처리 완료(acknowledged) 상태로 변경합니다."""
    from src.layer5_dashboard.metrics import MetricsCollector
    from src.layer5_dashboard.alert_system import AlertManager

    metrics = MetricsCollector(_config)
    alert_mgr = AlertManager(_config, metrics)
    alert_mgr.acknowledge_all()

    return json.dumps({"acknowledged": True}, ensure_ascii=False)


# ================================================================
# Tool 19: 건강 점수 상세 분해
# ================================================================
@mcp.tool()
def health_breakdown() -> str:
    """프로젝트 건강 점수를 상세 분해하여 반환합니다.
    Gate 통과율, 아키텍처 일관성, 코드 품질, 활동 지수, 기술 부채를 포함합니다."""
    from src.layer5_dashboard.metrics import MetricsCollector

    metrics = MetricsCollector(_config)
    result = metrics.get_health_breakdown()

    return json.dumps(result, ensure_ascii=False, indent=2)


# ================================================================
# Resource: 프로젝트 구조 정보
# ================================================================
@mcp.resource("vibe-x://architecture")
def get_architecture() -> str:
    """VIBE-X 5-Layer 아키텍처 구조를 반환합니다."""
    return json.dumps({
        "layers": [
            {"num": 1, "name": "Structured Prompts (PACT-D)", "path": "templates/"},
            {"num": 2, "name": "RAG Memory Engine", "path": "src/layer2_rag/"},
            {"num": 3, "name": "Multi Agent Quality Gate", "path": "src/layer3_agents/"},
            {"num": 4, "name": "Collaboration Orchestrator", "path": "src/layer4_collab/"},
            {"num": 5, "name": "Team Intelligence Dashboard", "path": "src/layer5_dashboard/"},
        ],
        "shared": "src/shared/",
        "dependency_rule": "상위 Layer만 하위 Layer를 참조 가능. shared는 모든 Layer에서 참조 가능.",
    }, ensure_ascii=False, indent=2)


@mcp.resource("vibe-x://coding-rules")
def get_coding_rules() -> str:
    """VIBE-X 코딩 규칙을 반환합니다."""
    rules_path = _config.paths.coding_rules_path
    if rules_path.exists():
        return rules_path.read_text(encoding="utf-8")
    return "코딩 규칙 파일이 아직 없습니다."


# ================================================================
# 서버 실행
# ================================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VIBE-X MCP Server")
    parser.add_argument(
        "--transport", choices=["stdio", "sse", "streamable-http"],
        default="stdio", help="전송 방식 (기본: stdio)"
    )
    args = parser.parse_args()

    mcp.run(transport=args.transport)
