"""Task 4.4 - RAG 기반 온보딩 자동 브리핑 + Q&A.

신규 팀원에게 프로젝트 컨텍스트를 자동 요약하여 제공하고,
RAG 기반으로 프로젝트 관련 질문에 답변한다.
"""

from pathlib import Path
from datetime import datetime

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger

logger = get_logger("onboarding")

CONTEXT_SNIPPET_LIMIT = 800
MAX_QA_RESULTS = 5


class OnboardingBriefing:
    """RAG 기반 온보딩 브리핑 생성기.

    프로젝트 구조, 설계 결정 이력, 코딩 규칙을
    자동으로 요약하여 신규 팀원에게 제공한다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()

    def generate_briefing(self) -> dict:
        """프로젝트 온보딩 브리핑을 생성한다."""
        sections = {
            "project_overview": self._get_project_overview(),
            "architecture": self._get_architecture_summary(),
            "coding_rules": self._get_coding_rules_summary(),
            "adr_timeline": self._get_adr_timeline(),
            "key_modules": self._get_key_modules(),
            "getting_started": self._get_getting_started(),
            "generated_at": datetime.now().isoformat(),
        }

        logger.info("온보딩 브리핑 생성 완료")
        return sections

    def _get_project_overview(self) -> dict:
        """프로젝트 개요를 수집한다."""
        overview_path = self._config.paths.vibe_x_root / "project-definition.md"
        content = ""
        if overview_path.exists():
            content = overview_path.read_text(encoding="utf-8", errors="replace")[:2000]

        return {
            "title": "VIBE-X 통합 협업 플랫폼",
            "description": "AI 바이브 코딩의 품질을 체계적으로 보장하는 5-Layer 아키텍처",
            "content": content,
        }

    def _get_architecture_summary(self) -> dict:
        """아키텍처 요약을 수집한다."""
        arch_path = self._config.paths.vibe_x_root / "architecture-map.md"
        content = ""
        if arch_path.exists():
            content = arch_path.read_text(encoding="utf-8", errors="replace")[:2000]

        return {
            "layers": [
                {"num": 1, "name": "Structured Prompts", "desc": "PACT-D 프레임워크 기반 프롬프트"},
                {"num": 2, "name": "RAG Memory Engine", "desc": "코드베이스 벡터 검색 + 의도 추적"},
                {"num": 3, "name": "Multi-Agent Quality Gate", "desc": "6-Gate 자동 검증 체인"},
                {"num": 4, "name": "Collaboration Orchestrator", "desc": "MCP 기반 팀 협업"},
                {"num": 5, "name": "Team Intelligence Dashboard", "desc": "실시간 지표 + 인사이트"},
            ],
            "content": content,
        }

    def _get_coding_rules_summary(self) -> dict:
        """코딩 규칙 요약을 수집한다."""
        rules_path = self._config.paths.vibe_x_root / "coding-rules.md"
        content = ""
        if rules_path.exists():
            content = rules_path.read_text(encoding="utf-8", errors="replace")[:2000]

        return {"content": content}

    def _get_adr_timeline(self) -> list[dict]:
        """ADR 타임라인을 수집한다."""
        adr_dir = self._config.paths.adr_dir
        adrs = []

        if adr_dir.exists():
            for adr_file in sorted(adr_dir.glob("*.md")):
                if adr_file.name == "template.md":
                    continue
                adrs.append({
                    "file": adr_file.name,
                    "title": adr_file.stem.split("-", 1)[-1].replace("-", " ") if "-" in adr_file.stem else adr_file.stem,
                })

        return adrs

    def _get_key_modules(self) -> list[dict]:
        """핵심 모듈 목록을 수집한다."""
        src_dir = self._config.paths.vibe_x_root / "src"
        modules = []

        if src_dir.exists():
            for layer_dir in sorted(src_dir.iterdir()):
                if layer_dir.is_dir() and not layer_dir.name.startswith("__"):
                    py_files = list(layer_dir.glob("*.py"))
                    file_names = [f.stem for f in py_files if f.stem != "__init__"]
                    if file_names:
                        modules.append({
                            "layer": layer_dir.name,
                            "files": file_names,
                            "count": len(file_names),
                        })

        return modules

    def answer_question(self, question: str) -> dict:
        """RAG 기반으로 프로젝트 관련 질문에 답변한다.

        벡터 DB에서 관련 코드/문서를 검색하고,
        ADR + 코딩 규칙 + 아키텍처 문서를 함께 참고한다.
        """
        from src.layer2_rag.searcher import CodeSearcher

        searcher = CodeSearcher(self._config)
        results = searcher.search(question, top_k=MAX_QA_RESULTS)

        code_context = []
        for r in results:
            code_context.append({
                "file": r.file_path,
                "lines": f"{r.start_line}-{r.end_line}",
                "score": round(r.relevance_score, 3),
                "snippet": r.content[:CONTEXT_SNIPPET_LIMIT],
                "name": r.metadata.get("name", ""),
                "type": r.metadata.get("chunk_type", ""),
            })

        doc_context = self._gather_doc_context(question)
        adr_context = self._gather_adr_context(question)

        answer = self._compose_answer(question, code_context, doc_context, adr_context)

        return {
            "question": question,
            "answer": answer,
            "code_references": code_context,
            "doc_sources": list(doc_context.keys()),
            "adr_references": [a["file"] for a in adr_context],
        }

    def _gather_doc_context(self, question: str) -> dict[str, str]:
        """프로젝트 문서에서 관련 컨텍스트를 수집한다."""
        docs: dict[str, str] = {}
        q_lower = question.lower()

        doc_map = {
            "project-definition.md": ["프로젝트", "목표", "비전", "스택", "project", "goal"],
            "architecture-map.md": ["아키텍처", "layer", "구조", "모듈", "architecture"],
            "coding-rules.md": ["규칙", "컨벤션", "네이밍", "rule", "convention", "naming"],
        }

        for filename, keywords in doc_map.items():
            if any(kw in q_lower for kw in keywords):
                path = self._config.paths.vibe_x_root / filename
                if path.exists():
                    docs[filename] = path.read_text(
                        encoding="utf-8", errors="replace"
                    )[:2000]

        if not docs:
            overview = self._config.paths.vibe_x_root / "project-definition.md"
            if overview.exists():
                docs["project-definition.md"] = overview.read_text(
                    encoding="utf-8", errors="replace"
                )[:1500]

        return docs

    def _gather_adr_context(self, question: str) -> list[dict]:
        """관련 ADR을 수집한다."""
        adr_dir = self._config.paths.adr_dir
        adrs: list[dict] = []

        if not adr_dir.exists():
            return adrs

        q_lower = question.lower()

        for adr_file in sorted(adr_dir.glob("*.md")):
            if adr_file.name == "template.md":
                continue
            content = adr_file.read_text(encoding="utf-8", errors="replace")
            title_part = adr_file.stem.split("-", 1)[-1].replace("-", " ")

            if any(word in content.lower() for word in q_lower.split() if len(word) > 2):
                adrs.append({
                    "file": adr_file.name,
                    "title": title_part,
                    "excerpt": content[:500],
                })

        return adrs[:3]

    def _compose_answer(
        self,
        question: str,
        code_ctx: list[dict],
        doc_ctx: dict[str, str],
        adr_ctx: list[dict],
    ) -> str:
        """수집된 컨텍스트를 기반으로 답변을 구성한다."""
        parts: list[str] = []

        if doc_ctx:
            parts.append("**관련 문서:**")
            for name, content in doc_ctx.items():
                summary = content[:300].replace("\n", " ").strip()
                parts.append(f"- `{name}`: {summary}...")

        if adr_ctx:
            parts.append("\n**관련 ADR:**")
            for adr in adr_ctx:
                parts.append(f"- `{adr['file']}`: {adr['title']}")

        if code_ctx:
            parts.append("\n**관련 코드:**")
            for c in code_ctx[:3]:
                name_info = f" ({c['name']})" if c['name'] else ""
                parts.append(
                    f"- `{c['file']}:{c['lines']}`{name_info} "
                    f"[{c['score']:.0%} relevance]"
                )

        if not parts:
            return "관련 정보를 찾지 못했습니다. 다른 키워드로 시도해보세요."

        return "\n".join(parts)

    def _get_getting_started(self) -> dict:
        """시작 가이드를 반환한다."""
        return {
            "steps": [
                "1. Python 3.10+ 환경 확인",
                "2. pip install -r requirements.txt",
                "3. python cli.py index . (코드베이스 인덱싱)",
                "4. python cli.py search '인증 로직' (시맨틱 검색 테스트)",
                "5. python cli.py pipeline <파일> (6-Gate 파이프라인 실행)",
                "6. python server.py (대시보드 서버 시작)",
            ],
            "cli_commands": [
                "index - 코드베이스 인덱싱",
                "search - 시맨틱 코드 검색",
                "gate - 기본 품질 검사 (Gate 1-2)",
                "pipeline - 6-Gate 전체 파이프라인",
                "review - 보안/성능 리뷰",
                "arch - 아키텍처 검증",
                "zone - 작업 영역 관리",
                "decision - 설계 결정 추출",
            ],
        }
