"""VIBE-X MCP 배포 패키지 빌드 스크립트.

pip과 npm 패키지 디렉토리에 소스 코드를 복사하고 빌드 준비를 완료한다.

Usage:
    python build.py          # pip + npm 모두 빌드
    python build.py pip      # pip만 빌드
    python build.py npm      # npm만 빌드
"""

import shutil
import sys
from pathlib import Path

BUILD_DIR = Path(__file__).parent
WORKSPACE = BUILD_DIR.parent.parent  # daker/
VIBE_X = WORKSPACE / "vibe-x"

SRC_DIRS = [
    "src/shared",
    "src/layer2_rag",
    "src/layer3_agents",
    "src/layer4_collab",
    "src/layer5_dashboard",
]

EXCLUDE_FILES = {"app.py", "static"}


def copy_source(dest_root: Path) -> int:
    """Copy VIBE-X source code into the destination package directory."""
    copied = 0
    for src_dir in SRC_DIRS:
        src = VIBE_X / src_dir
        dst = dest_root / src_dir

        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True, exist_ok=True)

        for item in sorted(src.rglob("*.py")):
            rel = item.relative_to(src)
            if any(part in EXCLUDE_FILES for part in rel.parts):
                continue
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            copied += 1

    src_init = dest_root / "src" / "__init__.py"
    if not src_init.exists():
        src_init.write_text("")
        copied += 1

    return copied


def build_pip() -> None:
    """Build pip package."""
    pip_pkg = BUILD_DIR / "pip" / "vibe-x-mcp" / "vibe_x_mcp"
    print(f"[pip] Copying source to {pip_pkg}")
    count = copy_source(pip_pkg)
    print(f"[pip] {count} files copied")
    print("[pip] Ready. Build with: cd pip/vibe-x-mcp && pip install build && python -m build")


def build_npm() -> None:
    """Build npm package."""
    npm_pkg = BUILD_DIR / "npm" / "vibe-x-mcp" / "python"
    print(f"[npm] Copying source to {npm_pkg}")
    count = copy_source(npm_pkg)

    server_src = BUILD_DIR / "pip" / "vibe-x-mcp" / "vibe_x_mcp" / "server.py"
    entry_src = BUILD_DIR / "pip" / "vibe-x-mcp" / "vibe_x_mcp" / "__main__.py"
    init_src = BUILD_DIR / "pip" / "vibe-x-mcp" / "vibe_x_mcp" / "__init__.py"

    for f in [server_src, entry_src, init_src]:
        if f.exists():
            shutil.copy2(f, npm_pkg / f.name)
            count += 1

    print(f"[npm] {count} files copied")
    print("[npm] Ready. Publish with: cd npm/vibe-x-mcp && npm publish")


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target in ("all", "pip"):
        build_pip()
    if target in ("all", "npm"):
        build_npm()

    print("\nBuild complete!")


if __name__ == "__main__":
    main()
