"""VIBE-X admin 비밀번호를 기본값(admin)으로 초기화합니다.

사용법:
    python scripts/reset_admin_password.py
    (vibe-x 폴더에서 실행하거나, daker 폴더에서 python vibe-x/scripts/reset_admin_password.py)
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# vibe-x 루트 = 이 스크립트의 부모의 부모
VIBE_X_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = VIBE_X_ROOT / ".state"
USERS_JSON = STATE_DIR / "users.json"

# 기본 admin 비밀번호 "admin" 의 해시 (auth.py 와 동일: salt + password)
DEFAULT_ADMIN_HASH = "38f88978f1c2a4d7320cad2c9003c7c4a408763a48201fb8c04eb4c64dea245b"


def main() -> None:
    if not USERS_JSON.exists():
        print("users.json 이 없습니다. 대시보드에 한 번도 로그인하지 않았을 수 있습니다.")
        print("기본 계정 admin / admin 으로 로그인하면 자동 생성됩니다.")
        sys.exit(0)

    data = json.loads(USERS_JSON.read_text(encoding="utf-8"))
    if "admin" not in data:
        data["admin"] = {
            "password_hash": DEFAULT_ADMIN_HASH,
            "role": "admin",
            "display_name": "Administrator",
            "email": "",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
        }
    else:
        data["admin"]["password_hash"] = DEFAULT_ADMIN_HASH

    USERS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("admin 비밀번호가 'admin' 으로 초기화되었습니다.")
    print("대시보드에서 아이디: admin, 비밀번호: admin 으로 로그인하세요.")


if __name__ == "__main__":
    main()
