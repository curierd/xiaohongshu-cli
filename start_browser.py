#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

# Load cookies
cookie_path = Path.home() / ".xiaohongshu-cli" / "cookies.json"
if not cookie_path.exists():
    print("No cookies found!")
    sys.exit(1)

cookies = json.loads(cookie_path.read_text())
print(f"Loaded cookies: {list(cookies.keys())}")

# Launch Camoufox
try:
    from camoufox.sync_api import Camoufox
except ImportError:
    print("camoufox not installed")
    sys.exit(1)

BROWSER_COOKIES = (
    "a1", "webId", "web_session", "web_session_sec", "id_token",
    "websectiga", "sec_poison_id", "xsecappid", "gid", "abRequestId",
    "webBuild", "loadts"
)

with Camoufox(headless=False) as browser:
    page = browser.new_page()

    # Add cookies
    cookie_list = []
    for name, value in cookies.items():
        if name in BROWSER_COOKIES:
            cookie_list.append({
                "name": name,
                "value": value,
                "domain": ".xiaohongshu.com",
                "path": "/",
            })

    if cookie_list:
        page.context.add_cookies(cookie_list)
        print(f"Injected {len(cookie_list)} cookies")

    # Navigate to XHS
    print("Navigating to https://www.xiaohongshu.com/...")
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")

    print("\nBrowser is running! Press Ctrl+C to close.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing...")
