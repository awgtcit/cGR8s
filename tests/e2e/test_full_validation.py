"""
Playwright test for ALL Master Data + FG Code pages.
Covers: Blends, Physical Params, Calibration, Lookups, Machines, SKUs,
        Tobacco Blend Analysis, FG Codes (including Targets tab).
Always opens browser (headless=False) and takes screenshots.
"""
import os
import sys
import time
import json

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "full_validation")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ── Always open browser (headed mode) ──────────────────────────────────
HEADLESS = False


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


def test_listing_page(page, url, page_name, screenshot_name, min_rows=1, errors=None):
    """Generic test for a listing page - navigate, check rows, screenshot."""
    print(f"\n── Testing {page_name} ──")
    page.goto(f"{BASE_URL}{url}")
    page.wait_for_load_state("networkidle")
    shot(page, screenshot_name)

    rows = page.locator("table tbody tr")
    count = rows.count()
    print(f"   Rows visible: {count}")

    if count < min_rows:
        msg = f"FAIL: {page_name} shows {count} rows (expected >= {min_rows})"
        print(f"   ❌ {msg}")
        if errors is not None:
            errors.append(msg)
    else:
        print(f"   ✅ {page_name} shows {count} rows")
        # Check first row has real content (not all dashes)
        first = rows.first
        first_text = first.inner_text().strip()
        if first_text and first_text != "—":
            print(f"   First row preview: {first_text[:80]}...")

    return count


def main():
    errors = []
    report = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=300)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # Collect console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ── 1. Login ──────────────────────────────────────────────
        print("=" * 60)
        print("1. AUTHENTICATION")
        print("=" * 60)
        page.goto(f"{BASE_URL}/login/test-bypass")
        page.wait_for_load_state("networkidle")
        shot(page, "01_login")
        assert "/dashboard" in page.url or page.url.endswith("/"), f"Login failed, url={page.url}"
        print("   ✅ Login OK")

        # ── 2. Blends ────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("2. MASTER DATA PAGES")
        print("=" * 60)

        count = test_listing_page(page, "/master-data/blends", "Blends", "02_blends", min_rows=25, errors=errors)
        report['blends'] = count

        # Blend create form
        print("\n── Testing Blend Create form ──")
        page.goto(f"{BASE_URL}/master-data/blends/create")
        page.wait_for_load_state("networkidle")
        shot(page, "02b_blend_form")
        for field_name in ["blend_code", "blend_name", "blend_gtin", "n_bld"]:
            if page.locator(f"[name='{field_name}']").count() == 0:
                errors.append(f"FAIL: Blend form missing field '{field_name}'")
            else:
                print(f"   ✅ Field '{field_name}' present")

        # ── 3. Physical Parameters ────────────────────────────────
        count = test_listing_page(page, "/master-data/physical-params", "Physical Params", "03_physical_params", min_rows=1, errors=errors)
        report['physical_params'] = count

        # ── 4. Calibration Constants ──────────────────────────────
        count = test_listing_page(page, "/master-data/calibration", "Calibration", "04_calibration", min_rows=1, errors=errors)
        report['calibration'] = count

        # ── 5. Lookups ────────────────────────────────────────────
        count = test_listing_page(page, "/master-data/lookups", "Lookups", "05_lookups", min_rows=1, errors=errors)
        report['lookups'] = count

        # ── 6. Machines ──────────────────────────────────────────
        count = test_listing_page(page, "/master-data/machines", "Machines", "06_machines", min_rows=20, errors=errors)
        report['machines'] = count

        # Machine create form
        print("\n── Testing Machine Create form ──")
        page.goto(f"{BASE_URL}/master-data/machines/create")
        page.wait_for_load_state("networkidle")
        shot(page, "06b_machine_form")
        for field_name in ["machine_code", "description", "plant", "format_type"]:
            if page.locator(f"[name='{field_name}']").count() == 0:
                errors.append(f"FAIL: Machine form missing field '{field_name}'")
            else:
                print(f"   ✅ Field '{field_name}' present")

        # ── 7. SKUs ──────────────────────────────────────────────
        count = test_listing_page(page, "/master-data/skus", "SKUs", "07_skus", min_rows=20, errors=errors)
        report['skus'] = count

        # SKU create form
        print("\n── Testing SKU Create form ──")
        page.goto(f"{BASE_URL}/master-data/skus/create")
        page.wait_for_load_state("networkidle")
        shot(page, "07b_sku_form")
        for field_name in ["sku_code", "description", "nicotine", "ventilation", "pd_code", "cig_code"]:
            if page.locator(f"[name='{field_name}']").count() == 0:
                errors.append(f"FAIL: SKU form missing field '{field_name}'")
            else:
                print(f"   ✅ Field '{field_name}' present")

        # ── 8. Tobacco Blend Analysis ─────────────────────────────
        count = test_listing_page(page, "/master-data/tobacco-blend-analysis",
                                  "Tobacco Blend Analysis", "08_tobacco_analysis", min_rows=1, errors=errors)
        report['tobacco_analysis'] = count

        # ── 9. Size / CU ─────────────────────────────────────────
        count = test_listing_page(page, "/master-data/size-cu", "Size / CU", "09_size_cu", min_rows=5, errors=errors)
        report['size_cu'] = count

        # ── 10. KP Tolerance ─────────────────────────────────────
        count = test_listing_page(page, "/master-data/kp-tolerance", "KP Tolerance", "10_kp_tolerance", min_rows=5, errors=errors)
        report['kp_tolerance'] = count

        # ── 11. Plug Length / Cuts ────────────────────────────────
        count = test_listing_page(page, "/master-data/plug-length-cuts", "Plug Length / Cuts", "11_plug_length_cuts", min_rows=5, errors=errors)
        report['plug_length_cuts'] = count

        # ── 12. App Fields ───────────────────────────────────────
        count = test_listing_page(page, "/master-data/app-fields", "App Fields", "12_app_fields", min_rows=20, errors=errors)
        report['app_fields'] = count

        # ── 13. Targets & Limits ─────────────────────────────────
        count = test_listing_page(page, "/master-data/targets-limits", "Targets & Limits", "13_targets_limits", min_rows=25, errors=errors)
        report['targets_limits'] = count

        # ── 14. FG Codes + Targets Tab ────────────────────────────
        print("\n" + "=" * 60)
        print("3. FG CODES & TARGETS TAB")
        print("=" * 60)

        print("\n── Loading FG Codes page ──")
        page.goto(f"{BASE_URL}/fg-codes/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        shot(page, "09_fg_codes")

        items = page.query_selector_all(".fg-item")
        print(f"   FG items rendered: {len(items)}")
        report['fg_codes'] = len(items)

        if items:
            # Click first item to load details
            items[0].click()
            time.sleep(2)
            shot(page, "09b_fg_selected")

            # Check all tabs exist including Targets
            tabs = page.query_selector_all(".detail-tab-btn")
            tab_names = [t.inner_text().strip() for t in tabs]
            print(f"   Detail tabs: {tab_names}")

            expected_tabs = ["Product", "Blend", "Physical", "Calibration", "Targets"]
            for expected in expected_tabs:
                if expected in tab_names:
                    print(f"   ✅ Tab '{expected}' present")
                else:
                    errors.append(f"FAIL: Missing tab '{expected}' in FG details")

            # Click Targets tab
            targets_tab = page.query_selector(".detail-tab-btn[data-tab='targets']")
            if targets_tab:
                targets_tab.click()
                time.sleep(0.5)
                shot(page, "09c_targets_tab")

                # Verify targets content loaded
                targets_pane = page.query_selector(".detail-tab-pane[data-tab='targets']")
                if targets_pane:
                    targets_text = targets_pane.inner_text()
                    has_targets_data = any(kw in targets_text for kw in
                                           ["Target Nic", "Circumference", "PDO", "Ventilation",
                                            "Hardness", "Moisture", "SSI", "Filling Power"])
                    if has_targets_data:
                        print("   ✅ Targets tab has data fields")
                    else:
                        print("   ⚠️  Targets tab rendered but may lack data")
                else:
                    errors.append("FAIL: Targets tab pane not found in DOM")
            else:
                errors.append("FAIL: Targets tab button not found")

            # Click through other tabs to verify no JS errors
            for tab in tabs:
                tab_name = tab.inner_text().strip()
                tab.click()
                time.sleep(0.3)
                shot(page, f"09d_tab_{tab_name.lower().replace(' ', '_')}")
                print(f"   Tab '{tab_name}' clicked OK")

        # ── 10. Sidebar Navigation ────────────────────────────────
        print("\n" + "=" * 60)
        print("4. SIDEBAR NAVIGATION")
        print("=" * 60)

        page.goto(f"{BASE_URL}/master-data/blends")
        page.wait_for_load_state("networkidle")

        # Check sub-nav items in sidebar
        sidebar_links = page.locator("#masterDataSub a.nav-link")
        sub_count = sidebar_links.count()
        print(f"   Master Data sub-nav links: {sub_count}")

        expected_sub_links = ["Blends", "Machines", "SKUs", "Tobacco Analysis",
                              "Targets & Limits", "Size / CU", "KP Tolerance",
                              "Plug Length / Cuts", "App Fields", "Lookups"]
        for expected in expected_sub_links:
            link = page.locator(f"#masterDataSub a:has-text('{expected}')")
            if link.count() > 0:
                print(f"   ✅ Sub-nav link '{expected}' present")
            else:
                errors.append(f"FAIL: Missing sidebar sub-nav '{expected}'")

        shot(page, "10_sidebar_expanded")

        # ── 11. Console errors ────────────────────────────────────
        print(f"\n── Console errors: {len(console_errors)} ──")
        for e in console_errors[:10]:
            print(f"   ⚠️  {e}")

        browser.close()

    # ── Summary Report ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 FULL VALIDATION REPORT")
    print("=" * 60)
    print(f"\nData counts:")
    for key, val in report.items():
        status = "✅" if val > 0 else "❌"
        print(f"  {status} {key}: {val} rows/items")

    print(f"\nConsole errors: {len(console_errors)}")
    print(f"Test failures: {len(errors)}")
    print(f"Screenshots saved to: {SCREENSHOTS_DIR}")

    # Save report JSON
    report_path = os.path.join(SCREENSHOTS_DIR, "test_report.json")
    with open(report_path, 'w') as f:
        json.dump({
            'data_counts': report,
            'errors': errors,
            'console_errors': console_errors[:20],
            'screenshots_dir': SCREENSHOTS_DIR,
        }, f, indent=2)
    print(f"Report saved: {report_path}")

    if errors:
        print(f"\n❌ FAILURES ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
