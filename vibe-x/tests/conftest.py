"""VIBE-X 테스트 공통 Fixture.

모든 테스트에서 공유하는 설정, 임시 파일, 서비스 인스턴스를 관리한다.
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# pytest capture 충돌 방지: logger.py의 stdout 래핑을 비활성화
os.environ["VIBE_X_NO_WRAP_STDOUT"] = "1"

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.shared.config import VibeXConfig, PathConfig, RagConfig, GateConfig


@pytest.fixture
def isolated_project_registry(tmp_path):
    """멀티 프로젝트 테스트를 위한 격리된 레지스트리.

    app 모듈의 _project_registry를 임시 디렉토리 기반의
    새 인스턴스로 교체하여 프로덕션 데이터 오염을 방지한다.
    """
    from src.layer5_dashboard import app as app_module
    from src.layer5_dashboard.project_registry import ProjectRegistry, REGISTRY_FILE
    from src.layer5_dashboard.project_context import ProjectContextManager

    original_registry = app_module._project_registry
    original_ctx = app_module._project_ctx

    temp_meta = tmp_path / ".meta"
    temp_meta.mkdir(parents=True, exist_ok=True)

    test_registry = ProjectRegistry.__new__(ProjectRegistry)
    test_registry._global_config = original_registry._global_config
    test_registry._projects = {}
    test_registry._configs = {}
    test_registry._persist_path = temp_meta / REGISTRY_FILE

    app_module._project_registry = test_registry
    app_module._project_ctx = ProjectContextManager()

    yield test_registry

    app_module._project_registry = original_registry
    app_module._project_ctx = original_ctx


@pytest.fixture
def tmp_project(tmp_path):
    """임시 프로젝트 디렉토리를 생성한다."""
    vibe_x = tmp_path / "vibe-x"
    vibe_x.mkdir()
    (vibe_x / "docs" / "adr").mkdir(parents=True)
    (vibe_x / "src" / "shared").mkdir(parents=True)
    (vibe_x / "src" / "layer2_rag").mkdir(parents=True)
    (vibe_x / "src" / "layer3_agents").mkdir(parents=True)
    (vibe_x / "src" / "layer4_collab").mkdir(parents=True)
    (vibe_x / "src" / "layer5_dashboard").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def config(tmp_project):
    """테스트용 설정 객체."""
    return VibeXConfig(
        paths=PathConfig(project_root=tmp_project),
        rag=RagConfig(
            chunk_max_lines=30,
            chunk_overlap_lines=3,
            search_top_k=5,
        ),
        gate=GateConfig(
            max_function_lines=30,
            forbidden_patterns=("console.log", "TODO: hack"),
        ),
    )


@pytest.fixture
def sample_python_file(tmp_project):
    """테스트용 Python 파일을 생성한다."""
    code = '''"""Sample module for testing."""

import os
from pathlib import Path


class Calculator:
    """Simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b

    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b


def helper_function(x: int) -> str:
    """Helper function."""
    return str(x * 2)


def another_function(name: str) -> str:
    """Another helper."""
    return f"Hello, {name}"
'''
    file_path = tmp_project / "sample.py"
    file_path.write_text(code, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_bad_python_file(tmp_project):
    """보안/규칙 위반이 있는 Python 파일."""
    code = '''"""Bad code example."""

import os
import subprocess

password = "super_secret_123"

def dangerous_function(user_input):
    eval(user_input)
    subprocess.call(user_input, shell=True)

def very_long_function():
    x = 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    return x
'''
    file_path = tmp_project / "bad_sample.py"
    file_path.write_text(code, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_markdown_file(tmp_project):
    """테스트용 Markdown 파일."""
    content = """# Test Document

## Section 1
This is a test document for VIBE-X.

## Section 2
Another section with content.
"""
    file_path = tmp_project / "test.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path
