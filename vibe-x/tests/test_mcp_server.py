"""MCP 서버 테스트."""

from src.layer4_collab.mcp_server import McpServer, McpMessage, MessageType


class TestMcpServer:
    """McpServer 통합 테스트."""

    def test_register_agent(self):
        server = McpServer()
        assert server.register_agent("gate1", "syntax") is True
        agents = server.get_active_agents()
        assert len(agents) == 1
        assert agents[0].name == "gate1"

    def test_register_duplicate_fails(self):
        server = McpServer()
        server.register_agent("gate1", "syntax")
        assert server.register_agent("gate1", "syntax") is False

    def test_unregister_agent(self):
        server = McpServer()
        server.register_agent("gate1", "syntax")
        assert server.unregister_agent("gate1") is True
        agents = server.get_active_agents()
        assert len(agents) == 0

    def test_unregister_nonexistent(self):
        server = McpServer()
        assert server.unregister_agent("nonexistent") is False

    def test_publish_subscribe(self):
        server = McpServer()
        received = []

        def handler(msg):
            received.append(msg)

        server.subscribe(MessageType.GATE_RESULT, handler)

        msg = McpMessage(
            msg_type=MessageType.GATE_RESULT,
            sender="gate1",
            payload={"status": "passed"},
        )
        delivered = server.publish(msg)

        assert delivered == 1
        assert len(received) == 1
        assert received[0].sender == "gate1"

    def test_publish_no_subscribers(self):
        server = McpServer()
        msg = McpMessage(
            msg_type=MessageType.GATE_RESULT,
            sender="gate1",
        )
        delivered = server.publish(msg)
        assert delivered == 0

    def test_multiple_subscribers(self):
        server = McpServer()
        counts = {"a": 0, "b": 0}

        server.subscribe(MessageType.ZONE_DECLARE, lambda m: counts.update(a=counts["a"] + 1))
        server.subscribe(MessageType.ZONE_DECLARE, lambda m: counts.update(b=counts["b"] + 1))

        msg = McpMessage(msg_type=MessageType.ZONE_DECLARE, sender="user1")
        delivered = server.publish(msg)

        assert delivered == 2
        assert counts["a"] == 1
        assert counts["b"] == 1

    def test_context_set_get(self):
        server = McpServer()
        server.set_context("current_branch", "main")
        assert server.get_context("current_branch") == "main"
        assert server.get_context("nonexistent") is None

    def test_heartbeat(self):
        server = McpServer()
        server.register_agent("gate1", "syntax")
        assert server.heartbeat("gate1") is True
        assert server.heartbeat("nonexistent") is False

    def test_heartbeat_inactive_agent(self):
        server = McpServer()
        server.register_agent("gate1", "syntax")
        server.unregister_agent("gate1")
        assert server.heartbeat("gate1") is False

    def test_message_log(self):
        server = McpServer()
        for i in range(5):
            msg = McpMessage(
                msg_type=MessageType.HEALTH_CHECK,
                sender=f"agent{i}",
            )
            server.publish(msg)

        log = server.get_message_log(limit=3)
        assert len(log) == 3

    def test_stats(self):
        server = McpServer()
        server.register_agent("g1", "syntax")
        server.register_agent("g2", "rules")
        server.subscribe(MessageType.GATE_RESULT, lambda m: None)
        server.set_context("key1", "val1")

        stats = server.get_stats()
        assert stats["total_agents"] == 2
        assert stats["active_agents"] == 2
        assert stats["total_subscriptions"] == 1
        assert "key1" in stats["context_keys"]

    def test_message_age(self):
        msg = McpMessage(
            msg_type=MessageType.HEALTH_CHECK,
            sender="test",
        )
        assert msg.age_ms >= 0

    def test_handler_exception_doesnt_break(self):
        """핸들러 예외가 다른 핸들러를 차단하지 않는다."""
        server = McpServer()
        results = []

        def bad_handler(msg):
            raise ValueError("bad")

        def good_handler(msg):
            results.append(msg.sender)

        server.subscribe(MessageType.GATE_RESULT, bad_handler)
        server.subscribe(MessageType.GATE_RESULT, good_handler)

        msg = McpMessage(msg_type=MessageType.GATE_RESULT, sender="test")
        delivered = server.publish(msg)

        assert delivered == 1  # good_handler만 성공
        assert "test" in results
