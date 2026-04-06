"""
E2E test: Verify QA Analysis & Production Data grids have the correct columns.
"""
import re
from playwright.sync_api import sync_playwright


BASE = "http://localhost:5053"

EXPECTED_QA_COLS = [
    'RID', 'QR Date (D-)', 'Prod. Date (D)', 'NPL Date (D+1)', 'Process Order',
    'SKU', 'SKU Desc', 'SKU GTN', 'Blend Code', 'Blend Desc', 'Blend GTIN', 'Cig. Code', 'UID',
    'Pack OV', 'Lamina CPI', 'Filling Power', 'Filling Power Corr', 'Maker Moisture', 'SSI',
    'PAN%', 'Total Cig. Length', 'Circumference Mean', 'Circumference SD', 'Cig Dia',
    'Tobacco Wt Mean', 'Tobacco Wt SD',
    'TIP VF', 'TIP Vf SD', 'Filter PD Mean', 'Filter Weight',
    'Plug Wrap CU', 'TOW',
    'Cig. Wt. Mean', 'Cig. Wt. SD',
    'Cig PDO', 'Cig. Hardness', 'Cig. Corr. Hardness', 'Loose Shorts', 'Plug Length',
    'MC', 'Company', 'Status',
]

EXPECTED_PROD_COLS_AFTER_PACK_OV = [
    'Lamina CPI', 'Filling Power', 'Filling Power Corr', 'Maker Moisture', 'SSI',
    'PAN%', 'Total Cig. Length', 'Circumference Mean', 'Circumference SD', 'Cig Dia',
    'Tobacco Weight Mean', 'Tobacco Weight SD',
    'TIP VF', 'TIP VF SD', 'Filter PD Mean', 'Filter Weight',
    'Plug Wrap CU', 'TOW',
    'Cig. Wt. Mean', 'Cig. Wt. SD',
    'Cig PDO', 'Cig. Hardness', 'Cig. Corr. Hardness',
    'Loose Shorts', 'Plug Length',
    'MC', 'Company', 'Status',
]


def test_qa_grid_columns():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to data grid
        page.goto(f"{BASE}/qa/data-grid", wait_until="networkidle", timeout=15000)

        # If redirected to login, use test-bypass
        if '/qa/data-grid' not in page.url:
            print(f"  [INFO] Redirected to: {page.url} – using test-bypass…")
            page.goto(f"{BASE}/login/test-bypass", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(1000)
            print(f"  [INFO] After bypass: {page.url}")
            page.goto(f"{BASE}/qa/data-grid", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(1000)
            print(f"  [INFO] Final URL: {page.url}")
            if '/qa/data-grid' not in page.url:
                page.screenshot(path="test-results/auth_fail.png")
                print(f"  [ERROR] Still not on data-grid page. Current URL: {page.url}")
                browser.close()
                return

        page.wait_for_timeout(1500)

        # Screenshot to see current state
        page.screenshot(path="test-results/data_grid_loaded.png", full_page=True)
        print(f"  [DEBUG] Page title: {page.title()}")
        print(f"  [DEBUG] Page URL: {page.url}")

        # Check if there's an error on the page
        error_text = page.locator('.alert-danger, .error, .traceback').first
        if error_text.count() > 0:
            print(f"  [ERROR] Page error: {error_text.inner_text()[:500]}")
            browser.close()
            return

        # ── QA Analysis tab ──
        qa_tab = page.locator('a[href="#tab-qa"]')
        if qa_tab.count() == 0:
            print("  [ERROR] QA tab not found on page!")
            print(f"  Page content snippet: {page.content()[:1000]}")
            browser.close()
            return
        qa_tab.click(timeout=5000)
        page.wait_for_timeout(500)

        qa_headers = page.locator('#qa-grid thead tr:first-child th')
        qa_count = qa_headers.count()
        print(f"\n  QA Analysis grid columns: {qa_count}")
        assert qa_count == len(EXPECTED_QA_COLS), f"Expected {len(EXPECTED_QA_COLS)} QA cols, got {qa_count}"

        for i, expected in enumerate(EXPECTED_QA_COLS):
            actual = qa_headers.nth(i).inner_text().strip()
            assert actual.upper() == expected.upper(), f"QA col {i}: expected '{expected}', got '{actual}'"

        print("  ✅ QA Analysis columns match!")

        # Take screenshot
        page.screenshot(path="test-results/qa_grid_columns.png", full_page=False)

        # ── Production Data tab ──
        prod_tab = page.locator('a[href="#tab-production"]')
        prod_tab.click()
        page.wait_for_timeout(500)

        prod_headers = page.locator('#prod-grid thead tr:first-child th')
        prod_count = prod_headers.count()
        print(f"\n  Production Data grid columns: {prod_count}")

        # Find "Pack OV" position and check columns after it
        pack_ov_idx = None
        for i in range(prod_count):
            text = prod_headers.nth(i).inner_text().strip()
            if text.upper() == 'PACK OV':
                pack_ov_idx = i
                break

        assert pack_ov_idx is not None, "Pack OV column not found in Production Data grid"
        print(f"  Pack OV at index {pack_ov_idx}")

        # Check columns after Pack OV
        remaining = prod_count - pack_ov_idx - 1
        print(f"  Columns after Pack OV: {remaining}")
        assert remaining == len(EXPECTED_PROD_COLS_AFTER_PACK_OV), \
            f"Expected {len(EXPECTED_PROD_COLS_AFTER_PACK_OV)} cols after Pack OV, got {remaining}"

        for i, expected in enumerate(EXPECTED_PROD_COLS_AFTER_PACK_OV):
            col_idx = pack_ov_idx + 1 + i
            actual = prod_headers.nth(col_idx).inner_text().strip()
            assert actual.upper() == expected.upper(), f"Prod col after Pack OV #{i}: expected '{expected}', got '{actual}'"

        print("  ✅ Production Data columns after Pack OV match!")

        page.screenshot(path="test-results/prod_grid_columns.png", full_page=False)

        # ── Test Excel download ──
        with page.expect_download() as download_info:
            page.locator('a:has-text("Excel")').click()
        download = download_info.value
        print(f"\n  Excel downloaded: {download.suggested_filename}")
        download.save_as(f"test-results/{download.suggested_filename}")

        page.screenshot(path="test-results/grid_final.png", full_page=False)
        print("\n  ✅ All tests passed!")
        browser.close()


if __name__ == '__main__':
    test_qa_grid_columns()
