"""Task 2.3 - 코드베이스 자동 인덱싱 모듈.

프로젝트 전체를 스캔하여 벡터 DB에 인덱싱한다.
증분 인덱싱을 지원하여 변경된 파일만 재처리한다.
"""

import time
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import IndexStats
from src.layer2_rag.vector_db import VectorStore
from src.layer2_rag.chunker import CodeChunker

logger = get_logger("indexer")


class CodebaseIndexer:
    """코드베이스를 벡터 DB에 인덱싱하는 엔진.

    기능:
    - 전체 인덱싱: 프로젝트 내 모든 지원 파일을 인덱싱
    - 증분 인덱싱: 변경된 파일만 재인덱싱
    - 파일 필터링: 지원 확장자 + 무시 디렉토리 적용
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._store = VectorStore(self._config)
        self._chunker = CodeChunker(self._config)

    def index_project(self, project_path: Path | None = None) -> IndexStats:
        """프로젝트 전체를 인덱싱한다.

        Args:
            project_path: 프로젝트 루트 경로 (None이면 현재 디렉토리)

        Returns:
            인덱싱 통계
        """
        root = project_path or self._config.paths.project_root
        start_time = time.time()
        stats = IndexStats()

        logger.info(f"인덱싱 시작: [bold]{root}[/bold]")

        # 대상 파일 수집
        files = self._collect_files(root)
        stats.total_files = len(files)
        logger.info(f"대상 파일: {stats.total_files}개")

        # 파일별 청킹 + 저장
        for file_path in files:
            try:
                chunks = self._chunker.chunk_file(file_path)
                if chunks:
                    # 증분 인덱싱: 기존 청크 삭제 후 재저장
                    self._store.delete_by_file(str(file_path))
                    self._store.add_chunks(chunks)
                    stats.indexed_files += 1
                    stats.total_chunks += len(chunks)
                else:
                    stats.skipped_files += 1
            except Exception as e:
                error_msg = f"{file_path}: {e}"
                stats.errors.append(error_msg)
                logger.warning(f"인덱싱 실패 - {error_msg}")

        stats.duration_seconds = round(time.time() - start_time, 2)
        self._log_stats(stats)
        return stats

    def index_file(self, file_path: Path) -> int:
        """단일 파일을 인덱싱한다 (Git Hook 연동용).

        Args:
            file_path: 인덱싱할 파일 경로

        Returns:
            생성된 청크 수
        """
        if not self._is_supported(file_path):
            return 0

        chunks = self._chunker.chunk_file(file_path)
        if not chunks:
            return 0

        self._store.delete_by_file(str(file_path))
        self._store.add_chunks(chunks)
        logger.info(f"파일 인덱싱: {file_path} → {len(chunks)}개 청크")
        return len(chunks)

    def _collect_files(self, root: Path) -> list[Path]:
        """인덱싱 대상 파일을 수집한다."""
        files: list[Path] = []
        ignored = set(self._config.rag.ignored_dirs)
        supported = set(self._config.rag.supported_extensions)

        for item in root.rglob("*"):
            # 무시 디렉토리 필터링
            if any(part in ignored for part in item.parts):
                continue

            # 파일만, 지원 확장자만
            if item.is_file() and item.suffix in supported:
                files.append(item)

        return sorted(files)

    def _is_supported(self, file_path: Path) -> bool:
        """파일이 인덱싱 대상인지 확인한다."""
        ignored = set(self._config.rag.ignored_dirs)
        if any(part in ignored for part in file_path.parts):
            return False
        return file_path.suffix in self._config.rag.supported_extensions

    def _log_stats(self, stats: IndexStats) -> None:
        """인덱싱 통계를 로그로 출력한다."""
        logger.info(
            f"인덱싱 완료 - "
            f"파일: {stats.indexed_files}/{stats.total_files}, "
            f"청크: {stats.total_chunks}, "
            f"스킵: {stats.skipped_files}, "
            f"에러: {len(stats.errors)}, "
            f"소요: {stats.duration_seconds}s"
        )
