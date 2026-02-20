"""M5 - Project Context Manager.

프로젝트별 격리된 서비스 인스턴스(Metrics, Alerts, WorkZone, Feedback)를 관리한다.
프로젝트 전환 시 해당 프로젝트의 서비스 인스턴스를 lazy-init으로 제공한다.
"""

from dataclasses import dataclass, field

from src.shared.config import VibeXConfig
from src.shared.logger import get_logger
from src.layer5_dashboard.metrics import MetricsCollector
from src.layer5_dashboard.alert_system import AlertSystem
from src.layer5_dashboard.onboarding import OnboardingBriefing
from src.layer5_dashboard.feedback_loop import FeedbackLoop
from src.layer4_collab.work_zone import WorkZoneManager
from src.layer4_collab.decision_extractor import DecisionExtractor

logger = get_logger("project_ctx")


@dataclass
class ProjectServices:
    """프로젝트별 서비스 인스턴스 번들."""

    project_id: str
    config: VibeXConfig
    metrics: MetricsCollector = field(init=False)
    alerts: AlertSystem = field(init=False)
    onboarding: OnboardingBriefing = field(init=False)
    feedback: FeedbackLoop = field(init=False)
    work_zone: WorkZoneManager = field(init=False)
    decision_extractor: DecisionExtractor = field(init=False)

    def __post_init__(self) -> None:
        self.metrics = MetricsCollector(self.config)
        self.alerts = AlertSystem(self.config)
        self.onboarding = OnboardingBriefing(self.config)
        self.feedback = FeedbackLoop(self.config, metrics_collector=self.metrics)
        self.work_zone = WorkZoneManager(config=self.config)
        self.decision_extractor = DecisionExtractor(self.config)
        logger.info(f"[{self.project_id}] 서비스 인스턴스 초기화 완료")


class ProjectContextManager:
    """프로젝트별 서비스 인스턴스를 lazy-init으로 관리한다."""

    def __init__(self) -> None:
        self._services: dict[str, ProjectServices] = {}

    def get_services(self, project_id: str, config: VibeXConfig) -> ProjectServices:
        """프로젝트의 서비스 인스턴스를 반환한다. 없으면 생성한다."""
        if project_id not in self._services:
            self._services[project_id] = ProjectServices(
                project_id=project_id,
                config=config,
            )
        return self._services[project_id]

    def remove(self, project_id: str) -> None:
        """프로젝트 서비스 인스턴스를 제거한다."""
        self._services.pop(project_id, None)

    def list_loaded(self) -> list[str]:
        """현재 로드된 프로젝트 ID 목록."""
        return list(self._services.keys())

    def get_cross_project_summary(self) -> list[dict]:
        """모든 로드된 프로젝트의 메트릭 요약을 반환한다."""
        summaries: list[dict] = []
        for pid, svc in self._services.items():
            dashboard = svc.metrics.get_dashboard_data()
            active_alerts = svc.alerts.get_active_alerts()
            active_zones = svc.work_zone.get_active_zones()
            summaries.append({
                "project_id": pid,
                "health_score": dashboard.get("health_score", 0),
                "today_gate_runs": dashboard.get("today", {}).get("gate_runs", 0),
                "today_pass_rate": dashboard.get("today", {}).get("pass_rate", 0),
                "today_cost": dashboard.get("today", {}).get("ai_cost", 0),
                "active_alerts": len(active_alerts),
                "active_zones": len(active_zones),
            })
        return summaries
