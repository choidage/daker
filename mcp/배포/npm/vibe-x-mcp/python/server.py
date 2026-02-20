"""VIBE-X MCP Server — Portable version (19 tools).

All paths are resolved from the --project-root argument.
No hardcoded paths. Works on any machine.
"""

import json
import threading
from pathlib import Path
from urllib import request as urllib_request

from mcp.server.fastmcp import FastMCP

DASHBOARD_API = "http://127.0.0.1:8000"


def _send_to_dashboard(gate_number: int, gate_name: str, status: str,
                        message: str, details: list, file_path: str = "") -> None:
    def _post() -> None:
        try:
            payload = json.dumps({
                "gate_number": gate_number, "gate_name": gate_name,
                "status": status, "message": message,
                "details": details[:20], "file_path": file_path,
            }).encode("utf-8")
            req = urllib_request.Request(
                f"{DASHBOARD_API}/api/gate-result",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib_request.urlopen(req, timeout=3)
        except Exception:
            pass
    threading.Thread(target=_post, daemon=True).start()


def create_server(project_root: Path) -> FastMCP:
    """Create a portable VIBE-X MCP server bound to the given project root."""
    from src.shared.config import load_config

    config = load_config(project_root=project_root)
    vibe_x_root = project_root / "vibe-x"

    mcp = FastMCP(
        name="VIBE-X",
        instructions=(
            "VIBE-X Full Platform MCP Server (v2). "
            "6-Gate pipeline, semantic code search, security review, "
            "architecture validation, team collaboration, Hidden Intent meta analysis, "
            "feedback loop, alert management, onboarding Q&A."
        ),
    )

    # ── Tool 1: Gate Check (Gate 1+2) ──
    @mcp.tool()
    def gate_check(file_path: str) -> str:
        """Run basic quality gates (Gate 1: Syntax, Gate 2: Coding Rules) on a file.
        Call this after writing code."""
        from src.layer2_rag.gate_basic import BasicGate

        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"}, ensure_ascii=False)

        gate = BasicGate(config)
        results = gate.run_all(path)
        output = []
        for r in results:
            output.append({"gate": r.gate_number, "name": r.gate_name,
                           "status": r.status.value, "message": r.message,
                           "issues": r.details[:10]})
            _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                               r.message, r.details, file_path)
        return json.dumps(output, ensure_ascii=False, indent=2)

    # ── Tool 2: 6-Gate Pipeline ──
    @mcp.tool()
    def pipeline(file_path: str, author: str = "ai-assistant") -> str:
        """Run the full 6-Gate pipeline on a file.
        Gate 1(Syntax) -> Gate 2(Rules) -> Gate 3(Test) -> Gate 4(Security) -> Gate 5(Architecture) -> Gate 6(Collision).
        Must run before committing."""
        from src.layer3_agents.gate_runner import GateChainRunner

        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"}, ensure_ascii=False)

        runner = GateChainRunner(config)
        result = runner.run_all(path, author=author)
        gates = []
        for r in result.gate_results:
            gates.append({"gate": r.gate_number, "name": r.gate_name,
                          "status": r.status.value, "message": r.message,
                          "issues": r.details[:5]})
            _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                               r.message, r.details, file_path)
        return json.dumps({"overall": result.overall_status.value,
                           "summary": result.summary, "stopped_at": result.stopped_at,
                           "gates": gates}, ensure_ascii=False, indent=2)

    # ── Tool 3: Security Review (Gate 4) ──
    @mcp.tool()
    def security_review(file_path: str) -> str:
        """Scan a file for security vulnerabilities and performance anti-patterns.
        OWASP-based security check + N+1 queries, sync sleep detection."""
        from src.layer3_agents.review_agent import ReviewAgent

        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"}, ensure_ascii=False)

        agent = ReviewAgent(config)
        r = agent.run(path)
        _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                           r.message, r.details, file_path)
        return json.dumps({"status": r.status.value, "message": r.message,
                           "issues": r.details}, ensure_ascii=False, indent=2)

    # ── Tool 4: Architecture Check (Gate 5) ──
    @mcp.tool()
    def architecture_check(file_path: str) -> str:
        """Verify architecture rules: layer dependencies, naming conventions, directory structure."""
        from src.layer3_agents.arch_agent import ArchitectureAgent

        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"}, ensure_ascii=False)

        agent = ArchitectureAgent(config)
        r = agent.run(path)
        _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                           r.message, r.details, file_path)
        return json.dumps({"status": r.status.value, "message": r.message,
                           "issues": r.details}, ensure_ascii=False, indent=2)

    # ── Tool 5: Semantic Code Search ──
    @mcp.tool()
    def code_search(query: str, top_k: int = 5) -> str:
        """Search codebase semantically. Use natural language like
        'authentication function', 'database connection setup'.
        Run index_codebase first."""
        from src.layer2_rag.searcher import CodeSearcher

        searcher = CodeSearcher(config)
        results = searcher.search(query, top_k=top_k)
        if not results:
            return json.dumps({"message": "No results. Run index_codebase first."}, ensure_ascii=False)

        output = [{"file": r.file_path, "lines": f"{r.start_line}-{r.end_line}",
                    "relevance": f"{r.relevance_score:.0%}",
                    "name": r.metadata.get("name", ""),
                    "content": r.content[:500]} for r in results]
        return json.dumps(output, ensure_ascii=False, indent=2)

    # ── Tool 6: Index Codebase ──
    @mcp.tool()
    def index_codebase(path: str = ".") -> str:
        """Index project codebase into Vector DB. Required before code_search."""
        from src.layer2_rag.indexer import CodebaseIndexer

        indexer = CodebaseIndexer(config)
        target = Path(path).resolve()
        stats = indexer.index_project(target)
        return json.dumps({"total_files": stats.total_files, "indexed": stats.indexed_files,
                           "skipped": stats.skipped_files, "chunks": stats.total_chunks,
                           "errors": len(stats.errors),
                           "duration_seconds": round(stats.duration_seconds, 2)},
                          ensure_ascii=False, indent=2)

    # ── Tool 7: Work Zone ──
    @mcp.tool()
    def work_zone(action: str, author: str, files: str = "", description: str = "") -> str:
        """Manage team work zones. action: 'declare', 'release', 'list', 'map'.
        Warns if another team member is editing the same files."""
        from src.layer4_collab.work_zone import WorkZoneManager

        manager = WorkZoneManager(config=config)
        if action == "declare":
            file_list = [f.strip() for f in files.split(",") if f.strip()]
            if not file_list:
                return json.dumps({"error": "files parameter required"}, ensure_ascii=False)
            return json.dumps(manager.declare(author, file_list, description), ensure_ascii=False, indent=2)
        elif action == "release":
            return json.dumps({"released": manager.release(author)}, ensure_ascii=False)
        elif action == "list":
            zones = manager.get_active_zones()
            return json.dumps({n: z.to_dict() for n, z in zones.items()}, ensure_ascii=False, indent=2)
        elif action == "map":
            return json.dumps(manager.get_zone_map(), ensure_ascii=False, indent=2)
        return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False)

    # ── Tool 8: Extract Decisions ──
    @mcp.tool()
    def extract_decisions(text: str) -> str:
        """Auto-extract architecture/design decisions from text.
        Works on conversations, code reviews, meeting notes. Saves as ADR."""
        from src.layer4_collab.decision_extractor import DecisionExtractor

        extractor = DecisionExtractor(config)
        decisions = extractor.extract_from_text(text, source="mcp-tool")
        if not decisions:
            return json.dumps({"message": "No design decisions detected."}, ensure_ascii=False)

        output = []
        for d in decisions:
            entry = {"title": d.title, "decision": d.decision[:300],
                     "confidence": f"{d.confidence:.0%}"}
            if d.confidence >= 0.5:
                adr_path = extractor.save_as_adr(d)
                if adr_path:
                    entry["adr_saved"] = str(adr_path)
            output.append(entry)
        return json.dumps(output, ensure_ascii=False, indent=2)

    # ── Tool 9: Project Status ──
    @mcp.tool()
    def project_status() -> str:
        """Get full project status summary: dashboard data + feedback analysis."""
        from src.layer5_dashboard.metrics import MetricsCollector
        from src.layer5_dashboard.feedback_loop import FeedbackLoop

        metrics = MetricsCollector(config)
        feedback = FeedbackLoop(config, metrics_collector=metrics)
        return json.dumps({"dashboard": metrics.get_dashboard_data(),
                           "feedback": feedback.analyze_failure_patterns()},
                          ensure_ascii=False, indent=2)

    # ── Tool 10: Meta Analyze ──
    @mcp.tool()
    def meta_analyze(file_path: str) -> str:
        """Analyze a source file with AST and auto-generate .meta.json (Hidden Intent File).
        Extracts purpose, dependencies, design decisions."""
        from src.layer2_rag.meta_generator import MetaGenerator

        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"}, ensure_ascii=False)

        gen = MetaGenerator(config)
        result = gen.analyze_and_generate(path)
        if not result:
            return json.dumps({"error": "Analysis failed or unsupported file type"}, ensure_ascii=False)

        meta = gen.read(file_path)
        return json.dumps({"meta_path": str(result),
                           "meta": meta.to_dict() if meta else None},
                          ensure_ascii=False, indent=2)

    # ── Tool 11: Meta Batch ──
    @mcp.tool()
    def meta_batch(directory: str = "") -> str:
        """Batch-generate .meta.json for all source files and index into Vector DB.
        Leave directory empty to analyze project src/."""
        from src.layer2_rag.meta_generator import MetaGenerator
        from src.layer2_rag.vector_db import VectorStore

        gen = MetaGenerator(config)
        target = Path(directory) if directory else vibe_x_root / "src"
        generated = gen.batch_analyze(target)

        chunks = gen.index_all_metas()
        indexed = 0
        if chunks:
            store = VectorStore(config)
            for chunk in chunks:
                store.delete_by_file(chunk.file_path)
            indexed = store.add_chunks(chunks)
        return json.dumps({"generated": len(generated), "indexed": indexed,
                           "directory": str(target)}, ensure_ascii=False, indent=2)

    # ── Tool 12: Meta Coverage ──
    @mcp.tool()
    def meta_coverage() -> str:
        """Get .meta.json coverage stats: how many source files have meta vs don't."""
        from src.layer2_rag.meta_generator import MetaGenerator
        gen = MetaGenerator(config)
        return json.dumps(gen.get_coverage(), ensure_ascii=False, indent=2)

    # ── Tool 13: Meta Dependency Graph ──
    @mcp.tool()
    def meta_dependency_graph() -> str:
        """Get file-to-file dependency graph based on meta data (import relationships)."""
        from src.layer2_rag.meta_generator import MetaGenerator
        gen = MetaGenerator(config)
        return json.dumps(gen.get_dependency_graph(), ensure_ascii=False, indent=2)

    # ── Tool 14: Feedback Analysis ──
    @mcp.tool()
    def feedback_analysis() -> str:
        """Analyze Gate execution history: find repeated failure patterns and suggest improvements."""
        from src.layer5_dashboard.metrics import MetricsCollector
        from src.layer5_dashboard.feedback_loop import FeedbackLoop

        metrics = MetricsCollector(config)
        fb = FeedbackLoop(config, metrics_collector=metrics)
        return json.dumps(fb.analyze_failure_patterns(), ensure_ascii=False, indent=2)

    # ── Tool 15: Integration Test (Gate 3) ──
    @mcp.tool()
    def integration_test(files: str) -> str:
        """Run Gate 3 (Integration Test) on changed files.
        Uses Impact Analysis to find affected modules and runs relevant tests.
        files: comma-separated file paths."""
        from src.layer3_agents.integration_agent import IntegrationAgent

        file_list = [f.strip() for f in files.split(",") if f.strip()]
        if not file_list:
            return json.dumps({"error": "files parameter required"}, ensure_ascii=False)

        agent = IntegrationAgent(config)
        r = agent.run(file_list)
        _send_to_dashboard(r.gate_number, r.gate_name, r.status.value,
                           r.message, r.details, files)
        return json.dumps({"status": r.status.value, "message": r.message,
                           "details": r.details}, ensure_ascii=False, indent=2)

    # ── Tool 16: Onboarding Q&A ──
    @mcp.tool()
    def onboarding_qa(question: str) -> str:
        """Answer project questions using RAG.
        Example: 'What does Gate 3 do?', 'How is the alert system structured?'"""
        from src.layer5_dashboard.onboarding import OnboardingGuide
        guide = OnboardingGuide(config)
        return json.dumps(guide.answer_question(question), ensure_ascii=False, indent=2)

    # ── Tool 17: Get Alerts ──
    @mcp.tool()
    def get_alerts(status: str = "active") -> str:
        """Get current alerts. status: 'active', 'all', 'acknowledged'."""
        from src.layer5_dashboard.metrics import MetricsCollector
        from src.layer5_dashboard.alert_system import AlertManager

        metrics = MetricsCollector(config)
        alert_mgr = AlertManager(config, metrics)
        if status == "all":
            alerts = alert_mgr.get_all_alerts()
        elif status == "acknowledged":
            alerts = [a for a in alert_mgr.get_all_alerts() if a.get("acknowledged")]
        else:
            alerts = alert_mgr.get_active_alerts()
        return json.dumps({"count": len(alerts), "alerts": alerts[:20]},
                          ensure_ascii=False, indent=2)

    # ── Tool 18: Acknowledge Alerts ──
    @mcp.tool()
    def acknowledge_alerts() -> str:
        """Mark all active alerts as acknowledged."""
        from src.layer5_dashboard.metrics import MetricsCollector
        from src.layer5_dashboard.alert_system import AlertManager

        metrics = MetricsCollector(config)
        alert_mgr = AlertManager(config, metrics)
        alert_mgr.acknowledge_all()
        return json.dumps({"acknowledged": True}, ensure_ascii=False)

    # ── Tool 19: Health Breakdown ──
    @mcp.tool()
    def health_breakdown() -> str:
        """Get detailed health score breakdown: Gate pass rate, architecture consistency,
        code quality, activity index, tech debt."""
        from src.layer5_dashboard.metrics import MetricsCollector
        metrics = MetricsCollector(config)
        return json.dumps(metrics.get_health_breakdown(), ensure_ascii=False, indent=2)

    # ── Resources ──
    @mcp.resource("vibe-x://architecture")
    def get_architecture() -> str:
        """Return VIBE-X 5-Layer architecture structure."""
        return json.dumps({
            "layers": [
                {"num": 1, "name": "Structured Prompts (PACT-D)", "path": "templates/"},
                {"num": 2, "name": "RAG Memory Engine", "path": "src/layer2_rag/"},
                {"num": 3, "name": "Multi Agent Quality Gate", "path": "src/layer3_agents/"},
                {"num": 4, "name": "Collaboration Orchestrator", "path": "src/layer4_collab/"},
                {"num": 5, "name": "Team Intelligence Dashboard", "path": "src/layer5_dashboard/"},
            ],
            "shared": "src/shared/",
            "dependency_rule": "Upper layers may only reference lower layers. shared is accessible from all layers.",
        }, ensure_ascii=False, indent=2)

    @mcp.resource("vibe-x://coding-rules")
    def get_coding_rules() -> str:
        """Return VIBE-X coding rules."""
        rules_path = config.paths.coding_rules_path
        if rules_path.exists():
            return rules_path.read_text(encoding="utf-8")
        return "No coding rules file found."

    return mcp
