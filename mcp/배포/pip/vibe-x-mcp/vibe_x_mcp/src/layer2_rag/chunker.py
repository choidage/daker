"""Task 2.2 - 코드 청킹 모듈.

소스 코드를 의미 있는 단위(함수, 클래스, 블록)로 분할한다.
각 청크는 벡터 DB에 저장되는 최소 검색 단위가 된다.
"""

import re
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import CodeChunk, ChunkType

logger = get_logger("chunker")

# 언어별 확장자 매핑
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
}

# 언어별 함수/클래스 패턴
PATTERNS: dict[str, dict[str, re.Pattern]] = {
    "python": {
        "function": re.compile(r"^(async\s+)?def\s+(\w+)\s*\(", re.MULTILINE),
        "class": re.compile(r"^class\s+(\w+)", re.MULTILINE),
    },
    "typescript": {
        "function": re.compile(
            r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)|"
            r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(",
            re.MULTILINE,
        ),
        "class": re.compile(r"^(?:export\s+)?class\s+(\w+)", re.MULTILINE),
    },
    "javascript": {
        "function": re.compile(
            r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)|"
            r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(",
            re.MULTILINE,
        ),
        "class": re.compile(r"^(?:export\s+)?class\s+(\w+)", re.MULTILINE),
    },
}


class CodeChunker:
    """코드를 의미 있는 청크로 분할하는 엔진.

    전략:
    1. 함수/클래스 단위 분할 (구조적 청킹)
    2. 구조 인식 불가 시 고정 라인 수 블록 분할 (폴백)
    3. 문서 파일은 전체를 하나의 청크로 처리
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()

    def chunk_file(self, file_path: Path) -> list[CodeChunk]:
        """파일을 청크 목록으로 분할한다.

        Args:
            file_path: 대상 파일 경로

        Returns:
            분할된 코드 청크 목록
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"파일 읽기 실패: {file_path} - {e}")
            return []

        if not content.strip():
            return []

        language = EXTENSION_TO_LANGUAGE.get(file_path.suffix, "text")
        rel_path = str(file_path)

        # 문서 파일은 전체를 하나의 청크로
        if language in ("markdown", "json", "yaml", "html", "css"):
            return self._chunk_as_document(rel_path, content, language)

        # 코드 파일은 구조적 청킹 시도
        chunks = self._chunk_by_structure(rel_path, content, language)

        # 구조적 청킹 결과가 없으면 블록 청킹으로 폴백
        if not chunks:
            chunks = self._chunk_by_lines(rel_path, content, language)

        return chunks

    def _chunk_as_document(
        self, file_path: str, content: str, language: str
    ) -> list[CodeChunk]:
        """파일 전체를 하나의 문서 청크로 생성한다."""
        lines = content.split("\n")
        return [
            CodeChunk(
                file_path=file_path,
                content=content[:3000],  # 문서는 3000자 제한
                start_line=1,
                end_line=len(lines),
                chunk_type=ChunkType.DOCUMENT,
                language=language,
                name=Path(file_path).name,
            )
        ]

    def _chunk_by_structure(
        self, file_path: str, content: str, language: str
    ) -> list[CodeChunk]:
        """함수/클래스 단위로 구조적 청킹을 수행한다."""
        patterns = PATTERNS.get(language)
        if not patterns:
            return []

        lines = content.split("\n")
        chunks: list[CodeChunk] = []
        boundaries: list[tuple[int, str, ChunkType]] = []

        # 함수/클래스 시작 위치 탐지
        for chunk_type_str, pattern in patterns.items():
            chunk_type = (
                ChunkType.FUNCTION if chunk_type_str == "function" else ChunkType.CLASS
            )
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                # 매칭된 그룹에서 이름 추출
                name = next((g for g in match.groups() if g), "anonymous")
                boundaries.append((line_num, name, chunk_type))

        if not boundaries:
            return []

        # 시작 라인 기준 정렬
        boundaries.sort(key=lambda b: b[0])

        # 각 경계 사이를 청크로 분할
        for i, (start_line, name, chunk_type) in enumerate(boundaries):
            if i + 1 < len(boundaries):
                end_line = boundaries[i + 1][0] - 1
            else:
                end_line = len(lines)

            chunk_content = "\n".join(lines[start_line - 1 : end_line])

            if chunk_content.strip():
                chunks.append(
                    CodeChunk(
                        file_path=file_path,
                        content=chunk_content,
                        start_line=start_line,
                        end_line=end_line,
                        chunk_type=chunk_type,
                        language=language,
                        name=name,
                    )
                )

        return chunks

    def _chunk_by_lines(
        self, file_path: str, content: str, language: str
    ) -> list[CodeChunk]:
        """고정 라인 수 기반 블록 청킹 (폴백 전략)."""
        lines = content.split("\n")
        max_lines = self._config.rag.chunk_max_lines
        overlap = self._config.rag.chunk_overlap_lines
        chunks: list[CodeChunk] = []

        start = 0
        while start < len(lines):
            end = min(start + max_lines, len(lines))
            chunk_content = "\n".join(lines[start:end])

            if chunk_content.strip():
                chunks.append(
                    CodeChunk(
                        file_path=file_path,
                        content=chunk_content,
                        start_line=start + 1,
                        end_line=end,
                        chunk_type=ChunkType.BLOCK,
                        language=language,
                    )
                )

            start = end - overlap if end < len(lines) else len(lines)

        return chunks
