"""Task 3.1 - MCP Server: Event Bus + Agent Registry.

VIBE-X 전체를 관통하는 표준 통신 계층.
Agent 등록/해제, 메시지 라우팅, 상태 관리를 담당한다.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable

from src.shared.logger import get_logger

logger = get_logger("mcp")


class MessageType(Enum):
    """MCP 메시지 유형."""
    GATE_RESULT = "gate_result"
    ZONE_DECLARE = "zone_declare"
    ZONE_RELEASE = "zone_release"
    COLLISION_ALERT = "collision_alert"
    DECISION_FOUND = "decision_found"
    CONTEXT_SYNC = "context_sync"
    HEALTH_CHECK = "health_check"


@dataclass
class McpMessage:
    """MCP 통신 메시지."""
    msg_type: MessageType
    sender: str
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def age_ms(self) -> float:
        return (datetime.now() - self.timestamp).total_seconds() * 1000


@dataclass
class AgentInfo:
    """등록된 Agent 정보."""
    name: str
    agent_type: str
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    is_active: bool = True


# 메시지 핸들러 타입
MessageHandler = Callable[[McpMessage], None]


class McpServer:
    """MCP 서버 - Agent 간 통신 허브.

    기능:
    - Agent 등록/해제/헬스체크
    - 메시지 라우팅 (pub/sub 패턴)
    - 팀 컨텍스트 상태 관리
    - 메시지 이력 보존
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentInfo] = {}
        self._subscribers: dict[MessageType, list[MessageHandler]] = {}
        self._message_log: list[McpMessage] = []
        self._context: dict[str, object] = {}
        self._max_log_size: int = 1000

    def register_agent(self, name: str, agent_type: str) -> bool:
        """Agent를 등록한다."""
        if name in self._agents:
            logger.warning(f"Agent '{name}' 이미 등록됨")
            return False

        self._agents[name] = AgentInfo(name=name, agent_type=agent_type)
        logger.info(f"Agent 등록: {name} ({agent_type})")
        return True

    def unregister_agent(self, name: str) -> bool:
        """Agent를 해제한다."""
        if name not in self._agents:
            return False

        self._agents[name].is_active = False
        logger.info(f"Agent 해제: {name}")
        return True

    def subscribe(self, msg_type: MessageType, handler: MessageHandler) -> None:
        """특정 메시지 유형에 대한 구독을 등록한다."""
        if msg_type not in self._subscribers:
            self._subscribers[msg_type] = []
        self._subscribers[msg_type].append(handler)

    def publish(self, message: McpMessage) -> int:
        """메시지를 발행하고 구독자에게 전달한다.

        Returns:
            메시지를 수신한 구독자 수
        """
        self._log_message(message)
        handlers = self._subscribers.get(message.msg_type, [])
        delivered = 0

        for handler in handlers:
            try:
                handler(message)
                delivered += 1
            except Exception as e:
                logger.warning(f"핸들러 실행 실패: {e}")

        return delivered

    def set_context(self, key: str, value: object) -> None:
        """팀 공유 컨텍스트를 설정한다."""
        self._context[key] = value

    def get_context(self, key: str) -> object | None:
        """팀 공유 컨텍스트를 조회한다."""
        return self._context.get(key)

    def heartbeat(self, agent_name: str) -> bool:
        """Agent 헬스체크 (하트비트)."""
        agent = self._agents.get(agent_name)
        if agent and agent.is_active:
            agent.last_heartbeat = datetime.now()
            return True
        return False

    def get_active_agents(self) -> list[AgentInfo]:
        """활성 Agent 목록을 반환한다."""
        return [a for a in self._agents.values() if a.is_active]

    def get_message_log(self, limit: int = 50) -> list[McpMessage]:
        """최근 메시지 이력을 반환한다."""
        return self._message_log[-limit:]

    def get_stats(self) -> dict:
        """MCP 서버 통계."""
        active = sum(1 for a in self._agents.values() if a.is_active)
        return {
            "total_agents": len(self._agents),
            "active_agents": active,
            "total_subscriptions": sum(len(h) for h in self._subscribers.values()),
            "message_log_size": len(self._message_log),
            "context_keys": list(self._context.keys()),
        }

    def _log_message(self, message: McpMessage) -> None:
        """메시지를 이력에 기록한다."""
        self._message_log.append(message)
        if len(self._message_log) > self._max_log_size:
            self._message_log = self._message_log[-self._max_log_size:]
