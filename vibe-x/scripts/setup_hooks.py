"""VIBE-X Git Hook 설정 스크립트.

git init (필요 시) + .githooks 디렉토리를 git hooks 경로로 등록한다.
실행: python scripts/setup_hooks.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PROJECT_ROOT / ".githooks"


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    return result.stdout.strip()


def main() -> int:
    git_dir = PROJECT_ROOT / ".git"

    if not git_dir.exists():
        print("[INIT] Git repository initializing...")
        run(["git", "init"])
        print("  .git created")

    print(f"[HOOK] Setting git hooks path: {HOOKS_DIR}")
    run(["git", "config", "core.hooksPath", str(HOOKS_DIR)])

    hook_file = HOOKS_DIR / "pre-commit"
    if not hook_file.exists():
        print("[ERROR] pre-commit hook file not found.")
        return 1

    if sys.platform != "win32":
        subprocess.run(["chmod", "+x", str(hook_file)])

    print("[OK] Git Hook setup complete!")
    print()
    print("Usage:")
    print("  git add <files>")
    print("  git commit -m 'message'")
    print("  -> Gate 1+2 auto-runs, blocks commit on FAIL")
    print()
    print("Bypass:")
    print("  git commit --no-verify -m 'hotfix'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
