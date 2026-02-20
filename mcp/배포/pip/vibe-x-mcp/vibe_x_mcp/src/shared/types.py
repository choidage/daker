"""VIBE-X 공통 타입 정의.

모든 Layer에서 사용하는 데이터 구조를 중앙에서 정의한다.
중복 타입 선언을 방지하고 인터페이스 일관성을 보장한다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class ChunkType(Enum):
    """코드 청크 유형."""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    BLOCK = "block"
    DOCUMENT = "document"


class GateStatus(Enum):
    """게이트 검증 상태."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class CodeChunk:
    """코드 청크 - 벡터 DB에 저장되는 최소 단위."""
    file_path: str
    content: str
    start_line: int
    end_line: int
    chunk_type: ChunkType
    language: str
    name: str = ""  # 함수명, 클래스명 등

    @property
    def chunk_id(self) -> str:
        return f"{self.file_path}:{self.start_line}-{self.end_line}"

    def to_metadata(self) -> dict:
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk_type": self.chunk_type.value,
            "language": self.language,
            "name": self.name,
        }


@dataclass
class SearchResult:
    """RAG 검색 결과."""
    chunk_id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    distance: float
    metadata: dict = field(default_factory=dict)

    @property
    def relevance_score(self) -> float:
        """코사인 거리(0~2)를 0~1 관련성 점수로 변환."""
        return max(0.0, 1.0 - (self.distance / 2.0))


@dataclass
class GateResult:
    """게이트 검증 결과."""
    gate_number: int
    gate_name: str
    status: GateStatus
    message: str
    details: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class IntentMeta:
    """Hidden Intent File (.meta.json) 구조."""
    file_path: str
    purpose: str
    decisions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    author: str = "vibe-x"

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "purpose": self.purpose,
            "decisions": self.decisions,
            "alternatives": self.alternatives,
            "constraints": self.constraints,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
        }


@dataclass
class IndexStats:
    """인덱싱 통계."""
    total_files: int = 0
    total_chunks: int = 0
    indexed_files: int = 0
    skipped_files: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
