"""VIBE-X CLI - 통합 명령줄 인터페이스.

사용법:
    python cli.py index [경로]       - 코드베이스 인덱싱
    python cli.py search <질의>      - 시맨틱 검색
    python cli.py gate <파일>        - 품질 게이트 실행 (Gate 1-2)
    python cli.py pipeline <파일>    - 6-Gate 전체 파이프라인 실행
    python cli.py review <파일>      - Gate 4 코드 리뷰 단독 실행
    python cli.py arch <파일>        - Gate 5 아키텍처 검증 단독 실행
    python cli.py zone <명령>        - 작업 영역 관리
    python cli.py decision <텍스트>  - 설계 결정 추출
    python cli.py mcp-status         - MCP 서버 상태 조회
    python cli.py onboarding         - 온보딩 브리핑 생성
    python cli.py report             - 월별 리포트 생성
    python cli.py meta <파일>        - 메타데이터 생성
    python cli.py stats              - DB 통계 조회
    python cli.py reset              - DB 초기화
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.shared.config import load_config, PathConfig, VibeXConfig
from src.shared.types import GateStatus

console = Console()


def _get_config() -> VibeXConfig:
    """프로젝트 루트 기반 설정을 로드한다."""
    return load_config(project_root=PROJECT_ROOT.parent)


@click.group()
@click.version_option(version="1.0.0", prog_name="VIBE-X")
def cli() -> None:
    """VIBE-X - AI 협업 플랫폼 CLI (Phase 3: 6-Gate Agent)"""
    pass


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def index(path: str) -> None:
    """코드베이스를 벡터 DB에 인덱싱한다."""
    from src.layer2_rag.indexer import CodebaseIndexer

    config = _get_config()
    indexer = CodebaseIndexer(config)
    target = Path(path).resolve()

    console.print(Panel(
        f"[bold cyan]인덱싱 대상:[/bold cyan] {target}",
        title="VIBE-X Indexer",
        border_style="cyan",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("인덱싱 중...", total=None)
        stats = indexer.index_project(target)
        progress.update(task, description="완료!")

    # 결과 테이블
    table = Table(title="인덱싱 결과", border_style="green")
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")
    table.add_row("전체 파일", str(stats.total_files))
    table.add_row("인덱싱 완료", f"[green]{stats.indexed_files}[/green]")
    table.add_row("스킵", str(stats.skipped_files))
    table.add_row("에러", f"[red]{len(stats.errors)}[/red]" if stats.errors else "0")
    table.add_row("총 청크", f"[cyan]{stats.total_chunks}[/cyan]")
    table.add_row("소요 시간", f"{stats.duration_seconds}s")
    console.print(table)

    if stats.errors:
        console.print("\n[red]에러 목록:[/red]")
        for err in stats.errors[:10]:
            console.print(f"  - {err}")


@cli.command()
@click.argument("query")
@click.option("-k", "--top-k", default=5, help="반환할 결과 수")
@click.option("-f", "--file-filter", default=None, help="파일 경로 필터")
@click.option("-l", "--lang", default=None, help="언어 필터")
def search(query: str, top_k: int, file_filter: str | None, lang: str | None) -> None:
    """자연어로 코드베이스를 검색한다."""
    from src.layer2_rag.searcher import CodeSearcher

    config = _get_config()
    searcher = CodeSearcher(config)

    console.print(Panel(
        f"[bold cyan]질의:[/bold cyan] {query}",
        title="VIBE-X Search",
        border_style="cyan",
    ))

    results = searcher.search(query, top_k, file_filter, lang)

    if not results:
        console.print("[yellow]검색 결과가 없습니다. 먼저 인덱싱을 실행하세요.[/yellow]")
        return

    for i, r in enumerate(results, 1):
        score_pct = f"{r.relevance_score:.0%}"
        score_color = "green" if r.relevance_score > 0.7 else "yellow" if r.relevance_score > 0.4 else "red"
        name_info = f" ({r.metadata.get('name', '')})" if r.metadata.get("name") else ""

        console.print(Panel(
            r.content[:500] + ("..." if len(r.content) > 500 else ""),
            title=f"[{score_color}][{i}] {score_pct}[/{score_color}] - "
                  f"{r.file_path}:{r.start_line}-{r.end_line}{name_info}",
            border_style=score_color,
        ))


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def gate(file_path: str) -> None:
    """파일에 대해 품질 게이트(Gate 1-2)를 실행한다."""
    from src.layer2_rag.gate_basic import BasicGate

    config = _get_config()
    gate_runner = BasicGate(config)
    target = Path(file_path)

    console.print(Panel(
        f"[bold cyan]대상:[/bold cyan] {target}",
        title="VIBE-X Quality Gate",
        border_style="cyan",
    ))

    results = gate_runner.run_all(target)

    for r in results:
        if r.status == GateStatus.PASSED:
            icon, color = "PASS", "green"
        elif r.status == GateStatus.WARNING:
            icon, color = "WARN", "yellow"
        elif r.status == GateStatus.FAILED:
            icon, color = "FAIL", "red"
        else:
            icon, color = "SKIP", "dim"

        console.print(f"\n[{color}][{icon}] Gate {r.gate_number}: {r.gate_name}[/{color}]")
        console.print(f"  {r.message}")

        for detail in r.details[:10]:
            console.print(f"  [dim]- {detail}[/dim]")

        if len(r.details) > 10:
            console.print(f"  [dim]... 외 {len(r.details) - 10}개[/dim]")


@cli.command()
@click.argument("file_path")
@click.option("-p", "--purpose", prompt="이 코드의 목적", help="코드 목적")
@click.option("-d", "--decision", multiple=True, help="설계 결정 (복수 가능)")
def meta(file_path: str, purpose: str, decision: tuple) -> None:
    """파일에 대한 .meta.json을 생성한다."""
    from src.layer2_rag.meta_generator import MetaGenerator

    config = _get_config()
    generator = MetaGenerator(config)

    meta_path = generator.generate(
        file_path=file_path,
        purpose=purpose,
        decisions=list(decision) if decision else [],
    )

    console.print(f"[green]메타 파일 생성 완료:[/green] {meta_path}")


@cli.command()
def stats() -> None:
    """벡터 DB 통계를 조회한다."""
    from src.layer2_rag.vector_db import VectorStore

    config = _get_config()
    store = VectorStore(config)
    db_stats = store.get_stats()

    table = Table(title="VIBE-X Vector DB 통계", border_style="cyan")
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")
    table.add_row("컬렉션", db_stats["collection_name"])
    table.add_row("총 청크 수", f"[cyan]{db_stats['total_chunks']}[/cyan]")
    table.add_row("DB 경로", db_stats["db_path"])
    console.print(table)


@cli.command()
@click.confirmation_option(prompt="정말로 모든 데이터를 삭제하시겠습니까?")
def reset() -> None:
    """벡터 DB를 초기화한다 (모든 데이터 삭제)."""
    from src.layer2_rag.vector_db import VectorStore

    config = _get_config()
    store = VectorStore(config)
    store.reset()
    console.print("[red]벡터 DB가 초기화되었습니다.[/red]")


# ============================================================
# Phase 3 Commands: 6-Gate Pipeline, Review, Arch, Zone, Decision
# ============================================================

@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--author", default="current", help="작업자 식별자")
@click.option("--bypass", is_flag=True, help="전체 Gate를 WARN 모드로 실행 (핫픽스용)")
def pipeline(file_path: str, author: str, bypass: bool) -> None:
    """6-Gate 전체 파이프라인을 실행한다 (Gate 1-6)."""
    from src.layer3_agents.gate_runner import GateChainRunner, FailPolicy

    config = _get_config()
    runner = GateChainRunner(config)

    if bypass:
        for g in range(1, 7):
            runner.set_policy(g, FailPolicy.BYPASS)
        console.print("[yellow]BYPASS 모드: 모든 Gate 실패를 무시합니다.[/yellow]")

    target = Path(file_path)
    console.print(Panel(
        f"[bold cyan]대상:[/bold cyan] {target}\n"
        f"[bold cyan]작업자:[/bold cyan] {author}",
        title="VIBE-X 6-Gate Pipeline",
        border_style="cyan",
    ))

    result = runner.run_all(target, author=author)

    # 결과 표시
    table = Table(title="Gate 파이프라인 결과", border_style="cyan")
    table.add_column("Gate", style="bold", width=8)
    table.add_column("이름", width=22)
    table.add_column("상태", width=8)
    table.add_column("메시지")

    for gr in result.gate_results:
        if gr.status == GateStatus.PASSED:
            status_str = "[green]PASS[/green]"
        elif gr.status == GateStatus.WARNING:
            status_str = "[yellow]WARN[/yellow]"
        elif gr.status == GateStatus.FAILED:
            status_str = "[red]FAIL[/red]"
        else:
            status_str = "[dim]SKIP[/dim]"

        table.add_row(str(gr.gate_number), gr.gate_name, status_str, gr.message)

    console.print(table)
    console.print(
        f"\n[bold]종합:[/bold] [{result.overall_status.value}] "
        f"{result.summary}"
    )

    if result.stopped_at:
        console.print(f"[red]Gate {result.stopped_at}에서 파이프라인 중단[/red]")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def review(file_path: str) -> None:
    """Gate 4: 보안/성능 코드 리뷰를 실행한다."""
    from src.layer3_agents.review_agent import ReviewAgent

    config = _get_config()
    agent = ReviewAgent(config)
    target = Path(file_path)

    console.print(Panel(
        f"[bold cyan]대상:[/bold cyan] {target}",
        title="VIBE-X Code Review (Gate 4)",
        border_style="cyan",
    ))

    result = agent.run(target)
    _display_gate_result(result)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def arch(file_path: str) -> None:
    """Gate 5: 아키텍처 정합성을 검증한다."""
    from src.layer3_agents.arch_agent import ArchitectureAgent

    config = _get_config()
    agent = ArchitectureAgent(config)
    target = Path(file_path)

    console.print(Panel(
        f"[bold cyan]대상:[/bold cyan] {target}",
        title="VIBE-X Architecture Check (Gate 5)",
        border_style="cyan",
    ))

    result = agent.run(target)
    _display_gate_result(result)


@cli.command()
@click.argument("action", type=click.Choice(["declare", "release", "list", "map"]))
@click.option("--author", default="current", help="작업자 식별자")
@click.option("--files", "-f", multiple=True, help="수정 예정 파일 경로")
@click.option("--desc", default="", help="작업 설명")
def zone(action: str, author: str, files: tuple, desc: str) -> None:
    """작업 영역 관리 (declare/release/list/map)."""
    from src.layer4_collab.work_zone import WorkZoneManager

    config = _get_config()
    manager = WorkZoneManager(config=config)

    if action == "declare":
        if not files:
            console.print("[red]--files 옵션으로 수정 예정 파일을 지정하세요.[/red]")
            return
        result = manager.declare(author, list(files), desc)
        console.print(f"[green]작업 영역 선언:[/green] {result['file_count']}개 파일")
        if result["conflicts"]:
            for c in result["conflicts"]:
                console.print(
                    f"  [yellow]충돌:[/yellow] {c['conflicting_author']} - "
                    f"{len(c['overlapping_files'])}개 파일"
                )

    elif action == "release":
        ok = manager.release(author)
        if ok:
            console.print(f"[green]'{author}' 작업 영역 해제 완료[/green]")
        else:
            console.print(f"[yellow]'{author}' - 활성 작업 영역 없음[/yellow]")

    elif action == "list":
        zones = manager.get_active_zones()
        if not zones:
            console.print("[dim]활성 작업 영역 없음[/dim]")
        else:
            table = Table(title="활성 작업 영역", border_style="cyan")
            table.add_column("작업자", style="bold")
            table.add_column("파일 수")
            table.add_column("설명")
            for name, z in zones.items():
                table.add_row(name, str(len(z.files)), z.description)
            console.print(table)

    elif action == "map":
        file_map = manager.get_zone_map()
        if not file_map:
            console.print("[dim]활성 매핑 없음[/dim]")
        else:
            table = Table(title="파일-작업자 매핑", border_style="cyan")
            table.add_column("파일")
            table.add_column("작업자")
            for fp, authors in sorted(file_map.items()):
                table.add_row(fp, ", ".join(authors))
            console.print(table)


@cli.command(name="decision")
@click.argument("text_or_file")
def extract_decision(text_or_file: str) -> None:
    """텍스트 또는 파일에서 설계 결정을 추출한다."""
    from src.layer4_collab.decision_extractor import DecisionExtractor

    config = _get_config()
    extractor = DecisionExtractor(config)

    # 파일이면 읽기
    path = Path(text_or_file)
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace")
        source = str(path)
    else:
        text = text_or_file
        source = "inline"

    decisions = extractor.extract_from_text(text, source)

    if not decisions:
        console.print("[yellow]설계 결정이 감지되지 않았습니다.[/yellow]")
        return

    for d in decisions:
        console.print(Panel(
            f"[bold]{d.title}[/bold]\n"
            f"신뢰도: {d.confidence:.0%}\n"
            f"결정: {d.decision[:200]}",
            title=f"Decision (출처: {d.source})",
            border_style="magenta",
        ))

        # ADR로 저장할지 확인
        if d.confidence >= 0.5:
            adr_path = extractor.save_as_adr(d)
            if adr_path:
                console.print(f"  [green]ADR 저장:[/green] {adr_path}")


@cli.command(name="mcp-status")
def mcp_status() -> None:
    """MCP 서버 상태를 조회한다."""
    from src.layer4_collab.mcp_server import McpServer

    mcp = McpServer()
    stats = mcp.get_stats()

    table = Table(title="MCP Server Status", border_style="cyan")
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")
    table.add_row("등록 Agent", str(stats["total_agents"]))
    table.add_row("활성 Agent", str(stats["active_agents"]))
    table.add_row("구독 수", str(stats["total_subscriptions"]))
    table.add_row("메시지 이력", str(stats["message_log_size"]))
    table.add_row("컨텍스트 키", ", ".join(stats["context_keys"]) or "(없음)")
    console.print(table)


@cli.command(name="onboarding")
def show_onboarding() -> None:
    """온보딩 브리핑을 생성하여 표시한다."""
    from src.layer5_dashboard.onboarding import OnboardingBriefing

    config = _get_config()
    briefing = OnboardingBriefing(config)
    data = briefing.generate_briefing()

    # 프로젝트 개요
    ov = data.get("project_overview", {})
    console.print(Panel(
        f"[bold]{ov.get('title', 'VIBE-X')}[/bold]\n"
        f"{ov.get('description', '')}",
        title="Project Overview",
        border_style="cyan",
    ))

    # 아키텍처
    arch_data = data.get("architecture", {})
    layers = arch_data.get("layers", [])
    if layers:
        table = Table(title="Architecture Layers", border_style="magenta")
        table.add_column("Layer", style="bold", width=6)
        table.add_column("Name", width=30)
        table.add_column("Description")
        for l in layers:
            table.add_row(str(l["num"]), l["name"], l["desc"])
        console.print(table)

    # 모듈 현황
    modules = data.get("key_modules", [])
    if modules:
        table = Table(title="Key Modules", border_style="green")
        table.add_column("Layer")
        table.add_column("Files")
        table.add_column("Count", justify="right")
        for m in modules:
            table.add_row(m["layer"], ", ".join(m["files"][:5]), str(m["count"]))
        console.print(table)

    # ADR
    adrs = data.get("adr_timeline", [])
    if adrs:
        console.print("\n[bold]ADR Timeline:[/bold]")
        for a in adrs:
            console.print(f"  [cyan]>[/cyan] {a['file']} - {a['title']}")

    # 시작 가이드
    gs = data.get("getting_started", {})
    steps = gs.get("steps", [])
    if steps:
        console.print(Panel(
            "\n".join(steps),
            title="Getting Started",
            border_style="green",
        ))


@cli.command(name="report")
def generate_report() -> None:
    """월별 자동 리포트를 생성한다."""
    from src.layer5_dashboard.feedback_loop import FeedbackLoop

    config = _get_config()
    fb = FeedbackLoop(config)
    report = fb.generate_monthly_report()

    summary = report.get("summary", {})
    table = Table(title=f"Monthly Report - {report.get('month', '')}", border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Gate Runs", str(summary.get("total_gate_runs", 0)))
    table.add_row("Pass Rate", f"{summary.get('pass_rate', 0)}%")
    table.add_row("AI Cost", f"${summary.get('total_cost_usd', 0)}")
    table.add_row("Files Indexed", str(summary.get("total_files_indexed", 0)))
    table.add_row("Searches", str(summary.get("total_searches", 0)))
    table.add_row("Decisions Extracted", str(summary.get("total_decisions", 0)))
    table.add_row("Active Days", str(summary.get("active_days", 0)))
    console.print(table)

    suggestions = report.get("recommendations", [])
    if suggestions:
        console.print("\n[bold]Recommendations:[/bold]")
        for s in suggestions:
            console.print(f"  [magenta]>[/magenta] {s}")


def _display_gate_result(result) -> None:
    """단일 Gate 결과를 화면에 표시한다."""
    if result.status == GateStatus.PASSED:
        icon, color = "PASS", "green"
    elif result.status == GateStatus.WARNING:
        icon, color = "WARN", "yellow"
    elif result.status == GateStatus.FAILED:
        icon, color = "FAIL", "red"
    else:
        icon, color = "SKIP", "dim"

    console.print(f"\n[{color}][{icon}] Gate {result.gate_number}: {result.gate_name}[/{color}]")
    console.print(f"  {result.message}")

    for detail in result.details[:15]:
        console.print(f"  [dim]- {detail}[/dim]")

    if len(result.details) > 15:
        console.print(f"  [dim]... 외 {len(result.details) - 15}개[/dim]")


if __name__ == "__main__":
    cli()
