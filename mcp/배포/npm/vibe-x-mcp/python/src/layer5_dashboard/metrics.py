"""Task 4.2 - Metrics Collector.

Gate 결과, 비용, 활동 로그 등 프로젝트 지표를 수집하고 저장한다.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import GateResult, GateStatus

logger = get_logger("metrics")

MAX_GATE_HISTORY = 200
DEFAULT_HEALTH_SCORE = 50
RECENT_HISTORY_WINDOW = 50
GATE_RANGE_START = 1
GATE_RANGE_END = 6
WEEKLY_DAYS = 7


@dataclass
class DailyMetric:
    """일별 지표."""
    date: str
    gate_runs: int = 0
    gate_passed: int = 0
    gate_failed: int = 0
    gate_warned: int = 0
    files_indexed: int = 0
    searches: int = 0
    decisions_extracted: int = 0
    ai_cost_usd: float = 0.0


@dataclass
class TeamMemberActivity:
    """팀원별 활동 현황."""
    name: str
    active_zone_files: int = 0
    gate_runs_today: int = 0
    last_activity: str = ""
    status: str = "offline"  # online / working / offline


class MetricsCollector:
    """프로젝트 지표 수집기.

    Gate 결과, 인덱싱 통계, 검색 횟수, 비용 등을 수집하여
    대시보드에서 활용할 수 있는 형태로 제공한다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._gate_history: list[dict] = []
        self._daily_metrics: dict[str, DailyMetric] = {}
        self._team_activity: dict[str, TeamMemberActivity] = {}
        self._state_path = self._config.paths.vibe_x_root / ".state" / "metrics.json"

        self._load_state()

    def record_gate_result(self, result: GateResult) -> None:
        """Gate 실행 결과를 기록한다."""
        today = datetime.now().strftime("%Y-%m-%d")
        metric = self._get_daily(today)

        metric.gate_runs += 1
        if result.status == GateStatus.PASSED:
            metric.gate_passed += 1
        elif result.status == GateStatus.FAILED:
            metric.gate_failed += 1
        elif result.status == GateStatus.WARNING:
            metric.gate_warned += 1

        self._gate_history.append({
            "gate": result.gate_number,
            "name": result.gate_name,
            "status": result.status.value,
            "message": result.message,
            "timestamp": datetime.now().isoformat(),
        })

        if len(self._gate_history) > MAX_GATE_HISTORY:
            self._gate_history = self._gate_history[-MAX_GATE_HISTORY:]

        self._save_state()

    def record_index(self, file_count: int) -> None:
        """인덱싱 이벤트를 기록한다."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._get_daily(today).files_indexed += file_count
        self._save_state()

    def record_search(self) -> None:
        """검색 이벤트를 기록한다."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._get_daily(today).searches += 1

    def record_decision(self) -> None:
        """설계 결정 추출 이벤트를 기록한다."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._get_daily(today).decisions_extracted += 1

    def record_cost(self, usd: float) -> None:
        """AI 비용을 기록한다."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._get_daily(today).ai_cost_usd += usd

    def update_team_member(self, name: str, **kwargs) -> None:
        """팀원 활동 정보를 업데이트한다."""
        if name not in self._team_activity:
            self._team_activity[name] = TeamMemberActivity(name=name)

        member = self._team_activity[name]
        for k, v in kwargs.items():
            if hasattr(member, k):
                setattr(member, k, v)

        member.last_activity = datetime.now().isoformat()

    def get_dashboard_data(self) -> dict:
        """대시보드에 필요한 전체 데이터를 반환한다."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_metric = self._get_daily(today)

        # 최근 7일 추이
        week_data = self._get_weekly_trend()

        # Gate 통과율 계산
        total_runs = today_metric.gate_runs
        pass_rate = (
            (today_metric.gate_passed / total_runs * 100) if total_runs > 0 else 0
        )

        # 전체 누적 통계
        cumulative = self._get_cumulative_stats()

        return {
            "timestamp": datetime.now().isoformat(),
            "today": {
                "date": today,
                "gate_runs": today_metric.gate_runs,
                "gate_passed": today_metric.gate_passed,
                "gate_failed": today_metric.gate_failed,
                "gate_warned": today_metric.gate_warned,
                "pass_rate": round(pass_rate, 1),
                "files_indexed": today_metric.files_indexed,
                "searches": today_metric.searches,
                "decisions": today_metric.decisions_extracted,
                "ai_cost": round(today_metric.ai_cost_usd, 2),
            },
            "weekly_trend": week_data,
            "cumulative": cumulative,
            "recent_gates": self._gate_history[-20:],
            "gate_pass_rates": self._get_per_gate_pass_rates(),
            "team": [
                {
                    "name": m.name,
                    "active_files": m.active_zone_files,
                    "gate_runs": m.gate_runs_today,
                    "status": m.status,
                    "last_activity": m.last_activity,
                }
                for m in self._team_activity.values()
            ],
            "health_score": self._calculate_health_score(),
        }

    def _get_per_gate_pass_rates(self) -> list[float]:
        """Gate 1~6 각각의 통과율(%)을 계산한다.

        _gate_history 에서 gate 번호별로 passed / total 비율을 구한다.
        실행 이력이 없는 Gate 는 0 으로 표시한다.
        """
        totals = {i: 0 for i in range(GATE_RANGE_START, GATE_RANGE_END + 1)}
        passed = {i: 0 for i in range(GATE_RANGE_START, GATE_RANGE_END + 1)}

        for entry in self._gate_history:
            g = entry.get("gate")
            if g is None:
                continue
            # gate_number 가 정수/문자열 모두 올 수 있으므로 안전 변환
            try:
                g = int(g)
            except (ValueError, TypeError):
                continue
            if GATE_RANGE_START <= g <= GATE_RANGE_END:
                totals[g] += 1
                if entry.get("status") == "passed":
                    passed[g] += 1

        return [
            round(passed[i] / totals[i] * 100, 1) if totals[i] > 0 else 0
            for i in range(GATE_RANGE_START, GATE_RANGE_END + 1)
        ]

    def _calculate_health_score(self) -> int:
        """프로젝트 건강 점수를 계산한다 (0-100).

        구성:
          - Gate 통과율 (40%): 최근 30건의 Gate pass 비율
          - 아키텍처 일관성 (25%): Gate 5 통과율
          - 코드 품질 (20%): Gate 4(보안/성능) 통과율
          - 활동 지수 (15%): 최근 7일간 활동 여부
        """
        recent = self._gate_history[-RECENT_HISTORY_WINDOW:]
        if not recent:
            return DEFAULT_HEALTH_SCORE

        total = len(recent)
        passed = sum(1 for g in recent if g["status"] == "passed")

        gate_pass_score = (passed / total) * 40

        arch_gates = [g for g in recent if g.get("gate") == 5]
        arch_passed = sum(1 for g in arch_gates if g["status"] == "passed")
        arch_score = (arch_passed / len(arch_gates) * 25) if arch_gates else 20

        review_gates = [g for g in recent if g.get("gate") == 4]
        review_passed = sum(
            1 for g in review_gates if g["status"] in ("passed", "warning")
        )
        quality_score = (review_passed / len(review_gates) * 20) if review_gates else 15

        active_days = self._count_active_days()
        activity_score = (active_days / WEEKLY_DAYS) * 15

        total_score = gate_pass_score + arch_score + quality_score + activity_score
        return max(0, min(100, int(total_score)))

    def get_health_breakdown(self) -> dict:
        """건강 점수의 세부 항목을 반환한다."""
        recent = self._gate_history[-RECENT_HISTORY_WINDOW:]
        if not recent:
            return {
                "overall": DEFAULT_HEALTH_SCORE,
                "gate_pass_rate": 0,
                "architecture_consistency": 0,
                "code_quality": 0,
                "activity_index": 0,
                "tech_debt_items": [],
            }

        total = len(recent)
        passed = sum(1 for g in recent if g["status"] == "passed")
        gate_rate = round(passed / total * 100, 1)

        arch_gates = [g for g in recent if g.get("gate") == 5]
        arch_passed = sum(1 for g in arch_gates if g["status"] == "passed")
        arch_pct = round(arch_passed / len(arch_gates) * 100, 1) if arch_gates else 0

        review_gates = [g for g in recent if g.get("gate") == 4]
        review_ok = sum(
            1 for g in review_gates if g["status"] in ("passed", "warning")
        )
        quality_pct = round(review_ok / len(review_gates) * 100, 1) if review_gates else 0

        active_days = self._count_active_days()

        tech_debt = self._detect_tech_debt(recent)

        return {
            "overall": self._calculate_health_score(),
            "gate_pass_rate": gate_rate,
            "architecture_consistency": arch_pct,
            "code_quality": quality_pct,
            "activity_index": round(active_days / WEEKLY_DAYS * 100, 1),
            "tech_debt_items": tech_debt,
        }

    def _count_active_days(self) -> int:
        """최근 7일 중 Gate 실행이 있었던 날 수를 반환한다."""
        count = 0
        for i in range(WEEKLY_DAYS):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if d in self._daily_metrics and self._daily_metrics[d].gate_runs > 0:
                count += 1
        return count

    def _detect_tech_debt(self, recent: list[dict]) -> list[dict]:
        """기술 부채 항목을 탐지한다."""
        debt: list[dict] = []

        failed_gates: dict[int, int] = {}
        for g in recent:
            if g.get("status") == "failed":
                gn = g.get("gate", 0)
                failed_gates[gn] = failed_gates.get(gn, 0) + 1

        debt_map = {
            1: ("구문 오류 반복", "린터/포매터 설정 강화"),
            2: ("코딩 규칙 위반 반복", "ESLint/flake8 pre-commit 추가"),
            3: ("테스트 실패 반복", "테스트 커버리지 개선"),
            4: ("보안/성능 이슈 반복", "OWASP 체크리스트 적용"),
            5: ("아키텍처 위반 반복", "ADR 문서 및 Layer 구조 리뷰"),
        }

        threshold = 3
        for gate_num, count in failed_gates.items():
            if count >= threshold and gate_num in debt_map:
                label, suggestion = debt_map[gate_num]
                debt.append({
                    "gate": gate_num,
                    "issue": label,
                    "count": count,
                    "suggestion": suggestion,
                    "severity": "high" if count >= 5 else "medium",
                })

        return debt

    def _get_daily(self, date: str) -> DailyMetric:
        """일별 지표를 반환 (없으면 생성)."""
        if date not in self._daily_metrics:
            self._daily_metrics[date] = DailyMetric(date=date)
        return self._daily_metrics[date]

    def _get_weekly_trend(self) -> list[dict]:
        """최근 7일간 추이 데이터를 반환한다."""
        trend = []
        for i in range(WEEKLY_DAYS - 1, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            m = self._daily_metrics.get(date, DailyMetric(date=date))
            trend.append({
                "date": date,
                "gate_runs": m.gate_runs,
                "passed": m.gate_passed,
                "failed": m.gate_failed,
                "cost": round(m.ai_cost_usd, 2),
                "searches": m.searches,
            })
        return trend

    def _get_cumulative_stats(self) -> dict:
        """전체 누적 통계를 반환한다."""
        total_runs = sum(m.gate_runs for m in self._daily_metrics.values())
        total_passed = sum(m.gate_passed for m in self._daily_metrics.values())
        total_cost = sum(m.ai_cost_usd for m in self._daily_metrics.values())
        total_indexed = sum(m.files_indexed for m in self._daily_metrics.values())

        return {
            "total_gate_runs": total_runs,
            "total_passed": total_passed,
            "overall_pass_rate": round(total_passed / total_runs * 100, 1) if total_runs else 0,
            "total_cost_usd": round(total_cost, 2),
            "total_files_indexed": total_indexed,
            "days_tracked": len(self._daily_metrics),
        }

    def _save_state(self) -> None:
        """상태를 파일에 저장한다."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "gate_history": self._gate_history,
            "daily_metrics": {
                k: {
                    "date": v.date,
                    "gate_runs": v.gate_runs,
                    "gate_passed": v.gate_passed,
                    "gate_failed": v.gate_failed,
                    "gate_warned": v.gate_warned,
                    "files_indexed": v.files_indexed,
                    "searches": v.searches,
                    "decisions_extracted": v.decisions_extracted,
                    "ai_cost_usd": v.ai_cost_usd,
                }
                for k, v in self._daily_metrics.items()
            },
            "saved_at": datetime.now().isoformat(),
        }
        self._state_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_gate_history(self) -> list[dict]:
        """Gate 실행 이력을 반환한다 (외부 모듈용 공개 접근자)."""
        return list(self._gate_history)

    def get_raw_daily_metrics(self) -> dict:
        """일별 지표 원본을 반환한다 (외부 모듈용 공개 접근자)."""
        return {
            k: {
                "date": v.date,
                "gate_runs": v.gate_runs,
                "gate_passed": v.gate_passed,
                "gate_failed": v.gate_failed,
                "gate_warned": v.gate_warned,
                "files_indexed": v.files_indexed,
                "searches": v.searches,
                "decisions_extracted": v.decisions_extracted,
                "ai_cost_usd": v.ai_cost_usd,
            }
            for k, v in self._daily_metrics.items()
        }

    def _load_state(self) -> None:
        """저장된 상태를 복원한다."""
        if not self._state_path.exists():
            return

        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            self._gate_history = data.get("gate_history", [])
            for k, v in data.get("daily_metrics", {}).items():
                self._daily_metrics[k] = DailyMetric(**v)
        except Exception as e:
            logger.warning(f"메트릭 상태 복원 실패: {e}")
