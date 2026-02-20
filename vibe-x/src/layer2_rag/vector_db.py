"""Task 2.1 - Vector DB 환경 구축.

ChromaDB를 사용한 벡터 저장소 관리.
코드 청크의 저장, 검색, 삭제를 담당한다.
"""

import chromadb
from chromadb.config import Settings

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import CodeChunk, SearchResult

logger = get_logger("vector-db")


class VectorStore:
    """ChromaDB 기반 벡터 저장소.

    코드 청크를 벡터화하여 저장하고 시맨틱 검색을 지원한다.
    PersistentClient를 사용하여 데이터가 디스크에 영속 저장된다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None

    @property
    def client(self) -> chromadb.ClientAPI:
        """ChromaDB 클라이언트를 지연 초기화한다."""
        if self._client is None:
            db_path = str(self._config.paths.chroma_db_path)
            self._config.paths.chroma_db_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=db_path)
            logger.info(f"ChromaDB 연결 완료: [bold]{db_path}[/bold]")
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        """컬렉션을 지연 초기화한다. 없으면 자동 생성."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self._config.rag.collection_name,
                metadata={
                    "description": "VIBE-X codebase knowledge base",
                    "hnsw:space": "cosine",
                },
            )
            count = self._collection.count()
            logger.info(
                f"컬렉션 '{self._config.rag.collection_name}' 로드 완료 "
                f"(문서 {count}개)"
            )
        return self._collection

    def add_chunks(self, chunks: list[CodeChunk]) -> int:
        """코드 청크 목록을 벡터 DB에 추가한다.

        Args:
            chunks: 저장할 코드 청크 목록

        Returns:
            실제 추가된 청크 수
        """
        if not chunks:
            return 0

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.to_metadata() for chunk in chunks]

        # 기존 ID와 중복되면 upsert로 처리
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"청크 {len(chunks)}개 저장 완료")
        return len(chunks)

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        """자연어 쿼리로 시맨틱 검색을 수행한다.

        Args:
            query: 검색 질의 (자연어)
            top_k: 반환할 최대 결과 수

        Returns:
            관련성 순으로 정렬된 검색 결과 목록
        """
        if not query.strip():
            logger.warning("빈 검색 쿼리")
            return []

        k = top_k or self._config.rag.search_top_k
        count = self.collection.count()

        if count == 0:
            logger.warning("벡터 DB가 비어 있음. 먼저 인덱싱을 실행하세요.")
            return []

        # 결과 수가 전체 문서 수보다 클 수 없음
        k = min(k, count)

        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        search_results: list[SearchResult] = []
        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i]
            search_results.append(
                SearchResult(
                    chunk_id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    file_path=metadata.get("file_path", ""),
                    start_line=metadata.get("start_line", 0),
                    end_line=metadata.get("end_line", 0),
                    distance=results["distances"][0][i],
                    metadata=metadata,
                )
            )

        logger.info(f"검색 완료: '{query[:40]}...' → {len(search_results)}개 결과")
        return search_results

    def delete_by_file(self, file_path: str) -> None:
        """특정 파일의 모든 청크를 삭제한다 (증분 인덱싱용)."""
        self.collection.delete(where={"file_path": file_path})
        logger.info(f"삭제 완료: {file_path}")

    def get_stats(self) -> dict:
        """벡터 DB 통계를 반환한다."""
        count = self.collection.count()
        return {
            "collection_name": self._config.rag.collection_name,
            "total_chunks": count,
            "db_path": str(self._config.paths.chroma_db_path),
        }

    def reset(self) -> None:
        """컬렉션을 완전히 초기화한다. 주의: 모든 데이터가 삭제됨."""
        self.client.delete_collection(self._config.rag.collection_name)
        self._collection = None
        logger.warning("컬렉션 초기화 완료 - 모든 데이터 삭제됨")
