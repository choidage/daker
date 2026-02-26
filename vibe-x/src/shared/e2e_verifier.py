"""E2E Verification — URL 접근성 및 브라우저 기반 검증.

- verify_url: httpx 기반 기본 URL 응답 검사 (의존성 없음)
- verify_selector: Playwright 기반 셀렉터 검증 (playwright 설치 시)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class E2EResult:
    """E2E 검증 결과."""

    ok: bool
    url: str
    status_code: int | None
    title: str | None
    message: str
    screenshot_path: str | None = None
    selector_matched: bool | None = None


def verify_url(url: str, timeout_ms: int = 10000) -> E2EResult:
    """URL이 정상 응답하는지 검증합니다. httpx 사용 (추가 의존성 없음)."""
    import httpx

    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    try:
        with httpx.Client(timeout=timeout_ms / 1000.0, follow_redirects=True) as client:
            resp = client.get(url)
            title = _extract_title(resp.text) if resp.text else None
            return E2EResult(
                ok=resp.status_code < 400,
                url=str(resp.url),
                status_code=resp.status_code,
                title=title,
                message=f"HTTP {resp.status_code}" + (f" — {title}" if title else ""),
            )
    except httpx.TimeoutException as e:
        return E2EResult(
            ok=False,
            url=url,
            status_code=None,
            title=None,
            message=f"타임아웃 ({timeout_ms}ms): {e!s}",
        )
    except Exception as e:
        return E2EResult(
            ok=False,
            url=url,
            status_code=None,
            title=None,
            message=f"오류: {e!s}",
        )


def verify_selector(
    url: str,
    selector: str,
    expected_text: str = "",
    timeout_ms: int = 15000,
    screenshot_path: str | None = None,
) -> E2EResult:
    """Playwright로 URL 접속 후 셀렉터 요소 존재/텍스트 검증.
    Playwright 미설치 시 verify_url로 폴백."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fallback = verify_url(url, timeout_ms)
        fallback.message += (
            " | Playwright 미설치. 셀렉터 검증을 위해: pip install playwright && playwright install chromium"
        )
        return fallback

    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=timeout_ms)
            title = page.title()

            elem = page.locator(selector).first
            elem.wait_for(state="visible", timeout=5000)

            actual_text = elem.inner_text() if expected_text else ""
            matched = (expected_text in actual_text) if expected_text else True

            saved_path = None
            if screenshot_path:
                page.screenshot(path=screenshot_path)
                saved_path = screenshot_path

            browser.close()

            return E2EResult(
                ok=matched,
                url=url,
                status_code=200,
                title=title,
                message=f"셀렉터 '{selector}' " + (
                    f"텍스트 일치: '{expected_text}'" if expected_text else "존재 확인"
                ),
                screenshot_path=saved_path,
                selector_matched=matched,
            )
    except Exception as e:
        return E2EResult(
            ok=False,
            url=url,
            status_code=None,
            title=None,
            message=f"Playwright 오류: {e!s}",
        )


def _extract_title(html: str) -> str | None:
    """HTML에서 <title> 태그 추출."""
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip()[:200] if m else None


def to_dict(r: E2EResult) -> dict[str, Any]:
    """E2EResult를 JSON 직렬화 가능한 dict로 변환."""
    return {
        "ok": r.ok,
        "url": r.url,
        "status_code": r.status_code,
        "title": r.title,
        "message": r.message,
        "screenshot_path": r.screenshot_path,
        "selector_matched": r.selector_matched,
    }
