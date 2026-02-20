"""VIBE-X Dashboard Server.

사용법:
    python server.py          - 기본 포트 8000
    python server.py --port 3000  - 포트 지정
"""

import io
import sys
from pathlib import Path

# Windows 콘솔 UTF-8 강제
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import click
import uvicorn


@click.command()
@click.option("--port", default=8000, help="서버 포트")
@click.option("--host", default="127.0.0.1", help="서버 호스트")
@click.option("--reload", is_flag=True, help="자동 리로드 (개발용)")
def main(port: int, host: str, reload: bool) -> None:
    """VIBE-X Team Intelligence Dashboard를 시작한다."""
    print(f"\n  VIBE-X Dashboard")
    print(f"  http://{host}:{port}")
    print(f"  Press Ctrl+C to stop\n")

    uvicorn.run(
        "src.layer5_dashboard.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
