"""VIBE-X 전역 설정 모듈.

모든 Layer에서 사용하는 경로, 상수, 환경 설정을 중앙 관리한다.
하드코딩된 값 없이 이 모듈을 통해서만 설정에 접근한다.
"""

from pathlib import Path
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PathConfig:
    """프로젝트 경로 설정."""

    project_root: Path = field(default_factory=lambda: Path.cwd())

    @property
    def vibe_x_root(self) -> Path:
        return self.project_root / "vibe-x"

    @property
    def chroma_db_path(self) -> Path:
        return self.vibe_x_root / ".chromadb"

    @property
    def memory_path(self) -> Path:
        return self.vibe_x_root / "memory.md"

    @property
    def coding_rules_path(self) -> Path:
        return self.vibe_x_root / "coding-rules.md"

    @property
    def adr_dir(self) -> Path:
        return self.vibe_x_root / "docs" / "adr"

    @property
    def meta_dir(self) -> Path:
        return self.vibe_x_root / ".meta"


@dataclass(frozen=True)
class RagConfig:
    """RAG 엔진 설정."""

    collection_name: str = "vibe_x_codebase"
    chunk_max_lines: int = 50
    chunk_overlap_lines: int = 5
    search_top_k: int = 10
    embedding_model: str = "all-MiniLM-L6-v2"
    supported_extensions: tuple = (
        ".py", ".ts", ".tsx", ".js", ".jsx",
        ".md", ".json", ".yaml", ".yml",
        ".html", ".css", ".sql",
    )
    ignored_dirs: tuple = (
        "node_modules", ".git", "__pycache__", ".venv",
        "venv", "dist", "build", ".chromadb", ".meta",
    )


@dataclass(frozen=True)
class GateConfig:
    """품질 게이트 설정."""

    max_function_lines: int = 50
    required_type_hints: bool = True
    forbidden_patterns: tuple = (
        "console.log",
        "# type: ignore",
        "noqa",
        "TODO: hack",
    )


@dataclass(frozen=True)
class VibeXConfig:
    """VIBE-X 통합 설정."""

    paths: PathConfig = field(default_factory=PathConfig)
    rag: RagConfig = field(default_factory=RagConfig)
    gate: GateConfig = field(default_factory=GateConfig)
    version: str = "0.5.0"


def load_config(project_root: Path | None = None) -> VibeXConfig:
    """설정을 로드한다. project_root가 주어지면 해당 경로를 기준으로 한다."""
    if project_root:
        return VibeXConfig(paths=PathConfig(project_root=project_root))
    return VibeXConfig()
