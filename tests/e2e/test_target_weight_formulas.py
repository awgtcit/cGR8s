"""
Target Weight Formulas – Playwright E2E Test (headed Chrome)
Tests:
  1. Login via test-bypass
  2. Navigate to Target Weight index page
  3. Screenshot index page
  4. Navigate to calculate page (first PO if available)
  5. Screenshot calculate page: verify 3-column layout, FG Info, Constants, Key Variables form, Last Calc
  6. Verify form fields render without errors
  7. Attempt a POST calculation (fill key variables, submit)
  8. Screenshot result page: verify interim results, output weights, input snapshot
  9. Check for console errors / 500 pages
"""

from playwright.sync_api import sync_playwright
import json
import time
import sys
import os

BASE = "http://127.0.0.1:5053"
SHOTS = os.path.join(os.path.dirname(__file__), "screenshots", "target_weight_formulas")
os.makedirs(SHOTS, exist_ok=True)

passed = 0
failed = 0
warnings = []


def check(label, ok):
    global passed, failed
    if ok:
        print(f"   \u2705 {label}")
        passed += 1
    else:
        print(f"   \u274c {label}")
        failed += 1


def warn(msg):
    global warnings
    warnings.append(msg)


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, channel="chrome")
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    console_errors = []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

    # ── 1. Login ──────────────────────────────────────────
    print("1. Logging in...")
    page.goto(f"{BASE}/login/test-bypass", wait_until="networkidle")
    check("Login OK", "/login" not in page.url)
    page.screenshot(path=os.path.join(SHOTS, "01_login.png"), full_page=True)

    # ── 2. Target Weight Index page ───────────────────────
    print("\n2. Target Weight index page...")
    page.goto(f"{BASE}/target-weight/", wait_until="networkidle")
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOTS, "02_tw_index.png"), full_page=True)

    tw_title = page.title()
    check("Index page loaded (title not empty)", tw_title != "")
    check("No 500 error on index", "Internal Server Error" not in page.content())

    # Check if there are any process orders listed
    rows = page.locator("table tbody tr")
    row_count = rows.count()
    print(f"   Found {row_count} process order row(s)")

    has_po = row_count > 0 and "No process orders" not in page.content()

    if not has_po:
        # Create a PO via the FG Codes API
        print("   No process orders – creating one via API...")

        # First, find a valid FG code
        resp = page.request.get(f"{BASE}/fg-codes/api/load-codes?page=1&per_page=1")
        fg_data = resp.json()
        fg_codes = fg_data.get('data', fg_data.get('codes', []))
        if not fg_codes:
            warn("No FG codes in database – cannot create PO")
            print("   \u26a0\ufe0f  No FG codes – cannot test calculate/result pages")
            browser.close()
            sys.exit(1)

        fg_code_val = fg_codes[0].get('fg_code', fg_codes[0].get('code', ''))
        print(f"   Using FG code: {fg_code_val}")

        import uuid
        po_number = f"PO-TEST-{uuid.uuid4().hex[:8].upper()}"

        # Get CSRF token from a page
        csrf_token = page.evaluate("() => { const el = document.querySelector('meta[name=csrf-token]'); return el ? el.content : ''; }")
        if not csrf_token:
            # Try from cookie
            cookies = ctx.cookies()
            csrf_token = next((c['value'] for c in cookies if 'csrf' in c['name'].lower()), '')

        headers = {"Content-Type": "application/json"}
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token

        create_resp = page.request.post(f"{BASE}/fg-codes/api/process-order/create", data=json.dumps({
            "fg_code": fg_code_val,
            "process_date": "2026-03-31T10:00:00",
            "process_order_id": po_number,
        }), headers=headers)

        print(f"   Create PO status: {create_resp.status}")
        if create_resp.status != 200:
            body_text = create_resp.text()
            print(f"   Create PO error response (first 500 chars): {body_text[:500]}")
            check("PO created via API", False)
        else:
            create_data = create_resp.json()
            print(f"   Create PO response: {create_data}")
            check("PO created via API", create_data.get('success'))
            po_id = create_data.get('process_order_id')

        # Reload index to see the new PO
        page.goto(f"{BASE}/target-weight/", wait_until="networkidle")
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(SHOTS, "02b_tw_index_with_po.png"), full_page=True)

    # ── 3. Navigate to first PO's calculate page ──────
    print("\n3. Navigate to Calculate page for first PO...")
    calc_link = page.locator("a:has-text('Calculate')").first

    if calc_link.count() > 0:
        calc_link.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(SHOTS, "03_tw_calculate.png"), full_page=True)

        check("Calculate page loaded", "Internal Server Error" not in page.content())
        check("Calculate page has form", page.locator("form").count() > 0)

        # ── 4. Verify 3-column layout ─────────────────
        print("\n4. Checking 3-column layout...")
        fg_info_card = page.locator("text=FG Code Info")
        constants_card = page.locator("text=Constants")
        kv_card = page.locator("text=Key Variables")
        last_calc_card = page.locator("text=Last Calculation")

        check("FG Code Info card exists", fg_info_card.count() > 0)
        check("Constants card exists", constants_card.count() > 0)
        check("Key Variables card exists", kv_card.count() > 0)
        check("Last Calculation card exists", last_calc_card.count() > 0)

        # ── 5. Verify form fields ─────────────────────
        print("\n5. Checking form fields...")
        check("N_BLD field exists", page.locator("input[name='n_bld']").count() > 0)
        check("P_CU field exists", page.locator("input[name='p_cu']").count() > 0)
        check("T_VNT field exists", page.locator("input[name='t_vnt']").count() > 0)
        check("F_PD field exists", page.locator("input[name='f_pd']").count() > 0)
        check("M_IP field exists", page.locator("input[name='m_ip']").count() > 0)

        # Check hidden calibration fields
        check("Hidden alpha field", page.locator("input[name='alpha']").count() > 0)
        check("Hidden beta field", page.locator("input[name='beta']").count() > 0)
        check("Hidden gamma field", page.locator("input[name='gamma']").count() > 0)
        check("Hidden delta field", page.locator("input[name='delta']").count() > 0)
        check("Hidden n_tgt field", page.locator("input[name='n_tgt']").count() > 0)

        # ── 6. Fill and submit form ───────────────────
        print("\n6. Filling key variables and submitting...")
        n_bld_input = page.locator("input[name='n_bld']")
        p_cu_input = page.locator("input[name='p_cu']")
        t_vnt_input = page.locator("input[name='t_vnt']")
        f_pd_input = page.locator("input[name='f_pd']")
        m_ip_input = page.locator("input[name='m_ip']")

        # Clear and fill with test values
        n_bld_input.fill("1.85")
        p_cu_input.fill("50")
        t_vnt_input.fill("25")
        f_pd_input.fill("350")
        m_ip_input.fill("12.5")

        page.screenshot(path=os.path.join(SHOTS, "04_tw_form_filled.png"), full_page=True)

        # Submit
        page.locator("button:has-text('Calculate'), input[type='submit']").first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SHOTS, "05_tw_result.png"), full_page=True)

        page_content = page.content()
        has_500 = "Internal Server Error" in page_content
        has_traceback = "Traceback" in page_content
        has_jinja_error = "UndefinedError" in page_content or "TemplateSyntaxError" in page_content

        check("No 500 error on submit", not has_500)
        check("No Python traceback on submit", not has_traceback)
        check("No Jinja template error", not has_jinja_error)

        if has_500 or has_traceback or has_jinja_error:
            # Save error page full content
            page.screenshot(path=os.path.join(SHOTS, "05_tw_error.png"), full_page=True)
            error_text = page.inner_text("body")
            print(f"\n   ERROR PAGE CONTENT (first 2000 chars):\n{error_text[:2000]}")
        else:
            # ── 7. Verify result page content ─────────
            print("\n7. Verifying result page content...")

            # KPI cards
            check("TW KPI card visible", page.locator("text=Target Weight (TW)").count() > 0
                   or page.locator("text=Target Weight").count() > 0)
            check("W_cig KPI card visible", page.locator("text=Cigarette Weight").count() > 0)
            check("Total Dilution KPI visible", page.locator("text=Total Dilution").count() > 0)

            # Interim results
            check("Stage 1 Dilution row", page.locator("text=Stage 1 Dilution").count() > 0)
            check("Stage 2 Dilution row", page.locator("text=Stage 2 Dilution").count() > 0)
            check("Filtration % row", page.locator("text=Filtration").count() > 0)
            check("Nic Demand Total row", page.locator("text=Nic Demand").count() > 0)
            check("Total Nicotine row", page.locator("text=Total Nicotine").count() > 0)

            # Output weights
            check("W_dry row", page.locator("text=W_dry").count() > 0)
            check("W_tob row", page.locator("text=W_tob").count() > 0)
            check("W_NTM row", page.locator("text=W_NTM").count() > 0)
            check("W_cig row", page.locator("text=W_cig").count() > 0)

            # Input snapshot
            check("Input N_BLD shown", page.locator("text=N_BLD").count() > 0)
            check("Input P_CU shown", page.locator("text=P_CU").count() > 0)
            check("Calibration alpha shown", "α" in page_content or "Alpha" in page_content)
            check("Calibration N_tgt shown", "N_tgt" in page_content)

            page.screenshot(path=os.path.join(SHOTS, "06_tw_result_verified.png"), full_page=True)
    else:
        warn("No Calculate link found on index page")
        print("   \u26a0\ufe0f  No Calculate link found")

    # ── 8. Console errors ─────────────────────────────────
    print("\n8. Checking console errors...")
    if console_errors:
        print(f"   Console errors ({len(console_errors)}):")
        for err in console_errors[:5]:
            print(f"      - {err[:120]}")
    check("No critical console errors", len(console_errors) == 0)

    # ── Summary ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"TARGET WEIGHT FORMULAS E2E: {passed} passed, {failed} failed")
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  \u26a0\ufe0f  {w}")
    print("=" * 60)

    browser.close()

if failed > 0:
    sys.exit(1)
