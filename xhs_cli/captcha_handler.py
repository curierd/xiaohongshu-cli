"""Captcha handler for XHS API — opens browser for manual verification."""

from __future__ import annotations

import logging
import time
from typing import Any

from .constants import HOME_URL
from .cookies import save_cookies


logger = logging.getLogger(__name__)


BROWSER_EXPORT_COOKIE_NAMES = (
    "a1",
    "webId",
    "web_session",
    "web_session_sec",
    "id_token",
    "websectiga",
    "sec_poison_id",
    "xsecappid",
    "gid",
    "abRequestId",
    "webBuild",
    "loadts",
)


def _normalize_browser_cookies(raw_cookies: list[dict[str, Any]]) -> dict[str, str]:
    """Convert Playwright cookies to dict."""
    cookies: dict[str, str] = {}
    for entry in raw_cookies:
        name = entry.get("name")
        value = entry.get("value")
        domain = entry.get("domain", "")
        if not isinstance(name, str) or not isinstance(value, str):
            continue
        if name not in BROWSER_EXPORT_COOKIE_NAMES:
            continue
        if not isinstance(domain, str) or "xiaohongshu.com" not in domain:
            continue
        cookies[name] = value
    return cookies


def handle_captcha_with_browser(
    cookies: dict[str, str],
    verify_type: str,
    verify_uuid: str,
) -> dict[str, str] | None:
    """
    Open browser for manual captcha verification.

    Returns updated cookies if successful, None otherwise.
    """
    print(f"\n🔐 Captcha required! (type={verify_type}, uuid={verify_uuid})")
    print("🌐 Opening browser for manual verification...\n")

    try:
        from camoufox.sync_api import Camoufox
    except ImportError:
        print("❌ Camoufox not available. Please install: pip install camoufox")
        print("   Then fetch browser: python -m camoufox fetch")
        return None

    try:
        with Camoufox(headless=False) as browser:
            page = browser.new_page()

            # Inject current cookies
            cookie_list = []
            for name, value in cookies.items():
                if name in BROWSER_EXPORT_COOKIE_NAMES:
                    cookie_list.append({
                        "name": name,
                        "value": value,
                        "domain": ".xiaohongshu.com",
                        "path": "/",
                    })

            if cookie_list:
                page.context.add_cookies(cookie_list)
                logger.debug("Injected %d cookies", len(cookie_list))

            # Navigate to XHS homepage
            print(f"👉 Please complete the captcha in the browser")
            print(f"👉 Navigating to {HOME_URL}...")
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30000)

            # Try to navigate to explore page to trigger verification
            try:
                page.wait_for_url("**/explore**", timeout=15000)
            except Exception:
                pass

            print("\n" + "=" * 60)
            print("📝 INSTRUCTIONS:")
            print("1. Complete any captcha/verification in the browser")
            print("2. Make sure you can see the Xiaohongshu homepage/explore page")
            print("3. When done, come back here and press Enter")
            print("=" * 60 + "\n")

            input("Press Enter when you've completed verification... ")

            # Wait a bit for cookies to update
            time.sleep(2)

            # Get updated cookies
            updated_cookies = _normalize_browser_cookies(page.context.cookies())

            # Merge with original cookies (preserve all values)
            final_cookies = {**cookies, **updated_cookies}

            # Save immediately
            save_cookies(final_cookies)
            print(f"\n✅ Saved updated cookies ({len(updated_cookies)} values)")

            return final_cookies

    except Exception as e:
        logger.error("Browser captcha handling failed: %s", e)
        print(f"❌ Browser verification failed: {e}")
        return None
