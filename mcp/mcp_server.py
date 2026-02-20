"""VIBE-X MCP Server.

Model Context Protocol 서버 - AI 어시스턴트(Cursor, Claude 등)가
코딩 중 자동으로 VIBE-X 품질 게이트, 코드 검색, 협업 기능을 호출할 수 있게 한다.

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
        "VIBE-X 통합 협업 플랫폼 MCP 서버. "
        "코드 품질 검사(6-Gate), 시맨틱 코드 검색, 보안 리뷰, "
        "아키텍처 검증, 팀 협업(Work Zone) 기능을 제공합니다."
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
