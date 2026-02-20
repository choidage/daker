"""Task 3.5 - Decision Extractor Agent.

AI 대화 로그에서 설계 결정을 자동으로 추출하여 ADR에 반영한다.
"""

import re
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger

logger = get_logger("decision")

# 설계 결정 탐지 패턴
DECISION_TRIGGERS = [
    re.compile(r"(?:결정|선택|채택|사용)(?:했|한다|하기로|하겠)", re.I),
    re.compile(r"(?:대신|대안|비교).*(?:선택|채택)", re.I),
    re.compile(r"(?:이유|근거|때문).*(?:선택|사용|채택)", re.I),
    re.compile(r"(?:A|B)\s*(?:대신|말고)\s*(?:A|B)", re.I),
    re.compile(r"(?:장단점|트레이드오프|trade-?off)", re.I),
    re.compile(r"ADR|아키텍처\s*결정", re.I),
]


@dataclass
class Decision:
    """추출된 설계 결정."""
    title: str
    context: str
    decision: str
    rationale: str = ""
    alternatives: list[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.now)
    source: str = "conversation"
    confidence: float = 0.0

    def to_adr_markdown(self, adr_number: int) -> str:
        """ADR 마크다운 형식으로 변환한다."""
        alts = "\n".join(f"- {a}" for a in self.alternatives) if self.alternatives else "- N/A"
        return f"""# ADR-{adr_number:03d}: {self.title}

> **상태:** 제안
> **작성일:** {self.extracted_at.strftime('%Y.%m.%d')}
> **추출 방법:** Decision Extractor Agent (신뢰도: {self.confidence:.0%})

---

## 컨텍스트

{self.context}

## 고려한 대안

{alts}

## 결정

{self.decision}

## 근거

{self.rationale}
"""


class DecisionExtractor:
    """AI 대화에서 설계 결정을 자동 추출하는 Agent.

    대화 텍스트를 분석하여 설계 결정 패턴을 탐지하고,
    구조화된 Decision 객체로 변환한 뒤 ADR에 자동 반영한다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._decisions: list[Decision] = []

    def extract_from_text(self, text: str, source: str = "conversation") -> list[Decision]:
        """텍스트에서 설계 결정을 추출한다.

        Args:
            text: 분석할 텍스트 (대화 로그, 코멘트 등)
            source: 출처 식별자

        Returns:
            추출된 설계 결정 목록
        """
        decisions: list[Decision] = []
        paragraphs = self._split_paragraphs(text)

        for para in paragraphs:
            confidence = self._calculate_confidence(para)
            if confidence >= 0.3:  # 30% 이상이면 결정으로 인식
                decision = self._parse_decision(para, source, confidence)
                if decision:
                    decisions.append(decision)
                    self._decisions.append(decision)

        if decisions:
            logger.info(f"설계 결정 {len(decisions)}개 추출 (출처: {source})")

        return decisions

    def save_as_adr(self, decision: Decision) -> Path | None:
        """추출된 결정을 ADR 파일로 저장한다."""
        adr_dir = self._config.paths.adr_dir
        adr_dir.mkdir(parents=True, exist_ok=True)

        # 기존 ADR 번호 확인
        existing = sorted(adr_dir.glob("*.md"))
        next_num = len(existing) + 1

        # 파일명 생성
        safe_title = re.sub(r"[^\w\s-]", "", decision.title)[:40].strip().replace(" ", "-")
        filename = f"{next_num:03d}-{safe_title}.md"
        adr_path = adr_dir / filename

        try:
            adr_path.write_text(
                decision.to_adr_markdown(next_num),
                encoding="utf-8",
            )
            logger.info(f"ADR 저장: {filename}")
            return adr_path
        except OSError as e:
            logger.warning(f"ADR 저장 실패: {e}")
            return None

    def get_all_decisions(self) -> list[Decision]:
        """모든 추출된 결정을 반환한다."""
        return list(self._decisions)

    def _split_paragraphs(self, text: str) -> list[str]:
        """텍스트를 단락으로 분할한다."""
        # 빈 줄 또는 마크다운 헤더로 분할
        blocks = re.split(r"\n\s*\n|\n#{1,3}\s+", text)
        return [b.strip() for b in blocks if b.strip() and len(b.strip()) > 20]

    def _calculate_confidence(self, text: str) -> float:
        """텍스트가 설계 결정을 포함할 확률을 계산한다."""
        score = 0.0
        matched_patterns = 0

        for pattern in DECISION_TRIGGERS:
            if pattern.search(text):
                matched_patterns += 1

        if matched_patterns == 0:
            return 0.0

        # 패턴 매칭 수에 따른 기본 점수
        score += min(matched_patterns * 0.2, 0.6)

        # 길이 보너스 (50자 이상이면 더 신뢰)
        if len(text) > 100:
            score += 0.1
        if len(text) > 200:
            score += 0.1

        # 기술 용어 보너스
        tech_terms = ["API", "DB", "패턴", "라이브러리", "프레임워크", "아키텍처"]
        tech_count = sum(1 for term in tech_terms if term.lower() in text.lower())
        score += min(tech_count * 0.05, 0.2)

        return min(score, 1.0)

    def _parse_decision(self, text: str, source: str, confidence: float) -> Decision | None:
        """텍스트에서 결정 구조를 파싱한다."""
        lines = text.split("\n")
        if not lines:
            return None

        # 첫 줄을 제목으로, 나머지를 컨텍스트+결정으로 분류
        title = lines[0][:80].strip()
        if len(title) < 5:
            title = text[:80].strip()

        body = " ".join(lines[1:]) if len(lines) > 1 else text

        return Decision(
            title=title,
            context=body[:300],
            decision=text[:500],
            rationale=self._extract_rationale(text),
            source=source,
            confidence=confidence,
        )

    def _extract_rationale(self, text: str) -> str:
        """근거/이유 부분을 추출한다."""
        reason_patterns = [
            re.compile(r"(?:이유|근거|때문)[:\s]*(.+?)(?:\n|$)", re.I),
            re.compile(r"(?:왜냐하면|because)[:\s]*(.+?)(?:\n|$)", re.I),
        ]

        for pattern in reason_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()[:200]

        return ""
