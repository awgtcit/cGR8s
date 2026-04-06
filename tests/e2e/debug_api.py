"""Quick diagnostic test - captures API responses."""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    responses = []
    def on_response(resp):
        if "api/load-codes" in resp.url or resp.status >= 400:
            try:
                body = resp.text()[:500]
            except:
                body = "<could not read>"
            responses.append({"url": resp.url, "status": resp.status, "body": body})
    page.on("response", on_response)

    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # Auth
    page.goto("http://127.0.0.1:5053/login/test-bypass", wait_until="networkidle")
    print("Auth OK, url:", page.url)

    # FG Codes
    page.goto("http://127.0.0.1:5053/fg-codes/", wait_until="networkidle")
    time.sleep(3)

    print(f"\nAPI responses: {len(responses)}")
    for r in responses:
        print(f"  [{r['status']}] {r['url']}")
        print(f"    Body: {r['body'][:300]}")

    print(f"\nConsole errors: {len(errors)}")
    for e in errors:
        print(f"  {e}")

    browser.close()
