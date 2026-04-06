"""
cGR8s – Comprehensive Playwright E2E Test Suite.

Tests every page, navigation flow, and core functionality.
Screenshots are saved to tests/e2e/screenshots/.

Usage:
    python tests/e2e/test_full_app.py
"""
import os
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5053")
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Track issues found during tests
issues_found = []


def screenshot(page, name):
    """Save a screenshot with a descriptive name."""
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  📸 Screenshot: {path.name}")
    return path


def log_issue(severity, page_name, description):
    """Log an issue found during testing."""
    issues_found.append({
        "severity": severity,
        "page": page_name,
        "description": description,
    })
    icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "ℹ️"
    print(f"  {icon} [{severity}] {page_name}: {description}")


def check_console_errors(page, page_name):
    """Collect and report JS console errors."""
    errors = []

    def on_console(msg):
        if msg.type == "error":
            errors.append(msg.text)

    page.on("console", on_console)
    # Give time for any pending JS to execute
    page.wait_for_timeout(500)
    page.remove_listener("console", on_console)

    for err in errors:
        log_issue("WARNING", page_name, f"Console error: {err}")
    return errors


def authenticate(page):
    """Log in via the dev test-bypass endpoint."""
    print("\n🔐 Authenticating via dev test-bypass...")
    page.goto(f"{BASE_URL}/login/test-bypass")
    page.wait_for_load_state("networkidle")

    # Should redirect to dashboard
    if "/login" in page.url:
        log_issue("CRITICAL", "Auth", "Test bypass redirect failed - still on login page")
        # Try screenshot of login page
        screenshot(page, "00_auth_failed")
        return False

    print(f"  ✅ Authenticated – redirected to: {page.url}")
    screenshot(page, "00_auth_success")
    return True


def test_login_page(page):
    """Test the login page renders correctly."""
    print("\n📄 Testing: Login Page")
    page.goto(f"{BASE_URL}/logout")  # Logout first
    page.wait_for_load_state("networkidle")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")

    # Check page loaded
    assert "cGR8s" in page.content(), "Login page missing cGR8s branding"

    # Check form elements
    login_input = page.locator("#login_id")
    password_input = page.locator("#password")
    submit_btn = page.locator("#loginBtn")

    assert login_input.is_visible(), "Login ID input not visible"
    assert password_input.is_visible(), "Password input not visible"
    assert submit_btn.is_visible(), "Submit button not visible"

    screenshot(page, "01_login_page")

    # Check SSO link
    sso_link = page.locator("text=Sign in via Auth Portal")
    if sso_link.is_visible():
        print("  ✅ SSO link present")
    else:
        log_issue("WARNING", "Login", "SSO link not visible")

    print("  ✅ Login page renders correctly")

    # Re-authenticate for remaining tests
    authenticate(page)


def test_dashboard(page):
    """Test Dashboard page."""
    print("\n📄 Testing: Dashboard")
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle")

    # Check page title
    heading = page.locator("h2")
    assert heading.is_visible(), "Dashboard heading not visible"

    # Check KPI cards
    kpi_cards = page.locator(".kpi-card")
    kpi_count = kpi_cards.count()
    if kpi_count >= 4:
        print(f"  ✅ {kpi_count} KPI cards present")
    else:
        log_issue("WARNING", "Dashboard", f"Expected 4 KPI cards, found {kpi_count}")

    # Check Quick Actions
    quick_actions = page.locator("text=Quick Actions")
    if quick_actions.is_visible():
        print("  ✅ Quick Actions section present")
    else:
        log_issue("WARNING", "Dashboard", "Quick Actions section missing")

    # Check sidebar navigation
    sidebar = page.locator("#sidebar")
    assert sidebar.is_visible(), "Sidebar not visible"

    nav_links = page.locator(".sidebar-nav .nav-link")
    nav_count = nav_links.count()
    print(f"  ✅ Sidebar: {nav_count} navigation links")

    screenshot(page, "02_dashboard")

    # Check for console errors
    check_console_errors(page, "Dashboard")

    print("  ✅ Dashboard page OK")


def test_sidebar_navigation(page):
    """Test all sidebar navigation links work."""
    print("\n📄 Testing: Sidebar Navigation")

    nav_items = [
        ("Dashboard", "/", "dashboard"),
        ("Process Orders", "/process-orders", "process_orders"),
        ("Target Weight", "/target-weight", "target_weight"),
        ("NPL Calculation", "/npl", "npl"),
        ("QA Workflow", "/qa", "qa"),
        ("Optimizer", "/optimizer", "optimizer"),
        ("FG Codes", "/fg-codes", "fg_codes"),
        ("Master Data", "/master-data", "master_data"),
        ("Batch Processing", "/batch", "batch"),
        ("Reports", "/reports", "reports"),
        ("Admin", "/admin", "admin"),
    ]

    for label, url_path, page_name in nav_items:
        page.goto(f"{BASE_URL}{url_path}")
        page.wait_for_load_state("networkidle")

        # Check page loaded (not error page)
        status = page.evaluate("() => document.title")
        page_content = page.content()

        if "500" in status or "Internal Server Error" in page_content:
            log_issue("CRITICAL", page_name, f"500 Error on {url_path}")
            screenshot(page, f"03_nav_error_{page_name}")
        elif "404" in status or "Not Found" in page_content:
            log_issue("CRITICAL", page_name, f"404 Not Found on {url_path}")
            screenshot(page, f"03_nav_404_{page_name}")
        else:
            print(f"  ✅ {label} ({url_path}) - loaded OK")

        screenshot(page, f"03_nav_{page_name}")

    print("  ✅ All navigation links tested")


def test_fg_codes_page(page):
    """Test FG Codes main interface."""
    print("\n📄 Testing: FG Codes - Main Interface")
    page.goto(f"{BASE_URL}/fg-codes")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)  # Wait for any JS initialization

    # Collect JS console errors
    console_errors = []

    def capture_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    page.on("console", capture_console)

    # Check panels exist
    panels = page.locator(".fg-panel")
    panel_count = panels.count()
    print(f"  Panels found: {panel_count}")

    if panel_count < 4:
        log_issue("WARNING", "FG Codes", f"Expected 4 panels, found {panel_count}")

    # Check panel headers
    headers = page.locator(".fg-panel-header")
    for i in range(headers.count()):
        header_text = headers.nth(i).inner_text()
        print(f"  📋 Panel header: {header_text}")

    screenshot(page, "04_fg_codes_initial")

    # Test Load button
    load_btn = page.locator("#loadBtn")
    if load_btn.is_visible():
        print("  ✅ Load button visible")

        # Check if limit input has correct default
        limit_input = page.locator("#loadLimit")
        limit_val = limit_input.input_value()
        print(f"  📋 Default load limit: {limit_val}")

        # Click Load
        load_btn.click()
        page.wait_for_timeout(3000)  # Wait for AJAX

        screenshot(page, "04_fg_codes_after_load")

        # Check if FG codes were loaded
        fg_items = page.locator(".fg-item")
        fg_count = fg_items.count()

        if fg_count > 0:
            print(f"  ✅ Loaded {fg_count} FG codes")

            # Click on first FG code
            fg_items.first.click()
            page.wait_for_timeout(2000)  # Wait for SKU details AJAX

            screenshot(page, "04_fg_codes_selected")

            # Check if SKU details populated
            sku_content = page.locator("#skuDetailsContent")
            if sku_content.is_visible():
                sku_text = sku_content.inner_text()
                if "Select an FG Code" in sku_text:
                    log_issue("WARNING", "FG Codes", "SKU details didn't populate after selection")
                else:
                    print("  ✅ SKU Details populated")

                    # Test tab switching
                    tabs = page.locator(".detail-tab")
                    for i in range(tabs.count()):
                        tab = tabs.nth(i)
                        tab_text = tab.inner_text()
                        tab.click()
                        page.wait_for_timeout(300)
                        print(f"    Tab: {tab_text}")
                    screenshot(page, "04_fg_codes_tabs")
        else:
            log_issue("WARNING", "FG Codes", "No FG codes loaded - might be empty DB or JS error")

            # Check for JS errors
            if console_errors:
                for err in console_errors:
                    log_issue("CRITICAL", "FG Codes", f"JS Error: {err}")
    else:
        log_issue("CRITICAL", "FG Codes", "Load button not visible")

    # Test Load All button
    load_all_btn = page.locator("#loadAllBtn")
    if load_all_btn.is_visible():
        print("  ✅ Load All button visible")
    else:
        log_issue("WARNING", "FG Codes", "Load All button not visible")

    # Test Key Variables inputs
    key_var_inputs = ["n_bld", "p_cu", "t_vnt", "f_pd", "m_ip"]
    for var_id in key_var_inputs:
        input_el = page.locator(f"#{var_id}")
        if input_el.is_visible():
            # Input test values
            input_el.fill("1.500")
            print(f"  ✅ Input {var_id}: filled with 1.500")
        else:
            log_issue("WARNING", "FG Codes", f"Key variable input #{var_id} not visible")

    screenshot(page, "04_fg_codes_variables_filled")

    # Test Calculate button
    calc_btn = page.locator("#calculateBtn")
    if calc_btn.is_visible():
        is_disabled = calc_btn.is_disabled()
        print(f"  Calculate button disabled: {is_disabled}")

        if not is_disabled:
            calc_btn.click()
            page.wait_for_timeout(3000)  # Wait for calculation AJAX
            screenshot(page, "04_fg_codes_calculated")

            # Check results
            results = page.locator("#resultsContent")
            results_text = results.inner_text()
            if "Run calculation" in results_text:
                log_issue("WARNING", "FG Codes", "Calculation didn't produce results")
            else:
                print("  ✅ Calculation completed")

                # Check for result values
                result_values = page.locator(".result-value")
                for i in range(result_values.count()):
                    val = result_values.nth(i).inner_text()
                    print(f"    Result value: {val}")
        else:
            log_issue("INFO", "FG Codes", "Calculate button disabled (no FG code selected)")
    else:
        log_issue("CRITICAL", "FG Codes", "Calculate button not visible")

    # Test NPL and Optimizer buttons
    npl_btn = page.locator("#nplBtn")
    opt_btn = page.locator("#optimizerBtn")

    if npl_btn.is_visible():
        print("  ✅ NPL button visible")
    else:
        log_issue("WARNING", "FG Codes", "NPL button not visible")

    if opt_btn.is_visible():
        print("  ✅ Optimizer button visible")
    else:
        log_issue("WARNING", "FG Codes", "Optimizer button not visible")

    # Report all JS errors
    page.remove_listener("console", capture_console)
    if console_errors:
        for err in console_errors:
            log_issue("CRITICAL", "FG Codes", f"Console error: {err}")

    screenshot(page, "04_fg_codes_final")
    print("  ✅ FG Codes page test complete")


def test_fg_codes_create(page):
    """Test FG Codes create form."""
    print("\n📄 Testing: FG Codes - Create Form")
    page.goto(f"{BASE_URL}/fg-codes/create")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "500" in page.evaluate("() => document.title") or "Internal Server Error" in content:
        log_issue("CRITICAL", "FG Codes Create", "500 error on create page")
        screenshot(page, "05_fg_create_error")
        return

    screenshot(page, "05_fg_create_form")

    # Check form fields
    fg_code_input = page.locator("input[name='fg_code']")
    if fg_code_input.is_visible():
        print("  ✅ FG Code input present")
    else:
        log_issue("WARNING", "FG Codes Create", "FG Code input not found")

    print("  ✅ FG Codes create page OK")


def test_process_orders(page):
    """Test Process Orders page."""
    print("\n📄 Testing: Process Orders")
    page.goto(f"{BASE_URL}/process-orders")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "Process Orders", "500 error")
        screenshot(page, "06_po_error")
        return

    # Check table
    table = page.locator("table")
    if table.is_visible():
        print("  ✅ Process Orders table visible")
    else:
        print("  ℹ️  No table (might be empty state)")

    # Check New Process Order button
    new_btn = page.locator("text=New Process Order")
    if new_btn.is_visible():
        print("  ✅ New Process Order button present")
    else:
        log_issue("WARNING", "Process Orders", "New Process Order button missing")

    screenshot(page, "06_process_orders")

    # Test create form
    page.goto(f"{BASE_URL}/process-orders/create")
    page.wait_for_load_state("networkidle")
    screenshot(page, "06_po_create_form")
    print("  ✅ Process Orders pages OK")


def test_target_weight(page):
    """Test Target Weight page."""
    print("\n📄 Testing: Target Weight")
    page.goto(f"{BASE_URL}/target-weight")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "Target Weight", "500 error")
        screenshot(page, "07_tw_error")
        return

    screenshot(page, "07_target_weight")
    print("  ✅ Target Weight page OK")


def test_npl(page):
    """Test NPL Calculation page."""
    print("\n📄 Testing: NPL Calculation")
    page.goto(f"{BASE_URL}/npl")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "NPL", "500 error")
        screenshot(page, "08_npl_error")
        return

    # Check for table or empty state
    screenshot(page, "08_npl")
    print("  ✅ NPL page OK")


def test_qa(page):
    """Test QA Workflow page."""
    print("\n📄 Testing: QA Workflow")
    page.goto(f"{BASE_URL}/qa")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "QA", "500 error")
        screenshot(page, "09_qa_error")
        return

    screenshot(page, "09_qa")

    # Test pending page
    page.goto(f"{BASE_URL}/qa/pending")
    page.wait_for_load_state("networkidle")
    screenshot(page, "09_qa_pending")
    print("  ✅ QA pages OK")


def test_optimizer(page):
    """Test Optimizer page."""
    print("\n📄 Testing: Optimizer")
    page.goto(f"{BASE_URL}/optimizer")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "Optimizer", "500 error")
        screenshot(page, "10_optimizer_error")
        return

    screenshot(page, "10_optimizer")
    print("  ✅ Optimizer page OK")


def test_master_data(page):
    """Test Master Data pages."""
    print("\n📄 Testing: Master Data")

    sub_pages = [
        ("/master-data/blends", "blends"),
        ("/master-data/physical-params", "physical_params"),
        ("/master-data/calibration", "calibration"),
    ]

    for url_path, name in sub_pages:
        page.goto(f"{BASE_URL}{url_path}")
        page.wait_for_load_state("networkidle")

        content = page.content()
        if "Internal Server Error" in content:
            log_issue("CRITICAL", f"Master Data ({name})", "500 error")
            screenshot(page, f"11_master_{name}_error")
        else:
            screenshot(page, f"11_master_{name}")
            print(f"  ✅ Master Data - {name} OK")


def test_batch(page):
    """Test Batch Processing page."""
    print("\n📄 Testing: Batch Processing")
    page.goto(f"{BASE_URL}/batch")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "Batch", "500 error")
        screenshot(page, "12_batch_error")
        return

    screenshot(page, "12_batch")

    # Test submit page
    page.goto(f"{BASE_URL}/batch/submit")
    page.wait_for_load_state("networkidle")
    screenshot(page, "12_batch_submit")
    print("  ✅ Batch pages OK")


def test_reports(page):
    """Test Reports page."""
    print("\n📄 Testing: Reports")
    page.goto(f"{BASE_URL}/reports")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "Reports", "500 error")
        screenshot(page, "13_reports_error")
        return

    screenshot(page, "13_reports")

    # Test generate page
    page.goto(f"{BASE_URL}/reports/generate")
    page.wait_for_load_state("networkidle")
    screenshot(page, "13_reports_generate")
    print("  ✅ Reports pages OK")


def test_product_dev(page):
    """Test Product Development page."""
    print("\n📄 Testing: Product Development")
    page.goto(f"{BASE_URL}/product-dev")
    page.wait_for_load_state("networkidle")

    content = page.content()
    if "Internal Server Error" in content:
        log_issue("CRITICAL", "Product Dev", "500 error")
        screenshot(page, "14_product_dev_error")
        return

    screenshot(page, "14_product_dev")
    print("  ✅ Product Dev page OK")


def test_admin(page):
    """Test Admin pages."""
    print("\n📄 Testing: Admin")

    sub_pages = [
        ("/admin", "admin_index"),
        ("/admin/system-config", "system_config"),
        ("/admin/audit-trail", "audit_trail"),
    ]

    for url_path, name in sub_pages:
        page.goto(f"{BASE_URL}{url_path}")
        page.wait_for_load_state("networkidle")

        content = page.content()
        if "Internal Server Error" in content:
            log_issue("CRITICAL", f"Admin ({name})", "500 error")
            screenshot(page, f"15_admin_{name}_error")
        else:
            screenshot(page, f"15_admin_{name}")
            print(f"  ✅ Admin - {name} OK")


def test_responsive(page):
    """Test responsive behavior at different viewport sizes."""
    print("\n📄 Testing: Responsive Design")

    viewports = [
        (1920, 1080, "desktop_full"),
        (1366, 768, "desktop_laptop"),
        (768, 1024, "tablet"),
        (375, 812, "mobile"),
    ]

    for width, height, label in viewports:
        page.set_viewport_size({"width": width, "height": height})
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")
        screenshot(page, f"16_responsive_{label}")
        print(f"  ✅ Viewport {width}x{height} ({label})")

    # Reset to desktop
    page.set_viewport_size({"width": 1920, "height": 1080})


def test_error_pages(page):
    """Test error handling for 404."""
    print("\n📄 Testing: Error Pages")
    page.goto(f"{BASE_URL}/nonexistent-page-12345")
    page.wait_for_load_state("networkidle")
    screenshot(page, "17_error_404")

    content = page.content()
    if "404" in content or "Not Found" in content:
        print("  ✅ 404 error page renders properly")
    else:
        log_issue("WARNING", "Error Pages", "404 page doesn't show proper error message")


def run_all_tests():
    """Run the complete test suite."""
    print("=" * 60)
    print("🧪 cGR8s – Comprehensive Playwright E2E Test Suite")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Screenshots: {SCREENSHOTS_DIR}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = context.new_page()

        # Collect all console errors globally
        all_console_errors = []

        def on_global_console(msg):
            if msg.type == "error":
                all_console_errors.append({"url": page.url, "error": msg.text})

        page.on("console", on_global_console)

        try:
            # Step 1: Authenticate
            if not authenticate(page):
                print("\n❌ Authentication failed. Cannot proceed with tests.")
                screenshot(page, "FATAL_auth_failed")
                browser.close()
                return

            # Step 2: Test login page
            test_login_page(page)

            # Step 3: Test Dashboard
            test_dashboard(page)

            # Step 4: Test Sidebar Navigation (visits each page)
            test_sidebar_navigation(page)

            # Step 5: Test FG Codes in depth
            test_fg_codes_page(page)
            test_fg_codes_create(page)

            # Step 6: Test Process Orders
            test_process_orders(page)

            # Step 7: Test Target Weight
            test_target_weight(page)

            # Step 8: Test NPL
            test_npl(page)

            # Step 9: Test QA
            test_qa(page)

            # Step 10: Test Optimizer
            test_optimizer(page)

            # Step 11: Test Master Data
            test_master_data(page)

            # Step 12: Test Batch
            test_batch(page)

            # Step 13: Test Reports
            test_reports(page)

            # Step 14: Test Product Dev
            test_product_dev(page)

            # Step 15: Test Admin
            test_admin(page)

            # Step 16: Test Responsive
            test_responsive(page)

            # Step 17: Test Error Pages
            test_error_pages(page)

        except Exception as e:
            print(f"\n❌ Test FAILED with exception: {e}")
            screenshot(page, "FATAL_exception")
            log_issue("CRITICAL", "Test Runner", str(e))
        finally:
            page.remove_listener("console", on_global_console)

        # Collect global console errors as issues
        for err_info in all_console_errors:
            log_issue("WARNING", "Console", f"[{err_info['url']}] {err_info['error']}")

        browser.close()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    screenshots = list(SCREENSHOTS_DIR.glob("*.png"))
    print(f"\n📸 Screenshots captured: {len(screenshots)}")

    if issues_found:
        print(f"\n⚠️  Issues found: {len(issues_found)}")

        critical = [i for i in issues_found if i["severity"] == "CRITICAL"]
        warnings = [i for i in issues_found if i["severity"] == "WARNING"]
        info = [i for i in issues_found if i["severity"] == "INFO"]

        if critical:
            print(f"\n🔴 CRITICAL ({len(critical)}):")
            for issue in critical:
                print(f"   - [{issue['page']}] {issue['description']}")

        if warnings:
            print(f"\n🟡 WARNINGS ({len(warnings)}):")
            for issue in warnings:
                print(f"   - [{issue['page']}] {issue['description']}")

        if info:
            print(f"\nℹ️  INFO ({len(info)}):")
            for issue in info:
                print(f"   - [{issue['page']}] {issue['description']}")

        # Save issues report
        report_path = SCREENSHOTS_DIR / "test_report.json"
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "base_url": BASE_URL,
                "total_issues": len(issues_found),
                "critical": len(critical),
                "warnings": len(warnings),
                "info": len(info),
                "issues": issues_found,
                "screenshots": [s.name for s in screenshots],
            }, f, indent=2)
        print(f"\n📋 Report saved: {report_path}")
    else:
        print("\n✅ No issues found!")

    print("\n" + "=" * 60)
    return issues_found


if __name__ == "__main__":
    issues = run_all_tests()
    sys.exit(1 if any(i["severity"] == "CRITICAL" for i in issues) else 0)
