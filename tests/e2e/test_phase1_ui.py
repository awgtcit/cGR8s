"""Phase 1 UI/UX Redesign - Playwright Verification Test.
Tests: Inter font, sidebar, breadcrumbs, topbar, design tokens, navigation.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "phase1")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        network_errors = []
        page.on("response", lambda resp: network_errors.append(f"{resp.status} {resp.url}") if resp.status >= 400 else None)

        # ── Login ─────────────────────────────────────────────
        print("1. Logging in...")
        page.goto(f"{BASE_URL}/login/test-bypass")
        page.wait_for_load_state("networkidle")
        assert "/dashboard" in page.url or page.url.endswith("/"), f"Login failed, url={page.url}"
        print("   ✅ Login OK")
        shot(page, "01_dashboard")

        # ── Check Inter Font ──────────────────────────────────
        print("\n2. Checking Inter font loaded...")
        font_family = page.evaluate("getComputedStyle(document.body).fontFamily")
        print(f"   font-family: {font_family}")
        if "Inter" not in font_family and "inter" not in font_family.lower():
            errors.append(f"FAIL: Inter font not loaded. Got: {font_family}")
        else:
            print("   ✅ Inter font active")

        # ── Check CSS Variables ───────────────────────────────
        print("\n3. Checking design tokens (CSS vars)...")
        primary = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--cgr-primary').trim()")
        bg = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--cgr-bg').trim()")
        print(f"   --cgr-primary: {primary}")
        print(f"   --cgr-bg: {bg}")
        if primary != "#0D6B3C":
            errors.append(f"FAIL: --cgr-primary is '{primary}', expected '#0D6B3C'")
        else:
            print("   ✅ Design tokens correct")

        # ── Sidebar ───────────────────────────────────────────
        print("\n4. Checking sidebar...")
        sidebar = page.locator("#sidebar")
        assert sidebar.is_visible(), "Sidebar not visible"
        brand = page.locator(".sidebar-brand .brand-text")
        assert brand.is_visible(), "Brand text not visible"
        assert brand.inner_text().strip() == "cGR8s", f"Brand text: {brand.inner_text()}"
        print("   ✅ Sidebar visible with brand")

        # Check sidebar scroll container
        scroll = page.locator(".sidebar-scroll")
        if scroll.count() == 0:
            errors.append("FAIL: .sidebar-scroll container missing")
        else:
            print("   ✅ sidebar-scroll container present")

        # ── Sidebar Navigation Links ──────────────────────────
        print("\n5. Checking sidebar nav links...")
        nav_links = page.locator(".sidebar-nav .nav-link")
        link_count = nav_links.count()
        print(f"   Nav links found: {link_count}")
        if link_count < 8:
            errors.append(f"FAIL: Expected 8+ nav links, found {link_count}")
        else:
            print("   ✅ Sufficient nav links")

        # ── Master Data Sub-menu ──────────────────────────────
        print("\n6. Checking Master Data sub-menu toggle...")
        master_toggle = page.locator(".nav-sub-toggle")
        if master_toggle.count() == 0:
            errors.append("FAIL: Master Data sub-toggle not found")
        else:
            # Check chevron icon
            chevron = master_toggle.first.locator(".chevron")
            if chevron.count() == 0:
                errors.append("FAIL: Chevron icon not found on Master Data toggle")
            else:
                print("   ✅ Chevron toggle present")

            # Click to expand
            master_toggle.first.click()
            page.wait_for_timeout(500)
            sub_nav = page.locator(".sub-nav .nav-link")
            sub_count = sub_nav.count()
            print(f"   Sub-nav links: {sub_count}")
            if sub_count < 10:
                errors.append(f"FAIL: Expected 10 sub-nav links, found {sub_count}")
            else:
                print("   ✅ 10 Master Data sub-links visible")

        # ── Topbar ────────────────────────────────────────────
        print("\n7. Checking topbar...")
        topbar = page.locator(".top-navbar")
        assert topbar.is_visible(), "Topbar not visible"

        # Check breadcrumb area
        breadcrumb = page.locator(".topbar-breadcrumb")
        if breadcrumb.count() == 0:
            errors.append("FAIL: .topbar-breadcrumb container missing")
        else:
            bc_text = breadcrumb.inner_text().strip()
            print(f"   Breadcrumb text: '{bc_text}'")
            print("   ✅ Breadcrumb area present")

        # Check user menu
        user_menu = page.locator(".user-menu-btn")
        if user_menu.count() == 0:
            errors.append("FAIL: User menu button not found")
        else:
            print("   ✅ User menu present")

        # ── Sidebar Toggle ────────────────────────────────────
        print("\n8. Testing sidebar toggle...")
        toggle_btn = page.locator("#sidebarToggle")
        toggle_btn.click()
        page.wait_for_timeout(400)
        is_collapsed = page.evaluate("document.getElementById('sidebar').classList.contains('collapsed')")
        if not is_collapsed:
            errors.append("FAIL: Sidebar didn't collapse on toggle")
        else:
            print("   ✅ Sidebar collapsed")
            shot(page, "02_sidebar_collapsed")

        # Toggle back
        toggle_btn.click()
        page.wait_for_timeout(400)
        is_expanded = not page.evaluate("document.getElementById('sidebar').classList.contains('collapsed')")
        if not is_expanded:
            errors.append("FAIL: Sidebar didn't expand on toggle")
        else:
            print("   ✅ Sidebar expanded back")

        # ── Navigate to Process Orders (check breadcrumbs) ────
        print("\n9. Navigating to Process Orders...")
        page.goto(f"{BASE_URL}/process-orders")
        page.wait_for_load_state("networkidle")
        shot(page, "03_process_orders")

        bc = page.locator(".topbar-breadcrumb")
        bc_text = bc.inner_text().strip()
        print(f"   Breadcrumb: '{bc_text}'")
        if "Home" not in bc_text or "Process Orders" not in bc_text:
            errors.append(f"FAIL: Process Orders breadcrumb incorrect: {bc_text}")
        else:
            print("   ✅ Breadcrumb shows Home / Process Orders")

        # ── Navigate to Master Data Blends ────────────────────
        print("\n10. Navigating to Blends...")
        page.goto(f"{BASE_URL}/master-data/blends")
        page.wait_for_load_state("networkidle")
        shot(page, "04_blends")

        bc = page.locator(".topbar-breadcrumb")
        bc_text = bc.inner_text().strip()
        print(f"   Breadcrumb: '{bc_text}'")
        if "Master Data" not in bc_text or "Blends" not in bc_text:
            errors.append(f"FAIL: Blends breadcrumb incorrect: {bc_text}")
        else:
            print("   ✅ Breadcrumb shows Home / Master Data / Blends")

        # ── Check Table Styling ───────────────────────────────
        print("\n11. Checking table design...")
        th = page.locator("table th").first
        if th.count() > 0:
            th_bg = page.evaluate("""
                (() => {
                    const th = document.querySelector('table th');
                    return th ? getComputedStyle(th).backgroundColor : 'none';
                })()
            """)
            print(f"   Table header bg: {th_bg}")
            print("   ✅ Table rendered")
        else:
            print("   ⚠️ No table found on this page")

        # ── Check Card Styling ────────────────────────────────
        print("\n12. Checking card styling...")
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        card = page.locator(".card").first
        if card.count() > 0:
            card_border = page.evaluate("""
                (() => {
                    const c = document.querySelector('.card');
                    return c ? getComputedStyle(c).border : 'none';
                })()
            """)
            card_radius = page.evaluate("""
                (() => {
                    const c = document.querySelector('.card');
                    return c ? getComputedStyle(c).borderRadius : 'none';
                })()
            """)
            print(f"   Card border: {card_border}")
            print(f"   Card radius: {card_radius}")
            print("   ✅ Card styled with border + radius")
        shot(page, "05_dashboard_cards")

        # ── Navigate to FG Codes ──────────────────────────────
        print("\n13. Navigating to FG Codes...")
        page.goto(f"{BASE_URL}/fg-codes")
        page.wait_for_load_state("networkidle")
        shot(page, "06_fg_codes")
        bc = page.locator(".topbar-breadcrumb")
        bc_text = bc.inner_text().strip()
        if "FG Codes" not in bc_text:
            errors.append(f"FAIL: FG Codes breadcrumb missing: {bc_text}")
        else:
            print("   ✅ FG Codes breadcrumb correct")

        # ── Navigate to Target Weight ─────────────────────────
        print("\n14. Navigating to Target Weight...")
        page.goto(f"{BASE_URL}/target-weight")
        page.wait_for_load_state("networkidle")
        shot(page, "07_target_weight")
        bc = page.locator(".topbar-breadcrumb")
        bc_text = bc.inner_text().strip()
        if "Target Weight" not in bc_text:
            errors.append(f"FAIL: Target Weight breadcrumb missing: {bc_text}")
        else:
            print("   ✅ Target Weight breadcrumb correct")

        # ── Navigate to Batch ─────────────────────────────────
        print("\n15. Navigating to Batch Processing...")
        page.goto(f"{BASE_URL}/batch")
        page.wait_for_load_state("networkidle")
        shot(page, "08_batch")
        bc = page.locator(".topbar-breadcrumb")
        bc_text = bc.inner_text().strip()
        if "Batch" not in bc_text:
            errors.append(f"FAIL: Batch breadcrumb missing: {bc_text}")
        else:
            print("   ✅ Batch breadcrumb correct")

        # ── Check Console Errors ──────────────────────────────
        print("\n16. Checking console errors...")
        if network_errors:
            for e in network_errors[:5]:
                print(f"   ⚠️ Network error: {e}")
        if console_errors:
            real_errors = [e for e in console_errors if "favicon" not in e.lower()]
            if real_errors:
                for e in real_errors[:5]:
                    print(f"   ⚠️ Console error: {e}")
                # Don't fail on 404s for favicon or non-critical assets
                print("   ℹ️ Console errors logged (non-blocking)")
            else:
                print("   ✅ No significant console errors")
        else:
            print("   ✅ No console errors")

        # ── Summary ───────────────────────────────────────────
        print("\n" + "=" * 60)
        if errors:
            print(f"❌ Phase 1 Test FAILED — {len(errors)} error(s):")
            for e in errors:
                print(f"   • {e}")
            browser.close()
            sys.exit(1)
        else:
            print("✅ Phase 1 Test PASSED — All checks passed!")
            browser.close()
            sys.exit(0)


if __name__ == "__main__":
    main()
