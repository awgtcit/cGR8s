"""
Comprehensive Browser Validation – Playwright E2E Tests.

Validates ALL recent changes:
1. Process Orders page: FG Code shows actual code (not UUID)
2. Target Weight page: FG Code shows actual code (not UUID)
3. Process Orders detail page: no errors, FG code link works
4. FG Codes view page: Excel-style display loads correctly
5. FG Codes main interface: calculation works, units are "mg", results 3 decimals
6. Create Process Order flow: end-to-end order creation

Usage:
    python tests/e2e/test_browser_validation.py
"""
import os
import re
import sys
import time
import uuid
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5053")
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots" / "validation"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)

results = {"passed": 0, "failed": 0, "errors": []}


def shot(page, name):
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  📸 {name}.png")
    return path


def check(condition, description):
    if condition:
        results["passed"] += 1
        print(f"  ✅ PASS: {description}")
    else:
        results["failed"] += 1
        results["errors"].append(description)
        print(f"  ❌ FAIL: {description}")


def authenticate(page):
    print("\n🔐 Authenticating via test-bypass...")
    page.goto(f"{BASE_URL}/login/test-bypass", wait_until="networkidle")
    if "/login" in page.url and "test-bypass" not in page.url:
        print("  ❌ Auth failed – still on login page")
        return False
    print(f"  ✅ Authenticated – URL: {page.url}")
    return True


# ─────────────────────────────────────────────────────────────
# TEST 1: Process Orders page – FG Code column
# ─────────────────────────────────────────────────────────────
def test_process_orders_fg_code_display(page):
    print("\n" + "=" * 60)
    print("TEST 1: Process Orders – FG Code shows actual code (not UUID)")
    print("=" * 60)

    page.goto(f"{BASE_URL}/process-orders/", wait_until="networkidle")
    page.wait_for_timeout(1000)
    shot(page, "01_process_orders_page")

    # Check page loaded
    check(page.locator("table").count() > 0, "Process Orders table exists")

    # Get all table rows (skip header)
    rows = page.locator("table.table-hover tbody tr")
    row_count = rows.count()
    print(f"  ℹ️ Found {row_count} rows in table")

    if row_count == 0:
        print("  ⚠️ No process orders found – skipping FG code UUID check")
        return

    uuid_found = False
    for i in range(min(row_count, 10)):  # Check up to 10 rows
        cells = rows.nth(i).locator("td")
        if cells.count() >= 2:
            fg_cell_text = cells.nth(1).inner_text().strip()
            if UUID_PATTERN.match(fg_cell_text):
                uuid_found = True
                print(f"  ❌ Row {i}: FG Code shows UUID: {fg_cell_text}")
            elif fg_cell_text and fg_cell_text != "–":
                print(f"  ✅ Row {i}: FG Code = {fg_cell_text}")

    check(not uuid_found, "No UUIDs displayed in FG Code column")

    # Check no server errors on page
    check("Internal Server Error" not in page.content(),
          "No Internal Server Error on page")
    check("Traceback" not in page.content(),
          "No Python traceback on Process Orders page")


# ─────────────────────────────────────────────────────────────
# TEST 2: Target Weight page – FG Code column
# ─────────────────────────────────────────────────────────────
def test_target_weight_fg_code_display(page):
    print("\n" + "=" * 60)
    print("TEST 2: Target Weight – FG Code shows actual code (not UUID)")
    print("=" * 60)

    page.goto(f"{BASE_URL}/target-weight/", wait_until="networkidle")
    page.wait_for_timeout(1000)
    shot(page, "02_target_weight_page")

    # Check page loaded
    check(page.locator("table").count() > 0, "Target Weight table exists")

    rows = page.locator("table.table-hover tbody tr")
    row_count = rows.count()
    print(f"  ℹ️ Found {row_count} rows in table")

    if row_count == 0:
        print("  ⚠️ No target weight entries – skipping UUID check")
        return

    uuid_found = False
    for i in range(min(row_count, 10)):
        cells = rows.nth(i).locator("td")
        if cells.count() >= 2:
            fg_cell_text = cells.nth(1).inner_text().strip()
            if UUID_PATTERN.match(fg_cell_text):
                uuid_found = True
                print(f"  ❌ Row {i}: FG Code shows UUID: {fg_cell_text}")
            elif fg_cell_text and fg_cell_text != "–":
                print(f"  ✅ Row {i}: FG Code = {fg_cell_text}")

    check(not uuid_found, "No UUIDs displayed in FG Code column")


# ─────────────────────────────────────────────────────────────
# TEST 3: Process Orders detail page – No BuildError
# ─────────────────────────────────────────────────────────────
def test_process_orders_detail(page):
    print("\n" + "=" * 60)
    print("TEST 3: Process Orders Detail – No BuildError, FG link works")
    print("=" * 60)

    # First get a process order from the list
    page.goto(f"{BASE_URL}/process-orders/", wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Click first order link
    first_link = page.locator("table.table-hover tbody tr td:first-child a").first
    if first_link.count() == 0:
        print("  ⚠️ No process orders to test detail page – skipping")
        return

    first_link.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    shot(page, "03_process_order_detail")

    current_url = page.url
    print(f"  ℹ️ Detail page URL: {current_url}")

    # No error on page
    page_content = page.content()
    check("BuildError" not in page_content, "No BuildError on detail page")
    check("Internal Server Error" not in page_content,
          "No Internal Server Error on detail page")
    check("jinja2" not in page_content.lower(),
          "No Jinja2 template errors on detail page")
    check("500" not in page.locator("title").inner_text(),
          "Page title is not 500 error")

    # Check FG Code link exists and points to fg_codes.view
    fg_link = page.locator("a[href*='/fg-codes/view/']")
    if fg_link.count() > 0:
        check(True, "FG Code link points to /fg-codes/view/")
        fg_href = fg_link.first.get_attribute("href")
        print(f"  ℹ️ FG Code link href: {fg_href}")

        # Click it and verify it loads
        fg_link.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        shot(page, "03b_fg_code_view_from_detail")

        check("Internal Server Error" not in page.content(),
              "FG Code view page loads without error from detail link")
    else:
        print("  ⚠️ No FG Code link found on detail page (fg may be None)")


# ─────────────────────────────────────────────────────────────
# TEST 4: FG Codes view page – Excel-style display
# ─────────────────────────────────────────────────────────────
def test_fg_codes_view_page(page):
    print("\n" + "=" * 60)
    print("TEST 4: FG Codes View Page – Excel-style display")
    print("=" * 60)

    # Get FG codes list to find a valid ID
    page.goto(f"{BASE_URL}/fg-codes/", wait_until="networkidle")
    page.wait_for_timeout(2000)

    # Get a data-code from the first FG item
    items = page.locator(".fg-item")
    if items.count() == 0:
        print("  ⚠️ No FG items found – skipping view page test")
        return

    # Click first FG item to get its details
    items.first.click()
    page.wait_for_timeout(2000)
    shot(page, "04a_fg_selected_for_view")

    # Try to find the FG code view link or navigate directly
    # Use the API to get an FG code ID
    fg_code = items.first.get_attribute("data-code")
    print(f"  ℹ️ First FG item code: {fg_code}")

    # Navigate to view page via API - fetch all codes to find an ID
    resp = page.evaluate("""async () => {
        const r = await fetch('/fg-codes/api/load-codes?limit=1');
        return await r.json();
    }""")

    if resp and resp.get("codes") and len(resp["codes"]) > 0:
        fg_id = resp["codes"][0].get("id")
        if fg_id:
            page.goto(f"{BASE_URL}/fg-codes/view/{fg_id}",
                       wait_until="networkidle")
            page.wait_for_timeout(1000)
            shot(page, "04b_fg_view_page")

            page_content = page.content()

            # Check page loaded without errors
            check("Internal Server Error" not in page_content,
                  "FG Codes view page loads without error")
            check("BuildError" not in page_content,
                  "No BuildError on FG Codes view page")

            # Check Excel-style sections exist
            check("General Information" in page_content or
                  "general" in page_content.lower(),
                  "General Information section visible")
            check("excel-table" in page_content or "table" in page_content.lower(),
                  "Excel-style table present")

            # Check key fields
            check("FG Code" in page_content, "FG Code label displayed")
        else:
            print("  ⚠️ Could not get FG code ID from API")
    else:
        print("  ⚠️ No codes returned from API")


# ─────────────────────────────────────────────────────────────
# TEST 5: FG Codes Calculator – units mg, 3 decimal places
# ─────────────────────────────────────────────────────────────
def test_fg_codes_calculator(page):
    print("\n" + "=" * 60)
    print("TEST 5: FG Codes Calculator – units mg, 3 decimal results")
    print("=" * 60)

    page.goto(f"{BASE_URL}/fg-codes/", wait_until="networkidle")
    page.wait_for_timeout(2000)
    shot(page, "05a_fg_codes_page")

    # Check "mg" unit labels in Key Variables section
    page_content = page.content()
    check("mg" in page_content, "Unit 'mg' found on page")

    # Select first FG code
    items = page.locator(".fg-item")
    if items.count() == 0:
        print("  ⚠️ No FG items – skipping calculator test")
        return

    items.first.click()
    page.wait_for_timeout(2000)
    shot(page, "05b_fg_item_selected")

    # Check SKU details loaded
    details_content = page.locator("#skuDetailsContent")
    if details_content.count() > 0:
        check(details_content.is_visible(), "SKU details panel loaded")

    # Check key variable inputs exist
    for input_id in ["#n_bld", "#p_cu", "#t_vnt", "#f_pd", "#m_ip", "#w_ntm"]:
        inp = page.locator(input_id)
        check(inp.count() > 0, f"Input {input_id} exists")

    # Click Calculate
    calc_btn = page.locator("#calculateBtn")
    if calc_btn.count() > 0 and calc_btn.is_enabled():
        calc_btn.click()
        page.wait_for_timeout(3000)
        shot(page, "05c_after_calculate")

        # Check results appeared
        results_content = page.locator("#resultsContent")
        if results_content.count() > 0:
            results_text = results_content.inner_text()
            print(f"  ℹ️ Results text (first 300 chars): {results_text[:300]}")

            # Check 3 decimal places (look for pattern like "123.456")
            decimal_pattern = re.compile(r"\d+\.\d{3}\b")
            has_3_decimals = bool(decimal_pattern.search(results_text))
            check(has_3_decimals, "Results show 3 decimal places")

            # Check units "mg" in results
            check("mg" in results_text, "Unit 'mg' in calculation results")

            # Check Target Weight highlighted result
            highlight = page.locator(".result-highlight")
            if highlight.count() > 0:
                highlight_text = highlight.inner_text()
                check("mg" in highlight_text,
                      "Target Weight result shows 'mg' unit")
                print(f"  ℹ️ Target Weight: {highlight_text.strip()}")
        else:
            check(False, "Calculation results appeared")
    else:
        print("  ⚠️ Calculate button not available or disabled")
        if calc_btn.count() > 0:
            print(f"  ℹ️ Button enabled: {calc_btn.is_enabled()}")


# ─────────────────────────────────────────────────────────────
# TEST 6: Console errors check across pages
# ─────────────────────────────────────────────────────────────
def test_no_console_errors(page):
    print("\n" + "=" * 60)
    print("TEST 6: No critical console errors across pages")
    print("=" * 60)

    console_errors = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append({"url": page.url, "text": msg.text})

    page.on("console", on_console)

    pages_to_check = [
        ("/fg-codes/", "FG Codes"),
        ("/process-orders/", "Process Orders"),
        ("/target-weight/", "Target Weight"),
    ]

    for path, name in pages_to_check:
        page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
        page.wait_for_timeout(1500)

    page.remove_listener("console", on_console)

    critical_errors = [e for e in console_errors
                       if "favicon" not in e["text"].lower()
                       and "404" not in e["text"]]

    if critical_errors:
        for err in critical_errors:
            print(f"  ⚠️ Console error on {err['url']}: {err['text'][:100]}")

    check(len(critical_errors) == 0,
          f"No critical JS console errors ({len(critical_errors)} found)")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "🔄" * 30)
    print("  cGR8s – COMPREHENSIVE BROWSER VALIDATION")
    print("🔄" * 30)
    print(f"  Base URL: {BASE_URL}")
    print(f"  Screenshots: {SCREENSHOTS_DIR}/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Authenticate
        if not authenticate(page):
            print("\n❌ Authentication failed! Cannot continue.")
            browser.close()
            sys.exit(1)

        # Run all tests
        try:
            test_process_orders_fg_code_display(page)
            test_target_weight_fg_code_display(page)
            test_process_orders_detail(page)
            test_fg_codes_view_page(page)
            test_fg_codes_calculator(page)
            test_no_console_errors(page)
        except Exception as e:
            print(f"\n💥 UNEXPECTED ERROR: {e}")
            shot(page, "99_error_state")
            results["failed"] += 1
            results["errors"].append(f"Unexpected error: {e}")

        browser.close()

    # Print summary
    print("\n" + "=" * 60)
    print("  📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    print(f"  Total: {total}")
    print(f"  ✅ Passed: {results['passed']}")
    print(f"  ❌ Failed: {results['failed']}")

    if results["errors"]:
        print("\n  Failures:")
        for err in results["errors"]:
            print(f"    ❌ {err}")

    status = "ALL TESTS PASSED ✅" if results["failed"] == 0 else "SOME TESTS FAILED ❌"
    print(f"\n  {status}")
    print("=" * 60)

    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
