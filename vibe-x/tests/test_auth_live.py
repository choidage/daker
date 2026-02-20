"""인증 API 라이브 테스트 스크립트.

서버가 localhost:8001에서 실행 중일 때 실행한다.
python tests/test_auth_live.py
"""

import httpx
import json
import sys

BASE = "http://localhost:8001"

def main():
    print("=" * 60)
    print("  VIBE-X 인증 시스템 동작 테스트")
    print("=" * 60)

    # 1. 로그인
    print("\n[1] Admin 로그인")
    r = httpx.post(f"{BASE}/api/auth/login", json={
        "username": "admin", "password": "admin"
    })
    data = r.json()
    print(f"    결과: {data['success']}")
    print(f"    역할: {data['user']['role']}")
    token = data["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 개발자 등록
    print("\n[2] 사용자 등록: 김개발 (developer)")
    r = httpx.post(f"{BASE}/api/auth/register", json={
        "username": "dev_kim",
        "password": "pass1234",
        "role": "developer",
        "display_name": "Kim Developer",
        "email": "kim@team.com",
    }, headers=headers)
    print(f"    결과: {r.json()}")

    # 3. 뷰어 등록
    print("\n[3] 사용자 등록: 이뷰어 (viewer)")
    r = httpx.post(f"{BASE}/api/auth/register", json={
        "username": "viewer_lee",
        "password": "view1234",
        "role": "viewer",
        "display_name": "Lee Viewer",
    }, headers=headers)
    print(f"    결과: {r.json()}")

    # 4. 사용자 목록
    print("\n[4] 전체 사용자 목록")
    r = httpx.get(f"{BASE}/api/auth/users", headers=headers)
    users = r.json().get("users", [])
    for u in users:
        active = "Active" if u["is_active"] else "Inactive"
        print(f"    - {u['display_name']} ({u['username']}) | {u['role']} | {active}")

    # 5. 개발자로 로그인
    print("\n[5] 개발자(dev_kim) 로그인")
    r = httpx.post(f"{BASE}/api/auth/login", json={
        "username": "dev_kim", "password": "pass1234"
    })
    dev_data = r.json()
    print(f"    성공: {dev_data['success']}, 역할: {dev_data['user']['role']}")
    dev_headers = {"Authorization": f"Bearer {dev_data['token']}"}

    # 6. 개발자가 Admin 등록 시도 (권한 차단)
    print("\n[6] 개발자가 Admin 등록 시도 (차단되어야 함)")
    r = httpx.post(f"{BASE}/api/auth/register", json={
        "username": "hacker", "password": "hack1234", "role": "admin"
    }, headers=dev_headers)
    result = r.json()
    blocked = not result.get("success", True)
    print(f"    차단됨: {blocked}")
    print(f"    메시지: {result.get('error', 'N/A')}")

    # 7. 내 정보 조회
    print("\n[7] 내 정보 조회 (dev_kim)")
    r = httpx.get(f"{BASE}/api/auth/me", headers=dev_headers)
    me = r.json()
    print(f"    사용자: {me['user']['display_name']}")
    print(f"    역할: {me['user']['role']}")

    # 8. 잘못된 비밀번호 로그인
    print("\n[8] 잘못된 비밀번호 로그인 (실패해야 함)")
    r = httpx.post(f"{BASE}/api/auth/login", json={
        "username": "admin", "password": "wrongpass"
    })
    print(f"    실패: {not r.json()['success']}")

    # 9. 대시보드 API 확인
    print("\n[9] 대시보드 API")
    r = httpx.get(f"{BASE}/api/dashboard")
    print(f"    상태코드: {r.status_code}")

    # 10. 피드백 API 확인
    print("\n[10] 피드백 API")
    r = httpx.get(f"{BASE}/api/feedback")
    print(f"    상태코드: {r.status_code}")

    print("\n" + "=" * 60)
    print("  모든 동작 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("ERROR: 서버가 실행되고 있지 않습니다.")
        print("먼저 실행: python server.py --port 8001")
        sys.exit(1)
