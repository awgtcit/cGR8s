"""Phase 3 Forms Redesign - Playwright Verification Test.
Tests: form_actions macro, form_section styling, form field transitions, validation styles.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "phase3")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


# Forms to check for form-actions macro
FORM_PAGES = [
    ("/master-data/blends/create", "Blend Create"),
    ("/master-data/machines/create", "Machine Create"),
    ("/master-data/skus/create", "SKU Create"),
    ("/master-data/lookups/create", "Lookup Create"),
    ("/master-data/calibration/create", "Calibration Create"),
    ("/master-data/physical-params/create", "Phys Param Create"),
    ("/process-orders/create", "Process Order Create"),
    ("/fg-codes/create", "FG Code Create"),
    ("/batch/submit", "Batch Submit"),
    ("/reports/generate", "Reports Generate"),
]


def main():
    errors = []
    warnings = []
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

        # ── Check Form Actions on Create Forms ────────────────
        print("\n2. Checking form-actions on create forms...")
        forms_checked = 0
        for path, name in FORM_PAGES:
            page.goto(f"{BASE_URL}{path}")
            page.wait_for_load_state("networkidle")

            if page.locator(".form-actions").count() > 0:
                # Check it has Cancel and Submit buttons
                cancel = page.locator(".form-actions a.btn-secondary")
                submit = page.locator(".form-actions button.btn-primary")
                if cancel.count() > 0 and submit.count() > 0:
                    print(f"   ✅ {name} - form-actions with Cancel + Submit")
                    forms_checked += 1
                else:
                    errors.append(f"FAIL: {name} - form-actions missing Cancel or Submit")
            else:
                errors.append(f"FAIL: {name} ({path}) - No .form-actions found")

        shot(page, "01_form_actions")
        print(f"   Checked {forms_checked}/{len(FORM_PAGES)} forms")

        # ── Check Form Section on Physical Params ─────────────
        print("\n3. Checking form-section on Physical Params...")
        page.goto(f"{BASE_URL}/master-data/physical-params/create")
        page.wait_for_load_state("networkidle")

        sections = page.locator(".form-section")
        section_count = sections.count()
        if section_count >= 3:
            print(f"   ✅ Found {section_count} form sections")
        else:
            errors.append(f"FAIL: Physical Params - Expected 3+ form sections, got {section_count}")

        titles = page.locator(".form-section-title")
        if titles.count() >= 3:
            for i in range(min(titles.count(), 5)):
                print(f"   ✅ Section: {titles.nth(i).text_content().strip()}")
        else:
            errors.append(f"FAIL: Physical Params - Expected 3+ section titles, got {titles.count()}")

        shot(page, "02_form_sections_phys_params")

        # ── Check Form Section on FG Codes Form ──────────────
        print("\n4. Checking form-section on FG Codes form...")
        page.goto(f"{BASE_URL}/fg-codes/create")
        page.wait_for_load_state("networkidle")

        sections = page.locator(".form-section")
        if sections.count() >= 2:
            print(f"   ✅ FG Codes form has {sections.count()} sections")
        else:
            errors.append(f"FAIL: FG Codes form - Expected 2+ sections, got {sections.count()}")

        shot(page, "03_form_sections_fg_codes")

        # ── Check Form Section on System Config ───────────────
        print("\n5. Checking form-section on System Config...")
        page.goto(f"{BASE_URL}/admin/system-config")
        page.wait_for_load_state("networkidle")

        sections = page.locator(".form-section")
        if sections.count() >= 3:
            print(f"   ✅ System Config has {sections.count()} sections")
        else:
            errors.append(f"FAIL: System Config - Expected 3+ sections, got {sections.count()}")

        shot(page, "04_system_config")

        # ── Check Form Control Focus Styling ──────────────────
        print("\n6. Checking form-control focus styling...")
        page.goto(f"{BASE_URL}/master-data/blends/create")
        page.wait_for_load_state("networkidle")

        input_el = page.locator("input.form-control").first
        if input_el.count() > 0:
            # Focus the input
            input_el.click()

            # Check border-color changes
            border_color = page.evaluate("""() => {
                const el = document.querySelector('input.form-control:focus');
                return el ? getComputedStyle(el).borderColor : 'none';
            }""")
            transition = page.evaluate("""() => {
                const el = document.querySelector('input.form-control');
                return el ? getComputedStyle(el).transition : 'none';
            }""")

            if transition and ("border" in transition or "all" in transition):
                print(f"   ✅ Input transition active: {transition[:60]}")
            else:
                warnings.append(f"WARN: Input transition: {transition}")

            print(f"   ✅ Focus border-color: {border_color}")
        else:
            warnings.append("WARN: No form-control inputs found on blend create")

        shot(page, "05_form_focus")

        # ── Check Form Label Styling ──────────────────────────
        print("\n7. Checking form-label styling...")
        label = page.locator(".form-label").first
        if label.count() > 0:
            font_weight = page.evaluate("""() => {
                const el = document.querySelector('.form-label');
                return getComputedStyle(el).fontWeight;
            }""")
            font_size = page.evaluate("""() => {
                const el = document.querySelector('.form-label');
                return getComputedStyle(el).fontSize;
            }""")
            if int(font_weight) >= 500:
                print(f"   ✅ Label weight: {font_weight}, size: {font_size}")
            else:
                warnings.append(f"WARN: Label weight only {font_weight}")
        else:
            warnings.append("WARN: No .form-label found")

        # ── Check Checkbox Styling ────────────────────────────
        print("\n8. Checking checkbox styling...")
        page.goto(f"{BASE_URL}/master-data/blends/create")
        page.wait_for_load_state("networkidle")

        checkbox = page.locator(".form-check-input")
        if checkbox.count() > 0:
            print(f"   ✅ Checkbox present ({checkbox.count()} found)")
        else:
            print("   ℹ️ No checkboxes on this form")

        shot(page, "06_form_complete")

        # ── Check Card Max-Width on Forms ─────────────────────
        print("\n9. Checking card max-width constraint on forms...")
        card = page.locator(".card")
        if card.count() > 0:
            max_width = page.evaluate("""() => {
                const el = document.querySelector('.card');
                return getComputedStyle(el).maxWidth;
            }""")
            if max_width and max_width != "none":
                print(f"   ✅ Card max-width: {max_width}")
            else:
                print(f"   ℹ️ Card max-width: {max_width} (full width)")
        else:
            errors.append("FAIL: No .card on blend create page")

        # ── Required Field Asterisks ──────────────────────────
        print("\n10. Checking required field asterisks...")
        asterisks = page.locator(".form-label .text-danger")
        if asterisks.count() > 0:
            print(f"   ✅ Found {asterisks.count()} required field markers")
        else:
            warnings.append("WARN: No required field asterisks found")

        shot(page, "07_required_fields")

        # ── Summary ───────────────────────────────────────────
        print("\n" + "=" * 60)
        print("PHASE 3 RESULTS")
        print("=" * 60)

        if console_errors:
            print(f"\n⚠️  Console errors ({len(console_errors)}):")
            for e in console_errors[:5]:
                print(f"   {e[:100]}")

        if network_errors:
            print(f"\n⚠️  Network errors ({len(network_errors)}):")
            for e in network_errors[:5]:
                print(f"   {e[:100]}")

        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for w in warnings:
                print(f"   {w}")

        if errors:
            print(f"\n❌ FAILURES ({len(errors)}):")
            for e in errors:
                print(f"   {e}")
            browser.close()
            sys.exit(1)
        else:
            print("\n✅ ALL PHASE 3 CHECKS PASSED!")
            browser.close()
            sys.exit(0)


if __name__ == "__main__":
    main()
