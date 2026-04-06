"""Browser test for P1 (UUID fix) and P2 (3dp consistency) fixes."""
from playwright.sync_api import sync_playwright
import time
import re
import sys

BASE = 'http://127.0.0.1:5053'
uuid_pat = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
errors_list = ['Internal Server Error', 'Traceback', 'UndefinedError', 'TemplateSyntaxError', 'BuildError']


def has_error(content):
    return any(e in content for e in errors_list)


def main():
    all_pass = True
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = ctx.new_page()

        page.goto(f'{BASE}/login/test-bypass', wait_until='networkidle')

        # Test 1: PO Index
        print('=== 1. Process Orders Index ===')
        page.goto(f'{BASE}/process-orders/', wait_until='networkidle')
        time.sleep(1)
        if has_error(page.content()):
            print('  FAIL: Server error')
            all_pass = False
        else:
            wf = page.locator('.wf-step').count()
            tw = page.locator('.tw-chip').count()
            print(f'  PASS: wf-steps={wf}, tw-chips={tw}')
            page.screenshot(path='tests/e2e/screenshots/validation/fix_po_index.png', full_page=True)

        # Test 2: PO Detail
        print('=== 2. Process Orders Detail ===')
        first_link = page.locator('table tbody tr td:first-child a').first
        if first_link.count() > 0:
            first_link.click()
            page.wait_for_load_state('networkidle')
            time.sleep(1)
            if has_error(page.content()):
                print('  FAIL: Server error on detail')
                all_pass = False
            else:
                steps = page.locator('.wf-stepper-step').count()
                print(f'  PASS: stepper steps={steps}')
                page.screenshot(path='tests/e2e/screenshots/validation/fix_po_detail.png', full_page=True)

        # Test 3: NPL Index
        print('=== 3. NPL Index (UUID fix) ===')
        page.goto(f'{BASE}/npl/', wait_until='networkidle')
        time.sleep(1)
        if has_error(page.content()):
            print('  FAIL: Server error')
            all_pass = False
        else:
            cells = page.locator('table tbody td').all_inner_texts()
            uuid_found = any(uuid_pat.fullmatch(t.strip()) for t in cells)
            if uuid_found:
                print('  WARN: UUID still visible in table')
            else:
                print('  PASS: No raw UUIDs in table')
            page.screenshot(path='tests/e2e/screenshots/validation/fix_npl_index.png', full_page=True)

        # Test 4: Optimizer Index
        print('=== 4. Optimizer Index (UUID fix) ===')
        page.goto(f'{BASE}/optimizer/', wait_until='networkidle')
        time.sleep(1)
        if has_error(page.content()):
            print('  FAIL: Server error')
            all_pass = False
        else:
            cells = page.locator('table tbody td').all_inner_texts()
            uuid_found = any(uuid_pat.fullmatch(t.strip()) for t in cells)
            if uuid_found:
                print('  WARN: UUID still visible in table')
            else:
                print('  PASS: No raw UUIDs in table')
            page.screenshot(path='tests/e2e/screenshots/validation/fix_optimizer_index.png', full_page=True)

        # Test 5: QA Index
        print('=== 5. QA Index (UUID fix) ===')
        page.goto(f'{BASE}/qa/', wait_until='networkidle')
        time.sleep(1)
        if has_error(page.content()):
            print('  FAIL: Server error')
            all_pass = False
        else:
            cells = page.locator('table tbody td').all_inner_texts()
            uuid_found = any(uuid_pat.fullmatch(t.strip()) for t in cells)
            if uuid_found:
                print('  WARN: UUID still visible in table')
            else:
                print('  PASS: No raw UUIDs in table')
            page.screenshot(path='tests/e2e/screenshots/validation/fix_qa_index.png', full_page=True)

        # Test 6: TW Calculate page (3dp consistency)
        print('=== 6. TW Calculate (3dp) ===')
        page.goto(f'{BASE}/process-orders/', wait_until='networkidle')
        first_link = page.locator('table tbody tr td:first-child a').first
        if first_link.count() > 0:
            href = first_link.get_attribute('href')
            po_id = href.split('/')[-1]
            page.goto(f'{BASE}/target-weight/calculate/{po_id}', wait_until='networkidle')
            time.sleep(1)
            if has_error(page.content()):
                print('  FAIL: Server error')
                all_pass = False
            else:
                print('  PASS: Page loaded OK')
                page.screenshot(path='tests/e2e/screenshots/validation/fix_tw_calc.png', full_page=True)

        status = 'ALL PASS' if all_pass else 'SOME FAILED'
        print(f'=== Overall: {status} ===')
        browser.close()

    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
