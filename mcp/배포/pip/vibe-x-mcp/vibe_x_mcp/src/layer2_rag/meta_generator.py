"""Task 2.5 - Hidden Intent File (.meta.json) 생성 모듈.

AI 코드 생성 시 "왜 이렇게 만들었는지"를 메타데이터로 기록한다.
코드는 남지만 의도는 사라지는 문제를 해결한다.

주요 기능:
- 수동 생성: generate() — 사용자가 의도를 직접 지정
- 자동 분석: analyze_and_generate() — AST 기반으로 목적/의존성 자동 추출
- Vector DB 인덱싱: index_meta() — .meta.json을 검색 가능하게 저장
- 일괄 처리: batch_analyze() — 프로젝트 전체 자동 분석
"""

import ast
import json
import re
from datetime import datetime
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import ChunkType, CodeChunk, IntentMeta

logger = get_logger("meta-gen")

MAX_DOCSTRING_LENGTH = 200


class MetaGenerator:
    """Hidden Intent File 생성기.

    코드 파일과 짝을 이루는 .meta.json 파일을 생성한다.
    이 메타데이터는 Vector DB에 인덱싱되어 RAG 검색에 활용된다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()

    def generate(
        self,
        file_path: str,
        purpose: str,
        decisions: list[str] | None = None,
        alternatives: list[str] | None = None,
        constraints: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> Path:
        """파일에 대한 .meta.json을 생성한다."""
        meta = IntentMeta(
            file_path=file_path,
            purpose=purpose,
            decisions=decisions or [],
            alternatives=alternatives or [],
            constraints=constraints or [],
            dependencies=dependencies or [],
            created_at=datetime.now(),
        )

        meta_path = self._get_meta_path(file_path)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(meta.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(f"meta created: {meta_path.name}")
        return meta_path

    def analyze_and_generate(self, file_path: Path) -> Path | None:
        """소스 파일을 AST로 분석하여 .meta.json을 자동 생성한다."""
        if not file_path.exists():
            return None
        if file_path.suffix not in (".py", ".ts", ".tsx"):
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

        if file_path.suffix == ".py":
            analysis = self._analyze_python(content, file_path)
        else:
            analysis = self._analyze_typescript(content, file_path)

        if not analysis["purpose"]:
            analysis["purpose"] = f"{file_path.name} module"

        return self.generate(
            file_path=str(file_path),
            purpose=analysis["purpose"],
            decisions=analysis["decisions"],
            constraints=analysis["constraints"],
            dependencies=analysis["dependencies"],
        )

    def batch_analyze(self, directory: Path) -> list[Path]:
        """디렉토리 내 모든 소스 파일에 대해 자동 분석 + 메타 생성."""
        generated: list[Path] = []
        extensions = {".py", ".ts", ".tsx"}
        ignored = {"__pycache__", "node_modules", ".next", ".git", ".venv"}

        for item in sorted(directory.rglob("*")):
            if any(part in ignored for part in item.parts):
                continue
            if item.is_file() and item.suffix in extensions:
                result = self.analyze_and_generate(item)
                if result:
                    generated.append(result)

        logger.info(f"batch analyze complete: {len(generated)} meta files")
        return generated

    def index_meta(self, meta: IntentMeta) -> list[CodeChunk]:
        """IntentMeta를 CodeChunk로 변환하여 Vector DB 인덱싱에 사용한다."""
        intent_text = self._meta_to_searchable_text(meta)
        chunk = CodeChunk(
            file_path=meta.file_path,
            content=intent_text,
            start_line=0,
            end_line=0,
            chunk_type=ChunkType.DOCUMENT,
            language="intent",
            name=f"intent:{Path(meta.file_path).name}",
        )
        return [chunk]

    def index_all_metas(self) -> list[CodeChunk]:
        """모든 .meta.json을 CodeChunk 리스트로 변환한다."""
        chunks: list[CodeChunk] = []
        for meta in self.list_all():
            chunks.extend(self.index_meta(meta))
        return chunks

    def read(self, file_path: str) -> IntentMeta | None:
        """파일의 .meta.json을 읽는다."""
        meta_path = self._get_meta_path(file_path)
        if not meta_path.exists():
            return None

        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            return IntentMeta(
                file_path=data["file_path"],
                purpose=data["purpose"],
                decisions=data.get("decisions", []),
                alternatives=data.get("alternatives", []),
                constraints=data.get("constraints", []),
                dependencies=data.get("dependencies", []),
                created_at=datetime.fromisoformat(data["created_at"]),
                author=data.get("author", "vibe-x"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"meta parse failed: {meta_path} - {e}")
            return None

    def list_all(self) -> list[IntentMeta]:
        """모든 .meta.json 파일을 읽어 목록으로 반환한다."""
        meta_dir = self._config.paths.meta_dir
        if not meta_dir.exists():
            return []

        metas: list[IntentMeta] = []
        for meta_file in sorted(meta_dir.rglob("*.meta.json")):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                metas.append(
                    IntentMeta(
                        file_path=data["file_path"],
                        purpose=data["purpose"],
                        decisions=data.get("decisions", []),
                        alternatives=data.get("alternatives", []),
                        constraints=data.get("constraints", []),
                        dependencies=data.get("dependencies", []),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        author=data.get("author", "vibe-x"),
                    )
                )
            except (json.JSONDecodeError, KeyError):
                continue

        return metas

    def _analyze_python(self, content: str, file_path: Path) -> dict:
        """Python 파일을 AST로 분석한다."""
        result: dict[str, str | list[str]] = {
            "purpose": "",
            "decisions": [],
            "constraints": [],
            "dependencies": [],
        }

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return result

        module_doc = ast.get_docstring(tree)
        if module_doc:
            result["purpose"] = module_doc.split("\n")[0][:MAX_DOCSTRING_LENGTH]

        imports: list[str] = []
        classes: list[str] = []
        functions: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                doc = ast.get_docstring(node)
                if doc:
                    decisions = result["decisions"]
                    assert isinstance(decisions, list)
                    decisions.append(f"Class {node.name}: {doc.split(chr(10))[0][:80]}")
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)

        result["dependencies"] = sorted(set(imports))[:10]

        constraints = result["constraints"]
        assert isinstance(constraints, list)
        if classes:
            constraints.append(f"classes: {', '.join(classes[:5])}")
        if functions:
            public_fns = [f for f in functions if not f.startswith("_")][:5]
            if public_fns:
                constraints.append(f"public API: {', '.join(public_fns)}")

        return result

    def _analyze_typescript(self, content: str, file_path: Path) -> dict:
        """TypeScript/TSX 파일을 정규식으로 분석한다."""
        result: dict[str, str | list[str]] = {
            "purpose": "",
            "decisions": [],
            "constraints": [],
            "dependencies": [],
        }

        first_comment = re.search(r"/\*\*\s*\n\s*\*\s*(.+)", content)
        if first_comment:
            result["purpose"] = first_comment.group(1).strip()[:MAX_DOCSTRING_LENGTH]

        imports: list[str] = []
        for match in re.finditer(
            r"(?:import|from)\s+['\"]([^'\"]+)['\"]", content
        ):
            imports.append(match.group(1))
        result["dependencies"] = sorted(set(imports))[:10]

        exports: list[str] = []
        for match in re.finditer(
            r"export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+(\w+)",
            content,
        ):
            exports.append(match.group(1))

        constraints = result["constraints"]
        assert isinstance(constraints, list)
        if exports:
            constraints.append(f"exports: {', '.join(exports[:5])}")

        return result

    def update_meta(
        self,
        file_path: str,
        purpose: str | None = None,
        decisions: list[str] | None = None,
        alternatives: list[str] | None = None,
        constraints: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> IntentMeta | None:
        """기존 .meta.json을 수정한다. None인 필드는 기존 값을 유지한다."""
        existing = self.read(file_path)
        if not existing:
            return None

        if purpose is not None:
            existing.purpose = purpose
        if decisions is not None:
            existing.decisions = decisions
        if alternatives is not None:
            existing.alternatives = alternatives
        if constraints is not None:
            existing.constraints = constraints
        if dependencies is not None:
            existing.dependencies = dependencies

        meta_path = self._get_meta_path(file_path)
        meta_path.write_text(
            json.dumps(existing.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"meta updated: {meta_path.name}")
        return existing

    def delete_meta(self, file_path: str) -> bool:
        """파일의 .meta.json을 삭제한다."""
        meta_path = self._get_meta_path(file_path)
        if meta_path.exists():
            meta_path.unlink()
            logger.info(f"meta deleted: {meta_path.name}")
            return True
        return False

    def get_coverage(self) -> dict:
        """소스 파일 대비 메타 파일 커버리지 통계를 반환한다."""
        src_dir = self._config.paths.project_root / "vibe-x" / "src"
        dash_dir = self._config.paths.project_root / "vibe-x" / "dashboard" / "src"
        extensions = {".py", ".ts", ".tsx"}
        ignored = {"__pycache__", "node_modules", ".next", ".git", ".venv"}

        source_files: list[str] = []
        for search_dir in [src_dir, dash_dir]:
            if not search_dir.exists():
                continue
            for item in sorted(search_dir.rglob("*")):
                if any(part in ignored for part in item.parts):
                    continue
                if item.is_file() and item.suffix in extensions:
                    source_files.append(str(item))

        metas = self.list_all()
        meta_files = {m.file_path for m in metas}

        covered = [f for f in source_files if f in meta_files]
        uncovered = [f for f in source_files if f not in meta_files]

        total = len(source_files)
        rate = (len(covered) / total * 100) if total > 0 else 0.0

        return {
            "total_source_files": total,
            "covered": len(covered),
            "uncovered": len(uncovered),
            "coverage_rate": round(rate, 1),
            "uncovered_files": [
                Path(f).name for f in uncovered[:20]
            ],
        }

    def get_dependency_graph(self) -> dict:
        """메타 데이터에서 파일 간 의존성 그래프를 생성한다."""
        metas = self.list_all()
        nodes: list[dict] = []
        edges: list[dict] = []
        seen_nodes: set[str] = set()

        for meta in metas:
            short_name = Path(meta.file_path).name
            if short_name not in seen_nodes:
                nodes.append({
                    "id": short_name,
                    "purpose": meta.purpose[:60],
                    "dep_count": len(meta.dependencies),
                })
                seen_nodes.add(short_name)

            for dep in meta.dependencies:
                dep_short = dep.split(".")[-1]
                if dep_short not in seen_nodes:
                    nodes.append({
                        "id": dep_short,
                        "purpose": "",
                        "dep_count": 0,
                    })
                    seen_nodes.add(dep_short)
                edges.append({
                    "from": short_name,
                    "to": dep_short,
                    "module": dep,
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    def _meta_to_searchable_text(self, meta: IntentMeta) -> str:
        """IntentMeta를 검색 가능한 텍스트로 변환한다."""
        parts = [
            f"File: {meta.file_path}",
            f"Purpose: {meta.purpose}",
        ]
        if meta.decisions:
            parts.append(f"Decisions: {'; '.join(meta.decisions)}")
        if meta.alternatives:
            parts.append(f"Alternatives considered: {'; '.join(meta.alternatives)}")
        if meta.constraints:
            parts.append(f"Constraints: {'; '.join(meta.constraints)}")
        if meta.dependencies:
            parts.append(f"Dependencies: {', '.join(meta.dependencies)}")
        return "\n".join(parts)

    def _get_meta_path(self, file_path: str) -> Path:
        """소스 파일에 대응하는 .meta.json 경로를 반환한다."""
        meta_dir = self._config.paths.meta_dir
        safe_name = Path(file_path).name.replace(".", "_")
        return meta_dir / f"{safe_name}.meta.json"
