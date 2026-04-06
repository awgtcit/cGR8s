"""Playwright test for FG Codes page - UI validation and screenshots."""
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "fg_codes")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # ── 1. Auth ────────────────────────────────────
        print("\n🔐 Authenticating via test-bypass…")
        page.goto(f"{BASE_URL}/login/test-bypass", wait_until="networkidle")
        shot(page, "01_after_login")
        print(f"  URL after login: {page.url}")

        # ── 2. Navigate to FG Codes ────────────────────
        print("\n📄 Opening FG Codes page…")
        page.goto(f"{BASE_URL}/fg-codes/", wait_until="networkidle")
        time.sleep(2)  # wait for AJAX load
        shot(page, "02_fg_codes_initial")
        print(f"  URL: {page.url}")

        # Check if codes loaded
        items = page.query_selector_all(".fg-item")
        print(f"  FG items rendered: {len(items)}")

        count_el = page.query_selector("#recordCount")
        count_text = count_el.inner_text() if count_el else "N/A"
        print(f"  Record count badge: {count_text}")

        # Check for errors in console
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ── 3. Search functionality ────────────────────
        print("\n🔍 Testing search…")
        search = page.query_selector("#searchInput")
        if search:
            search.fill("Bon One")
            time.sleep(1.5)
            shot(page, "03_search_bon_one")
            items_after = page.query_selector_all(".fg-item")
            print(f"  Items after 'Bon One' search: {len(items_after)}")
            search.fill("")
            time.sleep(1)

        # ── 4. Select a data-rich FG Code ─────────────
        print("\n👆 Selecting a data-rich FG Code (Bon One White .02)…")
        search = page.query_selector("#searchInput")
        if search:
            search.fill("11202239")
            time.sleep(1.5)
        items = page.query_selector_all(".fg-item")
        target_idx = 1 if len(items) > 1 else 0  # .02 is second
        if items:
            items[target_idx].click()
            time.sleep(2)
            shot(page, "04_fg_selected")

            # Check SKU details loaded
            selected_badge = page.query_selector("#selectedBadge")
            badge_text = selected_badge.inner_text() if selected_badge else "N/A"
            print(f"  Selected badge: {badge_text}")

            # Check details content
            details = page.query_selector("#skuDetailsContent")
            details_text = details.inner_text() if details else ""
            has_details = "FG Code" in details_text or "Brand" in details_text
            print(f"  Details loaded: {has_details}")

            # Check key variables populated
            n_bld = page.query_selector("#n_bld")
            n_bld_val = n_bld.input_value() if n_bld else "N/A"
            print(f"  N_BLD value: {n_bld_val}")

            # ── 5. Tab switching ───────────────────────
            print("\n📑 Testing detail tabs…")
            tabs = page.query_selector_all(".detail-tab-btn")
            for tab in tabs:
                tab_name = tab.inner_text()
                tab.click()
                time.sleep(0.3)
                shot(page, f"05_tab_{tab_name.lower().replace(' ', '_')}")
                print(f"  Tab '{tab_name}' clicked")

            # ── 6. Calculate target ────────────────────
            print("\n🧮 Testing calculation…")
            calc_btn = page.query_selector("#calculateBtn")
            if calc_btn and not calc_btn.is_disabled():
                calc_btn.click()
                time.sleep(2)
                shot(page, "06_calculation_result")

                results = page.query_selector("#resultsContent")
                results_text = results.inner_text() if results else ""
                has_results = "Target Weight" in results_text or "Dilution" in results_text or "W" in results_text
                print(f"  Results rendered: {has_results}")
                print(f"  Results text: {results_text[:200]}")
            else:
                print("  Calculate button disabled or not found")

            # ── 7. Process Order modal ─────────────────
            print("\n📋 Testing Process Order modal…")
            po_btn = page.query_selector("#createPOBtn")
            if po_btn and not po_btn.is_disabled():
                po_btn.click()
                time.sleep(1)
                shot(page, "07_process_order_modal")

                modal_visible = page.query_selector("#processOrderModal.show")
                print(f"  Modal visible: {modal_visible is not None}")

                # Close modal
                close = page.query_selector("#processOrderModal .btn-close")
                if close:
                    close.click()
                    time.sleep(0.5)
            else:
                print("  Process Order button disabled or not found")

        else:
            print("  ❌ No FG items found! Check API endpoint.")
            shot(page, "04_NO_ITEMS_ERROR")

        # ── 8. Responsive view (tablet) ────────────────
        print("\n📱 Testing responsive (tablet)…")
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(f"{BASE_URL}/fg-codes/", wait_until="networkidle")
        time.sleep(2)
        shot(page, "08_responsive_tablet")

        # ── 9. Responsive view (mobile) ────────────────
        print("\n📱 Testing responsive (mobile)…")
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(f"{BASE_URL}/fg-codes/", wait_until="networkidle")
        time.sleep(2)
        shot(page, "09_responsive_mobile")

        # Reset viewport
        page.set_viewport_size({"width": 1440, "height": 900})

        # ── 10. Check other pages ──────────────────────
        print("\n🏠 Testing other pages…")
        pages_to_test = [
            ("/", "10_dashboard"),
            ("/master-data/", "11_master_data"),
            ("/admin/", "12_admin"),
        ]
        for path, name in pages_to_test:
            page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
            time.sleep(1)
            shot(page, name)
            status_code = "OK" if "404" not in page.title().lower() and "error" not in page.title().lower() else "ISSUE"
            print(f"  {path} → {status_code} (title: {page.title()})")

        # ── Summary ────────────────────────────────────
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Screenshots saved to: {SCREENSHOTS_DIR}")
        print(f"Console errors: {len(console_errors)}")
        for e in console_errors[:10]:
            print(f"  ⚠️  {e}")

        browser.close()
        print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
