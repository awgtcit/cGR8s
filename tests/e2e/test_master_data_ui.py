"""Playwright test for Master Data pages - UI validation and screenshots."""
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "master_data")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # Collect console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ── Login ─────────────────────────────────────────────────
        print("1. Logging in via test bypass...")
        page.goto(f"{BASE_URL}/login/test-bypass")
        page.wait_for_load_state("networkidle")
        assert "/dashboard" in page.url or page.url.endswith("/"), f"Login failed, url={page.url}"
        print("   ✅ Login OK")

        # ── Blends ────────────────────────────────────────────────
        print("\n2. Testing Blends page...")
        page.goto(f"{BASE_URL}/master-data/blends")
        page.wait_for_load_state("networkidle")
        shot(page, "01_blends_listing")

        # Check table has data
        rows = page.locator("table tbody tr")
        count = rows.count()
        print(f"   Blend rows visible: {count}")
        if count == 0:
            errors.append("FAIL: Blends listing shows 0 rows (expected 25)")
        else:
            print(f"   ✅ Blends listing shows {count} rows")
            # Check first row has columns
            first = rows.first
            cells = first.locator("td")
            cell_count = cells.count()
            print(f"   First row cells: {cell_count}")
            # Verify content is not empty dashes
            blend_code_text = cells.nth(0).inner_text().strip()
            print(f"   First blend code: {blend_code_text}")
            if not blend_code_text or blend_code_text == "—":
                errors.append("FAIL: Blend code column is empty")

        # Check no empty-state message
        if page.locator("text=No blends defined").count() > 0:
            errors.append("FAIL: 'No blends defined' empty state shown despite data")

        # ── Physical Parameters ───────────────────────────────────
        print("\n3. Testing Physical Parameters page...")
        page.goto(f"{BASE_URL}/master-data/physical-params")
        page.wait_for_load_state("networkidle")
        shot(page, "02_physical_params_listing")

        rows = page.locator("table tbody tr")
        count = rows.count()
        print(f"   Physical param rows visible: {count}")
        if count == 0:
            errors.append("FAIL: Physical params listing shows 0 rows")
        else:
            print(f"   ✅ Physical params listing shows {count} rows")
            first = rows.first
            fg_code_text = first.locator("td").first.inner_text().strip()
            print(f"   First FG Code: {fg_code_text}")
            if not fg_code_text or fg_code_text == "—":
                errors.append("FAIL: Physical param FG code column is empty")

        # ── Calibration Constants ─────────────────────────────────
        print("\n4. Testing Calibration Constants page...")
        page.goto(f"{BASE_URL}/master-data/calibration")
        page.wait_for_load_state("networkidle")
        shot(page, "03_calibration_listing")

        rows = page.locator("table tbody tr")
        count = rows.count()
        print(f"   Calibration rows visible: {count}")
        if count == 0:
            errors.append("FAIL: Calibration listing shows 0 rows")
        else:
            print(f"   ✅ Calibration listing shows {count} rows")
            first = rows.first
            fg_code_text = first.locator("td").first.inner_text().strip()
            alpha_text = first.locator("td").nth(1).inner_text().strip()
            print(f"   First FG Code: {fg_code_text}, Alpha: {alpha_text}")

        # ── Lookups ───────────────────────────────────────────────
        print("\n5. Testing Lookups page...")
        page.goto(f"{BASE_URL}/master-data/lookups")
        page.wait_for_load_state("networkidle")
        shot(page, "04_lookups_listing")

        rows = page.locator("table tbody tr")
        count = rows.count()
        print(f"   Lookup rows visible: {count}")
        if count == 0:
            errors.append("FAIL: Lookups listing shows 0 rows")
        else:
            print(f"   ✅ Lookups listing shows {count} rows")
            first = rows.first
            cat_text = first.locator("td").first.inner_text().strip()
            code_text = first.locator("td").nth(1).inner_text().strip()
            print(f"   First category: {cat_text}, code: {code_text}")

        # ── Blend Form ────────────────────────────────────────────
        print("\n6. Testing Blend Create form...")
        page.goto(f"{BASE_URL}/master-data/blends/create")
        page.wait_for_load_state("networkidle")
        shot(page, "05_blend_create_form")

        # Check form fields exist
        for field_name in ["blend_code", "blend_name", "blend_gtin", "n_bld"]:
            if page.locator(f"[name='{field_name}']").count() == 0:
                errors.append(f"FAIL: Blend form missing field '{field_name}'")
            else:
                print(f"   ✅ Field '{field_name}' present")

        # ── Console errors ────────────────────────────────────────
        print(f"\n7. Console errors: {len(console_errors)}")
        for e in console_errors:
            print(f"   ❌ {e}")
            errors.append(f"Console error: {e}")

        browser.close()

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if errors:
        print(f"FAILURES ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    else:
        print("ALL MASTER DATA TESTS PASSED ✅")
        sys.exit(0)


if __name__ == "__main__":
    main()
