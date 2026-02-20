"""Task 4.5 - Feedback Loop Automation.

생성 -> 검증 -> 기록 -> 학습의 순환 파이프라인.
반복 실패 패턴을 탐지하고 팀 규칙 업데이트를 제안한다.
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger

logger = get_logger("feedback")


class FeedbackLoop:
    """품질 개선 피드백 루프.

    Gate 실패 패턴을 분석하여 팀 규칙 업데이트를 제안하고,
    월별 자동 리포트를 생성한다.
    """

    def __init__(
        self,
        config: VibeXConfig | None = None,
        metrics_collector=None,
    ) -> None:
        self._config = config or load_config()
        self._metrics = metrics_collector  # MetricsCollector 주입 (중복 읽기 방지)
        self._state_path = self._config.paths.vibe_x_root / ".state" / "metrics.json"

    def analyze_failure_patterns(self) -> dict:
        """반복 실패 패턴을 분석한다."""
        history = self._load_gate_history()
        if not history:
            return {
                "total_failures": 0,
                "total_runs": 0,
                "failure_rate": 0.0,
                "patterns": [],
                "top_messages": [],
                "suggestions": ["게이트 실행 이력이 없습니다. 파이프라인을 실행해 주세요."],
            }

        # 실패 유형별 카운트
        failures = [g for g in history if g.get("status") == "failed"]
        fail_by_gate = Counter(g.get("name", "unknown") for g in failures)
        fail_messages = Counter()
        for g in failures:
            msg = g.get("message", "")[:80]
            if msg:
                fail_messages[msg] += 1

        patterns = [
            {"gate": gate, "count": count}
            for gate, count in fail_by_gate.most_common(5)
        ]

        # 규칙 제안 생성
        suggestions = self._generate_suggestions(fail_by_gate, fail_messages)

        return {
            "total_failures": len(failures),
            "total_runs": len(history),
            "failure_rate": round(len(failures) / len(history) * 100, 1) if history else 0,
            "patterns": patterns,
            "top_messages": [
                {"message": msg, "count": cnt}
                for msg, cnt in fail_messages.most_common(5)
            ],
            "suggestions": suggestions,
        }

    def generate_monthly_report(self) -> dict:
        """월별 자동 리포트를 생성한다."""
        history = self._load_gate_history()
        daily = self._load_daily_metrics()
        now = datetime.now()
        month_str = now.strftime("%Y-%m")

        # 이번 달 데이터만 필터
        month_history = [
            g for g in history
            if g.get("timestamp", "").startswith(month_str)
        ]
        month_daily = {
            k: v for k, v in daily.items()
            if k.startswith(month_str)
        }

        total_runs = len(month_history)
        passed = sum(1 for g in month_history if g.get("status") == "passed")
        total_cost = sum(d.get("ai_cost_usd", 0) for d in month_daily.values())
        total_indexed = sum(d.get("files_indexed", 0) for d in month_daily.values())
        total_searches = sum(d.get("searches", 0) for d in month_daily.values())
        total_decisions = sum(d.get("decisions_extracted", 0) for d in month_daily.values())

        report = {
            "month": month_str,
            "generated_at": now.isoformat(),
            "summary": {
                "total_gate_runs": total_runs,
                "pass_rate": round(passed / total_runs * 100, 1) if total_runs else 0,
                "total_cost_usd": round(total_cost, 2),
                "total_files_indexed": total_indexed,
                "total_searches": total_searches,
                "total_decisions": total_decisions,
                "active_days": len(month_daily),
            },
            "failure_analysis": self.analyze_failure_patterns(),
            "recommendations": self._generate_suggestions(
                Counter(g.get("name") for g in month_history if g.get("status") == "failed"),
                Counter(),
            ),
        }

        # 리포트 저장
        report_dir = self._config.paths.vibe_x_root / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"monthly-{month_str}.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info(f"월별 리포트 생성: {report_path}")
        return report

    def _generate_suggestions(
        self,
        fail_by_gate: Counter,
        fail_messages: Counter,
    ) -> list[str]:
        """실패 패턴 기반 규칙 업데이트를 제안한다."""
        suggestions: list[str] = []

        if fail_by_gate.get("Syntax Agent", 0) > 5:
            suggestions.append("구문 오류가 반복됨 - 저장 시 자동 포맷팅(prettier/black) 설정 권장")

        if fail_by_gate.get("Rules Agent", 0) > 5:
            suggestions.append("코딩 규칙 위반 반복 - ESLint/flake8 사전 검사 강화 권장")

        if fail_by_gate.get("Review Agent", 0) > 3:
            suggestions.append("보안/성능 이슈 반복 - 팀 보안 교육 또는 OWASP 체크리스트 공유 권장")

        if fail_by_gate.get("Architecture Agent", 0) > 3:
            suggestions.append("아키텍처 규칙 위반 반복 - ADR 문서 업데이트 및 팀 리뷰 권장")

        if fail_by_gate.get("Collision Agent", 0) > 3:
            suggestions.append("작업 충돌 빈번 - Work Zone 선언 습관화 또는 모듈 분리 검토 권장")

        if not suggestions:
            suggestions.append("현재 특별한 반복 패턴 없음 - 양호한 상태")

        return suggestions

    def _load_gate_history(self) -> list[dict]:
        """Gate 이력을 로드한다 (MetricsCollector 주입 시 위임)."""
        if self._metrics is not None:
            return self._metrics.get_gate_history()

        if not self._state_path.exists():
            return []
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            return data.get("gate_history", [])
        except Exception:
            return []

    def _load_daily_metrics(self) -> dict:
        """일별 지표를 로드한다 (MetricsCollector 주입 시 위임)."""
        if self._metrics is not None:
            return self._metrics.get_raw_daily_metrics()

        if not self._state_path.exists():
            return {}
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            return data.get("daily_metrics", {})
        except Exception:
            return {}
