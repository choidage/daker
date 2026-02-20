"""VIBE-X 로깅 모듈.

모든 Layer에서 공통으로 사용하는 로거.
console.log 대신 이 로거를 사용한다 (coding-rules.md 준수).
"""

import io
import os
import sys
import logging
from rich.logging import RichHandler
from rich.console import Console

# Windows cp949 인코딩 문제 방지: UTF-8 강제 설정
# 테스트 환경(pytest)에서는 stdout 래핑을 건너뜀 (capture 충돌 방지)
if sys.platform == "win32" and not os.environ.get("VIBE_X_NO_WRAP_STDOUT"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

_console = Console(force_terminal=True, force_jupyter=False)

_LOG_FORMAT = "%(message)s"
_DATE_FORMAT = "%H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """이름 기반 로거를 생성한다. 중복 핸들러를 방지한다."""
    logger = logging.getLogger(f"vibe-x.{name}")

    if not logger.handlers:
        handler = RichHandler(
            console=_console,
            show_path=False,
            rich_tracebacks=True,
            markup=True,
        )
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger
