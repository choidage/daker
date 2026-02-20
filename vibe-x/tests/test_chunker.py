"""코드 청킹 모듈 테스트."""

from pathlib import Path
from src.shared.types import ChunkType
from src.layer2_rag.chunker import CodeChunker, EXTENSION_TO_LANGUAGE


class TestCodeChunker:
    """CodeChunker 테스트."""

    def test_python_structural_chunking(self, config, sample_python_file):
        """Python 파일의 구조적 청킹을 검증한다."""
        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(sample_python_file)

        assert len(chunks) > 0

        # 클래스와 함수가 모두 감지되어야 함
        chunk_types = {c.chunk_type for c in chunks}
        assert ChunkType.CLASS in chunk_types or ChunkType.FUNCTION in chunk_types

        # 청크에 이름이 있어야 함
        names = [c.name for c in chunks if c.name]
        assert len(names) > 0

    def test_markdown_as_document(self, config, sample_markdown_file):
        """Markdown 파일은 하나의 문서 청크로 처리된다."""
        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(sample_markdown_file)

        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.DOCUMENT
        assert chunks[0].language == "markdown"

    def test_empty_file(self, config, tmp_project):
        """빈 파일은 빈 청크 목록을 반환한다."""
        empty_file = tmp_project / "empty.py"
        empty_file.write_text("", encoding="utf-8")

        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(empty_file)
        assert chunks == []

    def test_nonexistent_file(self, config, tmp_project):
        """존재하지 않는 파일은 빈 목록을 반환한다."""
        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(tmp_project / "nonexistent.py")
        assert chunks == []

    def test_fallback_to_block_chunking(self, config, tmp_project):
        """구조 인식 불가 시 블록 청킹으로 폴백한다."""
        code = "\n".join([f"x_{i} = {i}" for i in range(100)])
        file_path = tmp_project / "flat_code.py"
        file_path.write_text(code, encoding="utf-8")

        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(file_path)
        assert len(chunks) > 0
        assert all(c.chunk_type == ChunkType.BLOCK for c in chunks)

    def test_chunk_content_not_empty(self, config, sample_python_file):
        """모든 청크의 content가 비어있지 않아야 한다."""
        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(sample_python_file)
        for chunk in chunks:
            assert chunk.content.strip() != ""

    def test_chunk_line_numbers_valid(self, config, sample_python_file):
        """청크의 라인 번호가 유효해야 한다."""
        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(sample_python_file)
        for chunk in chunks:
            assert chunk.start_line >= 1
            assert chunk.end_line >= chunk.start_line

    def test_extension_to_language_mapping(self):
        """확장자-언어 매핑이 올바르게 동작한다."""
        assert EXTENSION_TO_LANGUAGE[".py"] == "python"
        assert EXTENSION_TO_LANGUAGE[".ts"] == "typescript"
        assert EXTENSION_TO_LANGUAGE[".js"] == "javascript"
        assert EXTENSION_TO_LANGUAGE[".md"] == "markdown"

    def test_json_file_as_document(self, config, tmp_project):
        """JSON 파일은 문서로 처리된다."""
        json_file = tmp_project / "data.json"
        json_file.write_text('{"key": "value"}', encoding="utf-8")

        chunker = CodeChunker(config)
        chunks = chunker.chunk_file(json_file)
        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.DOCUMENT
        assert chunks[0].language == "json"
