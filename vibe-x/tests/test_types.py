"""공통 타입 테스트."""

from datetime import datetime
from src.shared.types import (
    CodeChunk, ChunkType, SearchResult, GateResult, GateStatus,
    IntentMeta, IndexStats,
)


class TestCodeChunk:
    """CodeChunk 데이터 클래스 테스트."""

    def test_chunk_id_format(self):
        chunk = CodeChunk(
            file_path="src/app.py",
            content="def hello(): pass",
            start_line=10,
            end_line=15,
            chunk_type=ChunkType.FUNCTION,
            language="python",
            name="hello",
        )
        assert chunk.chunk_id == "src/app.py:10-15"

    def test_to_metadata(self):
        chunk = CodeChunk(
            file_path="src/app.py",
            content="class Foo: pass",
            start_line=1,
            end_line=5,
            chunk_type=ChunkType.CLASS,
            language="python",
            name="Foo",
        )
        meta = chunk.to_metadata()
        assert meta["file_path"] == "src/app.py"
        assert meta["chunk_type"] == "class"
        assert meta["language"] == "python"
        assert meta["name"] == "Foo"

    def test_chunk_types(self):
        assert ChunkType.FUNCTION.value == "function"
        assert ChunkType.CLASS.value == "class"
        assert ChunkType.MODULE.value == "module"
        assert ChunkType.BLOCK.value == "block"
        assert ChunkType.DOCUMENT.value == "document"


class TestSearchResult:
    """SearchResult 테스트."""

    def test_relevance_score_close(self):
        result = SearchResult(
            chunk_id="test:1-5",
            content="test",
            file_path="test.py",
            start_line=1,
            end_line=5,
            distance=0.1,
        )
        assert result.relevance_score == pytest.approx(0.95, abs=0.01)

    def test_relevance_score_far(self):
        result = SearchResult(
            chunk_id="test:1-5",
            content="test",
            file_path="test.py",
            start_line=1,
            end_line=5,
            distance=1.5,
        )
        assert result.relevance_score == pytest.approx(0.25, abs=0.01)

    def test_relevance_score_exact(self):
        result = SearchResult(
            chunk_id="test:1-5",
            content="test",
            file_path="test.py",
            start_line=1,
            end_line=5,
            distance=0.0,
        )
        assert result.relevance_score == 1.0


class TestGateResult:
    """GateResult 테스트."""

    def test_gate_statuses(self):
        assert GateStatus.PASSED.value == "passed"
        assert GateStatus.FAILED.value == "failed"
        assert GateStatus.WARNING.value == "warning"
        assert GateStatus.SKIPPED.value == "skipped"

    def test_gate_result_defaults(self):
        result = GateResult(
            gate_number=1,
            gate_name="Test Gate",
            status=GateStatus.PASSED,
            message="OK",
        )
        assert result.details == []
        assert isinstance(result.timestamp, datetime)


class TestIntentMeta:
    """IntentMeta 테스트."""

    def test_to_dict(self):
        meta = IntentMeta(
            file_path="src/app.py",
            purpose="Main application entry point",
            decisions=["Use FastAPI"],
            alternatives=["Flask", "Django"],
        )
        d = meta.to_dict()
        assert d["file_path"] == "src/app.py"
        assert d["purpose"] == "Main application entry point"
        assert "Use FastAPI" in d["decisions"]
        assert "Flask" in d["alternatives"]
        assert d["author"] == "vibe-x"

    def test_defaults(self):
        meta = IntentMeta(file_path="test.py", purpose="test")
        assert meta.constraints == []
        assert meta.dependencies == []


class TestIndexStats:
    """IndexStats 테스트."""

    def test_defaults(self):
        stats = IndexStats()
        assert stats.total_files == 0
        assert stats.total_chunks == 0
        assert stats.errors == []
        assert stats.duration_seconds == 0.0


import pytest
