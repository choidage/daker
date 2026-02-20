"""품질 게이트 테스트 (Gate 1~5)."""

from pathlib import Path
from src.shared.types import GateStatus
from src.layer2_rag.gate_basic import BasicGate
from src.layer3_agents.review_agent import ReviewAgent
from src.layer3_agents.arch_agent import ArchitectureAgent


class TestGate1Syntax:
    """Gate 1: Syntax Agent 테스트."""

    def test_clean_file_passes(self, config, sample_python_file):
        gate = BasicGate(config)
        result = gate.run_gate1(sample_python_file)
        assert result.status == GateStatus.PASSED
        assert result.gate_number == 1
        assert result.gate_name == "Syntax Agent"

    def test_empty_file_warns(self, config, tmp_project):
        empty = tmp_project / "empty.py"
        empty.write_text("", encoding="utf-8")

        gate = BasicGate(config)
        result = gate.run_gate1(empty)
        assert result.status == GateStatus.WARNING
        assert "빈 파일" in result.details[0]

    def test_long_line_warns(self, config, tmp_project):
        code = "x = " + "a" * 250 + "\n"
        f = tmp_project / "long_line.py"
        f.write_text(code, encoding="utf-8")

        gate = BasicGate(config)
        result = gate.run_gate1(f)
        assert result.status == GateStatus.WARNING
        assert any("200자 초과" in d for d in result.details)

    def test_mixed_indent_warns(self, config, tmp_project):
        code = "def foo():\n\tpass\n  x = 1\n  y = 2\n"
        f = tmp_project / "mixed.py"
        f.write_text(code, encoding="utf-8")

        gate = BasicGate(config)
        result = gate.run_gate1(f)
        assert result.status == GateStatus.WARNING
        assert any("혼용" in d for d in result.details)


class TestGate2Rules:
    """Gate 2: Rules Agent 테스트."""

    def test_clean_file_passes(self, config, sample_python_file):
        gate = BasicGate(config)
        result = gate.run_gate2(sample_python_file)
        assert result.status == GateStatus.PASSED
        assert result.gate_number == 2

    def test_forbidden_pattern_detected(self, config, tmp_project):
        code = 'x = 1  # TODO: hack this later\nconsole.log("test")\n'
        f = tmp_project / "bad.py"
        f.write_text(code, encoding="utf-8")

        gate = BasicGate(config)
        result = gate.run_gate2(f)
        assert result.status in (GateStatus.WARNING, GateStatus.FAILED)
        assert any("금지 패턴" in d for d in result.details)

    def test_run_all(self, config, sample_python_file):
        gate = BasicGate(config)
        results = gate.run_all(sample_python_file)
        assert len(results) == 2
        assert results[0].gate_number == 1
        assert results[1].gate_number == 2


class TestGate4Review:
    """Gate 4: Review Agent 테스트."""

    def test_clean_file_passes(self, config, sample_python_file):
        agent = ReviewAgent(config)
        result = agent.run(sample_python_file)
        assert result.status == GateStatus.PASSED
        assert result.gate_number == 4

    def test_security_issues_detected(self, config, sample_bad_python_file):
        agent = ReviewAgent(config)
        result = agent.run(sample_bad_python_file)
        assert result.status == GateStatus.FAILED
        assert any("SEC-" in d for d in result.details)

    def test_eval_detected(self, config, tmp_project):
        code = 'def run(x):\n    eval(x)\n'
        f = tmp_project / "eval_use.py"
        f.write_text(code, encoding="utf-8")

        agent = ReviewAgent(config)
        result = agent.run(f)
        assert any("SEC-002" in d for d in result.details)

    def test_hardcoded_secret_detected(self, config, tmp_project):
        code = 'password = "my_super_secret_key_12345"\n'
        f = tmp_project / "secret.py"
        f.write_text(code, encoding="utf-8")

        agent = ReviewAgent(config)
        result = agent.run(f)
        assert any("SEC-001" in d for d in result.details)

    def test_file_too_large_warns(self, config, tmp_project):
        code = "\n".join([f"x_{i} = {i}" for i in range(600)])
        f = tmp_project / "big_file.py"
        f.write_text(code, encoding="utf-8")

        agent = ReviewAgent(config)
        result = agent.run(f)
        assert any("CMPLX-001" in d for d in result.details)


class TestGate5Architecture:
    """Gate 5: Architecture Agent 테스트."""

    def test_valid_file_passes(self, config, sample_python_file):
        agent = ArchitectureAgent(config)
        result = agent.run(sample_python_file)
        assert result.gate_number == 5
        # 프로젝트 외부 파일이므로 통과
        assert result.status in (GateStatus.PASSED, GateStatus.WARNING)

    def test_snake_case_filename(self, config, tmp_project):
        f = tmp_project / "src" / "shared" / "my_module.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x = 1\n", encoding="utf-8")

        agent = ArchitectureAgent(config)
        result = agent.run(f)
        # snake_case이므로 이름 관련 이슈 없어야 함
        assert not any("ARCH-003" in d for d in result.details)

    def test_bad_filename_warns(self, config, tmp_project):
        f = tmp_project / "src" / "shared" / "MyBadModule.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x = 1\n", encoding="utf-8")

        agent = ArchitectureAgent(config)
        result = agent.run(f)
        assert any("ARCH-003" in d for d in result.details)

    def test_bad_class_name(self, config, tmp_project):
        code = "class bad_class_name:\n    pass\n"
        f = tmp_project / "src" / "shared" / "test_naming.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(code, encoding="utf-8")

        agent = ArchitectureAgent(config)
        result = agent.run(f)
        assert any("ARCH-004" in d for d in result.details)
