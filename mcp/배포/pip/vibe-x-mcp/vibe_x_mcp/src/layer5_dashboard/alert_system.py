"""Task 4.2 - Alert System.

임계값 기반 경고 + WebSocket 푸시 알림.
Gate 실패율, AI 비용, 아키텍처 위반 등의 지표가
설정된 임계값을 초과하면 자동으로 팀에 경고한다.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger

logger = get_logger("alerts")


class AlertLevel(Enum):
    """경고 수준."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """경고 객체."""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold: float
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
        }


GATE_FAIL_RATE_WARNING = 30.0
GATE_FAIL_RATE_CRITICAL = 50.0
DAILY_COST_WARNING_USD = 5.0
DAILY_COST_CRITICAL_USD = 20.0
ARCH_VIOLATION_THRESHOLD = 3
MAX_ALERTS_RETAINED = 100
ALERTS_PERSIST_FILE = "alerts_store.json"


class AlertSystem:
    """임계값 기반 경고 시스템.

    메트릭 데이터를 평가하여 임계값 초과 시 Alert를 생성하고
    WebSocket을 통해 실시간 푸시 알림을 전송한다.
    """

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._alerts: list[Alert] = []
        self._alert_counter = 0
        self._persist_path = self._config.paths.meta_dir / ALERTS_PERSIST_FILE
        self._load_from_disk()

    def evaluate_metrics(self, dashboard_data: dict) -> list[Alert]:
        """대시보드 데이터를 평가하여 경고를 생성한다."""
        new_alerts: list[Alert] = []

        today = dashboard_data.get("today", {})
        new_alerts.extend(self._check_gate_fail_rate(today))
        new_alerts.extend(self._check_cost(today))
        new_alerts.extend(self._check_health_score(dashboard_data))

        for alert in new_alerts:
            self._alerts.append(alert)
            logger.warning(f"[{alert.level.value}] {alert.title}: {alert.message}")

        self._trim_alerts()
        return new_alerts

    def evaluate_gate_result(self, gate_number: int, status: str, details: list[str]) -> list[Alert]:
        """개별 Gate 결과를 즉시 평가한다."""
        new_alerts: list[Alert] = []

        if status == "failed" and gate_number in (1, 2):
            alert = self._create_alert(
                level=AlertLevel.CRITICAL,
                title=f"Gate {gate_number} Failed",
                message=f"기본 품질 Gate 실패 - 즉시 수정 필요",
                metric_name=f"gate_{gate_number}_status",
                current_value=0,
                threshold=1,
            )
            new_alerts.append(alert)

        arch_violations = [d for d in details if "ARCH-001" in d]
        if len(arch_violations) >= ARCH_VIOLATION_THRESHOLD:
            alert = self._create_alert(
                level=AlertLevel.WARNING,
                title="Architecture Violations",
                message=f"Layer 의존성 위반 {len(arch_violations)}건 감지",
                metric_name="arch_violations",
                current_value=len(arch_violations),
                threshold=ARCH_VIOLATION_THRESHOLD,
            )
            new_alerts.append(alert)

        for alert in new_alerts:
            self._alerts.append(alert)

        self._trim_alerts()
        return new_alerts

    def get_active_alerts(self) -> list[dict]:
        """미확인 경고 목록을 반환한다."""
        return [
            a.to_dict() for a in self._alerts
            if not a.acknowledged
        ]

    def get_all_alerts(self) -> list[dict]:
        """전체 경고 목록을 반환한다."""
        return [a.to_dict() for a in self._alerts]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """경고를 확인(dismiss)한다."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self._save_to_disk()
                return True
        return False

    def acknowledge_all(self) -> int:
        """모든 미확인 경고를 확인한다."""
        count = 0
        for alert in self._alerts:
            if not alert.acknowledged:
                alert.acknowledged = True
                count += 1
        if count > 0:
            self._save_to_disk()
        return count

    def _check_gate_fail_rate(self, today: dict) -> list[Alert]:
        """Gate 실패율을 검사한다."""
        alerts: list[Alert] = []
        total = today.get("gate_runs", 0)
        failed = today.get("gate_failed", 0)

        if total < 5:
            return alerts

        fail_rate = (failed / total) * 100

        if fail_rate >= GATE_FAIL_RATE_CRITICAL:
            alerts.append(self._create_alert(
                level=AlertLevel.CRITICAL,
                title="Critical Gate Failure Rate",
                message=f"오늘 Gate 실패율 {fail_rate:.0f}% - 코드 품질 긴급 점검 필요",
                metric_name="gate_fail_rate",
                current_value=fail_rate,
                threshold=GATE_FAIL_RATE_CRITICAL,
            ))
        elif fail_rate >= GATE_FAIL_RATE_WARNING:
            alerts.append(self._create_alert(
                level=AlertLevel.WARNING,
                title="High Gate Failure Rate",
                message=f"오늘 Gate 실패율 {fail_rate:.0f}% - 주의 필요",
                metric_name="gate_fail_rate",
                current_value=fail_rate,
                threshold=GATE_FAIL_RATE_WARNING,
            ))

        return alerts

    def _check_cost(self, today: dict) -> list[Alert]:
        """AI 비용을 검사한다."""
        alerts: list[Alert] = []
        cost = today.get("ai_cost", 0)

        if cost >= DAILY_COST_CRITICAL_USD:
            alerts.append(self._create_alert(
                level=AlertLevel.CRITICAL,
                title="AI Cost Alert",
                message=f"오늘 AI 비용 ${cost:.2f} - 일일 한도 초과",
                metric_name="daily_cost",
                current_value=cost,
                threshold=DAILY_COST_CRITICAL_USD,
            ))
        elif cost >= DAILY_COST_WARNING_USD:
            alerts.append(self._create_alert(
                level=AlertLevel.WARNING,
                title="AI Cost Warning",
                message=f"오늘 AI 비용 ${cost:.2f} - 예산 주의",
                metric_name="daily_cost",
                current_value=cost,
                threshold=DAILY_COST_WARNING_USD,
            ))

        return alerts

    def _check_health_score(self, data: dict) -> list[Alert]:
        """프로젝트 건강 점수를 검사한다."""
        alerts: list[Alert] = []
        score = data.get("health_score", 100)

        health_critical_threshold = 30
        health_warning_threshold = 60

        if score <= health_critical_threshold:
            alerts.append(self._create_alert(
                level=AlertLevel.CRITICAL,
                title="Critical Health Score",
                message=f"프로젝트 건강 점수 {score}점 - 긴급 개선 필요",
                metric_name="health_score",
                current_value=score,
                threshold=health_critical_threshold,
            ))
        elif score <= health_warning_threshold:
            alerts.append(self._create_alert(
                level=AlertLevel.WARNING,
                title="Low Health Score",
                message=f"프로젝트 건강 점수 {score}점 - 개선 권장",
                metric_name="health_score",
                current_value=score,
                threshold=health_warning_threshold,
            ))

        return alerts

    def _create_alert(self, **kwargs) -> Alert:
        self._alert_counter += 1
        return Alert(
            alert_id=f"ALT-{self._alert_counter:04d}",
            **kwargs,
        )

    def _trim_alerts(self) -> None:
        """경고 목록을 최대 크기로 유지한다."""
        if len(self._alerts) > MAX_ALERTS_RETAINED:
            self._alerts = self._alerts[-MAX_ALERTS_RETAINED:]
        self._save_to_disk()

    def _save_to_disk(self) -> None:
        """경고 목록을 JSON 파일에 저장한다."""
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "counter": self._alert_counter,
                "alerts": [a.to_dict() for a in self._alerts],
            }
            self._persist_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error(f"Alert 저장 실패: {exc}")

    def _load_from_disk(self) -> None:
        """서버 재시작 시 JSON 파일에서 경고를 복원한다."""
        if not self._persist_path.exists():
            return
        try:
            raw = json.loads(self._persist_path.read_text(encoding="utf-8"))
            self._alert_counter = raw.get("counter", 0)
            for item in raw.get("alerts", []):
                alert = Alert(
                    alert_id=item["alert_id"],
                    level=AlertLevel(item["level"]),
                    title=item["title"],
                    message=item["message"],
                    metric_name=item["metric_name"],
                    current_value=item["current_value"],
                    threshold=item["threshold"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                    acknowledged=item.get("acknowledged", False),
                )
                self._alerts.append(alert)
            logger.info(f"Alert {len(self._alerts)}건 복원 완료")
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning(f"Alert 복원 실패, 초기화: {exc}")
            self._alerts = []
            self._alert_counter = 0
