"""Task 2.6 - RAG 검색 엔진.

자연어 질의로 코드베이스에서 관련 코드를 찾는다.
벡터 유사도 검색 + 메타데이터 필터링을 결합한다.
"""

from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import SearchResult
from src.layer2_rag.vector_db import VectorStore

logger = get_logger("searcher")


class CodeSearcher:
    """코드베이스 시맨틱 검색 엔진.

    사용 예:
        searcher = CodeSearcher()
        results = searcher.search("인증 미들웨어는 어디에 있나?")
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._store = VectorStore(self._config)

    def search(
        self,
        query: str,
        top_k: int | None = None,
        file_filter: str | None = None,
        language_filter: str | None = None,
    ) -> list[SearchResult]:
        """시맨틱 검색을 수행한다.

        Args:
            query: 자연어 검색 질의
            top_k: 반환할 최대 결과 수
            file_filter: 특정 파일 경로로 필터링 (부분 매칭)
            language_filter: 특정 언어로 필터링

        Returns:
            관련성 순으로 정렬된 검색 결과
        """
        results = self._store.search(query, top_k)

        # 메타데이터 기반 필터링
        if file_filter:
            results = [
                r for r in results if file_filter in r.file_path
            ]
        if language_filter:
            results = [
                r for r in results
                if r.metadata.get("language") == language_filter
            ]

        return results

    def search_similar_code(self, code_snippet: str, top_k: int = 5) -> list[SearchResult]:
        """코드 스니펫과 유사한 코드를 찾는다.

        Args:
            code_snippet: 참조 코드
            top_k: 반환 결과 수

        Returns:
            유사 코드 검색 결과
        """
        return self._store.search(code_snippet, top_k)

    def format_results(self, results: list[SearchResult]) -> str:
        """검색 결과를 읽기 좋은 형태로 포맷팅한다."""
        if not results:
            return "검색 결과가 없습니다."

        output_parts: list[str] = []
        for i, result in enumerate(results, 1):
            score = f"{result.relevance_score:.0%}"
            location = f"{result.file_path}:{result.start_line}-{result.end_line}"
            chunk_type = result.metadata.get("chunk_type", "unknown")
            name = result.metadata.get("name", "")

            header = f"[{i}] {score} - {location}"
            if name:
                header += f" ({chunk_type}: {name})"

            # 코드 미리보기 (최대 10줄)
            preview_lines = result.content.split("\n")[:10]
            preview = "\n".join(preview_lines)
            if len(result.content.split("\n")) > 10:
                preview += "\n    ... (생략)"

            output_parts.append(f"{header}\n{preview}")

        return "\n\n---\n\n".join(output_parts)
