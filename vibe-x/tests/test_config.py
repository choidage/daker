"""설정 모듈 테스트."""

from pathlib import Path
from src.shared.config import (
    PathConfig, RagConfig, GateConfig, VibeXConfig, load_config,
)


class TestPathConfig:
    """PathConfig 경로 설정 테스트."""

    def test_default_paths(self):
        config = PathConfig()
        assert config.vibe_x_root == config.project_root / "vibe-x"
        assert config.chroma_db_path == config.vibe_x_root / ".chromadb"
        assert config.memory_path == config.vibe_x_root / "memory.md"
        assert config.coding_rules_path == config.vibe_x_root / "coding-rules.md"
        assert config.adr_dir == config.vibe_x_root / "docs" / "adr"
        assert config.meta_dir == config.vibe_x_root / ".meta"

    def test_custom_project_root(self, tmp_path):
        config = PathConfig(project_root=tmp_path)
        assert config.project_root == tmp_path
        assert config.vibe_x_root == tmp_path / "vibe-x"


class TestRagConfig:
    """RagConfig RAG 설정 테스트."""

    def test_defaults(self):
        config = RagConfig()
        assert config.collection_name == "vibe_x_codebase"
        assert config.chunk_max_lines == 50
        assert config.chunk_overlap_lines == 5
        assert config.search_top_k == 10
        assert config.embedding_model == "all-MiniLM-L6-v2"

    def test_supported_extensions(self):
        config = RagConfig()
        assert ".py" in config.supported_extensions
        assert ".ts" in config.supported_extensions
        assert ".md" in config.supported_extensions

    def test_ignored_dirs(self):
        config = RagConfig()
        assert "node_modules" in config.ignored_dirs
        assert ".git" in config.ignored_dirs
        assert "__pycache__" in config.ignored_dirs


class TestGateConfig:
    """GateConfig 게이트 설정 테스트."""

    def test_defaults(self):
        config = GateConfig()
        assert config.max_function_lines == 50
        assert config.required_type_hints is True
        assert "console.log" in config.forbidden_patterns


class TestLoadConfig:
    """load_config 함수 테스트."""

    def test_default_config(self):
        config = load_config()
        assert isinstance(config, VibeXConfig)
        assert isinstance(config.paths, PathConfig)
        assert isinstance(config.rag, RagConfig)
        assert isinstance(config.gate, GateConfig)

    def test_custom_root(self, tmp_path):
        config = load_config(project_root=tmp_path)
        assert config.paths.project_root == tmp_path
