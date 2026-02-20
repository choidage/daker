"""Task 3.6 - 6-Gate Chain Orchestrator.

Gate 1~6 을 순차 실행하는 파이프라인.
각 Gate 실패 시 중단/경고/바이패스 정책을 적용한다.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from src.shared.config import VibeXConfig, load_config
from src.shared.logger import get_logger
from src.shared.types import GateResult, GateStatus

logger = get_logger("pipeline")


class FailPolicy(Enum):
    """Gate 실패 시 정책."""
    STOP = "stop"          # 즉시 중단
    WARN = "warn"          # 경고 후 계속
    BYPASS = "bypass"      # 무시 (핫픽스 등)


@dataclass
class PipelineResult:
    """전체 파이프라인 실행 결과."""
    gate_results: list[GateResult] = field(default_factory=list)
    total_time_seconds: float = 0.0
    stopped_at: int | None = None
    overall_status: GateStatus = GateStatus.PASSED

    @property
    def summary(self) -> str:
        passed = sum(1 for g in self.gate_results if g.status == GateStatus.PASSED)
        failed = sum(1 for g in self.gate_results if g.status == GateStatus.FAILED)
        warned = sum(1 for g in self.gate_results if g.status == GateStatus.WARNING)
        skipped = sum(1 for g in self.gate_results if g.status == GateStatus.SKIPPED)
        return (
            f"통과:{passed} 실패:{failed} 경고:{warned} "
            f"스킵:{skipped} / 소요:{self.total_time_seconds:.1f}s"
        )


class GateChainRunner:
    """6-Gate 체인 오케스트레이터.

    Gate 1 (Syntax Agent) -> 2 (Rules Agent) -> 3 (Integration Agent)
    -> 4 (Review Agent) -> 5 (Architecture Agent) -> 6 (Collision Agent)

    각 Gate에 대해 실패 정책(중단/경고/바이패스)을 설정할 수 있다.
    """

    # 기본 실패 정책
    DEFAULT_POLICIES: dict[int, FailPolicy] = {
        1: FailPolicy.STOP,    # 구문 오류 -> 즉시 중단
        2: FailPolicy.STOP,    # 규칙 위반 -> 즉시 중단
        3: FailPolicy.WARN,    # 테스트 실패 -> 경고 후 계속
        4: FailPolicy.WARN,    # 리뷰 이슈 -> 경고 후 계속
        5: FailPolicy.WARN,    # 아키텍처 이슈 -> 경고 후 계속
        6: FailPolicy.WARN,    # 충돌 감지 -> 경고 후 계속
    }

    def __init__(self, config: VibeXConfig | None = None) -> None:
        self._config = config or load_config()
        self._policies = dict(self.DEFAULT_POLICIES)

    def set_policy(self, gate_number: int, policy: FailPolicy) -> None:
        """특정 Gate의 실패 정책을 변경한다."""
        self._policies[gate_number] = policy

    def run_all(
        self,
        file_path: Path,
        changed_files: list[Path] | None = None,
        author: str = "current",
    ) -> PipelineResult:
        """전체 6-Gate 파이프라인을 실행한다.

        Args:
            file_path: 주요 검증 대상 파일
            changed_files: 변경된 전체 파일 목록 (Gate 3, 6용)
            author: 작업자 식별자 (Gate 6용)

        Returns:
            파이프라인 전체 실행 결과
        """
        start = time.time()
        result = PipelineResult()

        if changed_files is None:
            changed_files = [file_path]

        logger.info(f"6-Gate 파이프라인 시작: {file_path}")

        # Gate 1-2: Basic Gate (Phase 2에서 구현)
        gate12_results = self._run_gate_1_2(file_path)
        for gr in gate12_results:
            result.gate_results.append(gr)
            if not self._should_continue(gr, result):
                result.total_time_seconds = time.time() - start
                return result

        # Gate 3: Integration Agent
        gate3_result = self._run_gate_3(changed_files)
        result.gate_results.append(gate3_result)
        if not self._should_continue(gate3_result, result):
            result.total_time_seconds = time.time() - start
            return result

        # Gate 4: Review Agent
        gate4_result = self._run_gate_4(file_path)
        result.gate_results.append(gate4_result)
        if not self._should_continue(gate4_result, result):
            result.total_time_seconds = time.time() - start
            return result

        # Gate 5: Architecture Agent
        gate5_result = self._run_gate_5(file_path)
        result.gate_results.append(gate5_result)
        if not self._should_continue(gate5_result, result):
            result.total_time_seconds = time.time() - start
            return result

        # Gate 6: Collision Agent
        gate6_result = self._run_gate_6(changed_files, author)
        result.gate_results.append(gate6_result)

        # 최종 상태 결정
        self._finalize(result)
        result.total_time_seconds = time.time() - start

        logger.info(f"파이프라인 완료 [{result.overall_status.value}]: {result.summary}")
        return result

    def _run_gate_1_2(self, file_path: Path) -> list[GateResult]:
        """Gate 1-2: 기본 품질 검사."""
        from src.layer2_rag.gate_basic import BasicGate

        gate = BasicGate(self._config)
        return gate.run_all(file_path)

    def _run_gate_3(self, changed_files: list[Path]) -> GateResult:
        """Gate 3: 통합 테스트."""
        from src.layer3_agents.integration_agent import IntegrationAgent

        agent = IntegrationAgent(self._config)
        return agent.run(changed_files)

    def _run_gate_4(self, file_path: Path) -> GateResult:
        """Gate 4: 코드 리뷰."""
        from src.layer3_agents.review_agent import ReviewAgent

        agent = ReviewAgent(self._config)
        return agent.run(file_path)

    def _run_gate_5(self, file_path: Path) -> GateResult:
        """Gate 5: 아키텍처 검증."""
        from src.layer3_agents.arch_agent import ArchitectureAgent

        agent = ArchitectureAgent(self._config)
        return agent.run(file_path)

    def _run_gate_6(self, changed_files: list[Path], author: str) -> GateResult:
        """Gate 6: 충돌 감지."""
        from src.layer3_agents.collision_agent import CollisionAgent

        agent = CollisionAgent(self._config)
        return agent.run(changed_files, author)

    def _should_continue(self, gate_result: GateResult, pipeline: PipelineResult) -> bool:
        """Gate 실패 시 계속 진행할지 판단한다."""
        if gate_result.status in (GateStatus.PASSED, GateStatus.SKIPPED):
            return True

        policy = self._policies.get(gate_result.gate_number, FailPolicy.WARN)

        if gate_result.status == GateStatus.WARNING:
            return True  # 경고는 항상 계속

        if gate_result.status == GateStatus.FAILED:
            if policy == FailPolicy.STOP:
                pipeline.stopped_at = gate_result.gate_number
                pipeline.overall_status = GateStatus.FAILED
                logger.warning(
                    f"파이프라인 중단: Gate {gate_result.gate_number} 실패 (정책: STOP)"
                )
                return False
            elif policy == FailPolicy.BYPASS:
                logger.info(
                    f"Gate {gate_result.gate_number} 실패 - 바이패스 (정책: BYPASS)"
                )
                return True
            else:
                return True

        return True

    def _finalize(self, result: PipelineResult) -> None:
        """파이프라인 최종 상태를 결정한다."""
        if result.overall_status == GateStatus.FAILED:
            return

        has_warning = any(
            g.status == GateStatus.WARNING for g in result.gate_results
        )
        has_failed = any(
            g.status == GateStatus.FAILED for g in result.gate_results
        )

        if has_failed:
            result.overall_status = GateStatus.FAILED
        elif has_warning:
            result.overall_status = GateStatus.WARNING
        else:
            result.overall_status = GateStatus.PASSED
