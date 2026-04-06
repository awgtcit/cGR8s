"""
E2E test for Calibration tab (Gamma + N Target) and Master Data pages.
Validates:
  1. Formula Constants page loads (no ProgrammingError)
  2. Gamma Constants page shows full-format entries (not old short prefixes)
  3. FG Code Calibration tab shows correct gamma value (non-zero)
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5053")
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots" / "calibration"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

results = {"passed": 0, "failed": 0, "errors": []}


def shot(page, name):
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  📸 {name}.png")


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


def test_formula_constants_page(page):
    """Test 1: Formula Constants page loads without error."""
    print("\n" + "=" * 60)
    print("TEST 1: Formula Constants page loads")
    print("=" * 60)

    page.goto(f"{BASE_URL}/master-data/formula-constants", wait_until="networkidle")
    page.wait_for_timeout(1000)
    shot(page, "01_formula_constants")

    # Should NOT show ProgrammingError
    content = page.content()
    check("ProgrammingError" not in content, "No ProgrammingError on page")
    check("Invalid object name" not in content, "No 'Invalid object name' error")

    # Should show formula constants table
    has_alpha = page.locator("text=Alpha").count() > 0
    check(has_alpha, "Alpha constant visible")

    has_beta = page.locator("text=Beta").count() > 0
    check(has_beta, "Beta constant visible")

    has_delta = page.locator("text=Delta").count() > 0
    check(has_delta, "Delta constant visible")


def test_gamma_constants_page(page):
    """Test 2: Gamma Constants page shows full-format entries."""
    print("\n" + "=" * 60)
    print("TEST 2: Gamma Constants page - full format entries")
    print("=" * 60)

    page.goto(f"{BASE_URL}/master-data/gamma-constants", wait_until="networkidle")
    page.wait_for_timeout(1000)
    shot(page, "02_gamma_constants")

    content = page.content()

    # Should show full format entries like KS20SE, KS10SE
    has_ks20se = "KS20SE" in content
    check(has_ks20se, "KS20SE format entry visible")

    has_ks10se = "KS10SE" in content
    check(has_ks10se, "KS10SE format entry visible")

    # Reseed button should be present
    reseed_btn = page.locator("text=Reseed")
    check(reseed_btn.count() > 0, "Reseed button visible")


def test_fg_calibration_tab(page):
    """Test 3: FG Code Calibration tab shows correct gamma."""
    print("\n" + "=" * 60)
    print("TEST 3: FG Code Calibration tab - Gamma lookup")
    print("=" * 60)

    # Go to FG Codes page
    page.goto(f"{BASE_URL}/fg-codes/", wait_until="networkidle")
    page.wait_for_timeout(2000)
    shot(page, "03a_fg_codes_page")

    # Hit the API directly to check calibration data
    response = page.request.get(f"{BASE_URL}/fg-codes/api/sku-details/11130115.03")
    if response.ok:
        data = response.json()
        cal = data.get("calibration", {})
        print(f"  API response calibration: {cal}")

        alpha = cal.get("alpha", 0)
        beta = cal.get("beta", 0)
        gamma = cal.get("gamma", 0)
        delta = cal.get("delta", 0)
        n_tgt = cal.get("n_tgt", 0)
        fmt = cal.get("gamma_format", "")
        pl = cal.get("gamma_plug_length", 0)
        cond = cal.get("gamma_condition", "")

        check(alpha == 10.0, f"Alpha = 10.0 (got {alpha})")
        check(beta == -0.043, f"Beta = -0.043 (got {beta})")
        check(delta == -0.056, f"Delta = -0.056 (got {delta})")
        check(gamma > 0, f"Gamma > 0 (got {gamma})")
        check(fmt == "KS20SE", f"Gamma format = KS20SE (got {fmt})")
        check(pl == 21, f"Gamma plug_length = 21 (got {pl})")
        check(cond in ("TRUE", "FALSE"), f"Gamma condition = TRUE/FALSE (got {cond})")

        # If n_tgt < 0.3, condition should be TRUE and gamma should be 95
        if n_tgt < 0.3:
            check(cond == "TRUE", f"Condition TRUE when n_tgt={n_tgt} < 0.3")
            check(gamma == 95.0, f"Gamma = 95.0 for KS20SE/21/TRUE (got {gamma})")
        else:
            check(cond == "FALSE", f"Condition FALSE when n_tgt={n_tgt} >= 0.3")
            check(gamma == 85.0, f"Gamma = 85.0 for KS20SE/21/FALSE (got {gamma})")

        print(f"\n  N Target = {n_tgt} (from DB: target_nic or SKU.nicotine)")
    else:
        check(False, f"API returned {response.status}")
        return

    # Now click on the FG code in the list to see the Calibration tab
    # Search for the FG code
    search_input = page.locator("input[type='search'], input[placeholder*='Search'], input[placeholder*='search'], #fg-code-search, .fg-search")
    if search_input.count() > 0:
        search_input.first.fill("11130115.03")
        page.wait_for_timeout(1000)

    # Click on the FG code item
    fg_item = page.locator("text=11130115.03")
    if fg_item.count() > 0:
        fg_item.first.click()
        page.wait_for_timeout(2000)
        shot(page, "03b_fg_selected")

        # Click Calibration tab (use specific detail-tab-btn selector)
        cal_tab = page.locator('button.detail-tab-btn[data-tab="calibration"]')
        if cal_tab.count() > 0:
            cal_tab.first.click(timeout=5000)
            page.wait_for_timeout(1000)
            shot(page, "03c_calibration_tab")

            # Check the values in the calibration pane
            cal_pane = page.locator('div.detail-tab-pane[data-tab="calibration"]')
            pane_text = cal_pane.inner_text() if cal_pane.count() > 0 else page.content()
            check("KS20SE" in pane_text, "Format KS20SE shown in Calibration tab")
            check("95" in pane_text, "Gamma value 95 shown in Calibration tab")
        else:
            check(False, "Calibration tab not found")
    else:
        print("  ⚠️ FG code 11130115.03 not visible in list, skipping UI check")


def main():
    print("=" * 60)
    print("CALIBRATION & GAMMA E2E TEST")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        if not authenticate(page):
            print("\n💥 Auth failed, aborting")
            browser.close()
            sys.exit(1)

        test_formula_constants_page(page)
        test_gamma_constants_page(page)
        test_fg_calibration_tab(page)

        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    if results["errors"]:
        print("FAILURES:")
        for e in results["errors"]:
            print(f"  ❌ {e}")
    print("=" * 60)

    sys.exit(1 if results["failed"] else 0)


if __name__ == "__main__":
    main()
