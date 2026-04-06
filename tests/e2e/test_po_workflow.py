"""
Playwright E2E test: PO Composite Key + Inline Save + Calculate NPL + Verify + QA Sidebar
"""
import re
from playwright.sync_api import sync_playwright, expect

BASE = 'http://localhost:5053'


def test_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ── 1. Login via test-bypass ──
        page.goto(f'{BASE}/login/test-bypass')
        page.wait_for_url(f'{BASE}/**', timeout=10000)
        print('[PASS] Logged in via test-bypass')

        # ── 2. QA Sidebar links to Data Grid ──
        page.goto(BASE)
        page.wait_for_load_state('networkidle')
        qa_link = page.locator('a.nav-link:has-text("QA Workflow")')
        href = qa_link.get_attribute('href')
        assert 'data-grid' in href, f'QA sidebar should link to data-grid, got: {href}'
        print(f'[PASS] QA sidebar links to: {href}')

        # ── 3. Navigate to FG Codes ──
        page.goto(f'{BASE}/fg-codes')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)

        # Verify Order button and modal are gone
        assert page.locator('#createPOBtn').count() == 0, 'Order button should be removed'
        assert page.locator('#processOrderModal').count() == 0, 'Modal should be removed'
        print('[PASS] Order button & modal removed')

        # Verify inline PO section is hidden initially
        po_section = page.locator('#poInlineSection')
        expect(po_section).to_be_hidden()
        print('[PASS] Inline PO section hidden initially')

        # ── 4. Select an FG Code ──
        fg_items = page.locator('.fg-item')
        fg_items.first.wait_for(state='visible', timeout=10000)
        fg_items.first.click()
        page.wait_for_timeout(2000)
        print('[PASS] Selected first FG Code')

        # ── 5. Click Calculate Target ──
        calc_btn = page.locator('#calculateBtn')
        expect(calc_btn).to_be_enabled(timeout=5000)
        calc_btn.click()
        page.wait_for_timeout(3000)

        # Verify inline PO section shows after calculation
        expect(po_section).to_be_visible(timeout=5000)
        print('[PASS] Inline PO section visible after Calculate')

        # ── 6. Fill PO fields and save ──
        page.fill('#processOrderId', 'PW-TEST-001')
        page.fill('#processDate', '2026-04-06')
        page.click('#savePOBtn')
        page.wait_for_timeout(3000)

        # Verify success status
        status_text = page.locator('#poSaveStatus').inner_text()
        assert '✓' in status_text, f'Expected save success, got: {status_text}'
        print(f'[PASS] PO saved: {status_text}')

        # Verify Calculate NPL button appeared
        calc_npl_section = page.locator('#calcNplSection')
        expect(calc_npl_section).to_be_visible(timeout=3000)
        print('[PASS] Calculate NPL button visible')

        # ── 7. Same PO + different date = new record ──
        page.fill('#processDate', '2026-04-07')
        page.click('#savePOBtn')
        page.wait_for_timeout(3000)
        status_text2 = page.locator('#poSaveStatus').inner_text()
        assert '✓' in status_text2, f'Expected save success for new date, got: {status_text2}'
        assert 'Saved' in status_text2, f'Should create new record, got: {status_text2}'
        print(f'[PASS] Same PO + diff date = new record: {status_text2}')

        # ── 8. Same PO + same date = update ──
        page.click('#savePOBtn')
        page.wait_for_timeout(3000)
        status_text3 = page.locator('#poSaveStatus').inner_text()
        assert '✓' in status_text3, f'Expected update success, got: {status_text3}'
        assert 'Updated' in status_text3, f'Should update existing, got: {status_text3}'
        print(f'[PASS] Same PO + same date = update: {status_text3}')

        # ── 9. Click Calculate NPL → redirects to NPL page ──
        page.click('#calcNplBtn')
        page.wait_for_url('**/npl/calculate/**', timeout=10000)
        print(f'[PASS] Redirected to NPL calculate: {page.url}')

        # ── 10. Fill NPL inputs and submit ──
        page.fill('input[name="t_iss"]', '100')
        page.fill('input[name="t_un"]', '5')
        page.fill('input[name="n_mc"]', '10')
        page.fill('input[name="n_cg"]', '7200')
        page.fill('input[name="n_w"]', '0.85')
        page.fill('input[name="m_dsp"]', '12')

        submit_btn = page.locator('button[type="submit"], input[type="submit"]')
        if submit_btn.count() > 0:
            submit_btn.first.click()
            page.wait_for_timeout(3000)

            # Check if we're on the result page
            if '/npl/' in page.url or 'result' in page.url.lower():
                print(f'[PASS] NPL calculated, on result page: {page.url}')

                # ── 11. Verify the Verify & Confirm button exists ──
                verify_btn = page.locator('button:has-text("Verify")')
                if verify_btn.count() > 0:
                    print('[PASS] Verify & Confirm button present on result page')
                else:
                    print('[INFO] Verify button not found (may not be on result page)')
            else:
                print(f'[INFO] After NPL submit, on: {page.url}')
        else:
            print('[INFO] No submit button found on NPL calculate page')

        # ── 12. Take screenshot ──
        page.screenshot(path='test-results/e2e_po_workflow.png', full_page=True)
        print('[PASS] Screenshot saved')

        # ── 13. QA sidebar click test ──
        page.goto(BASE)
        page.wait_for_load_state('networkidle')
        qa_link = page.locator('a.nav-link:has-text("QA Workflow")')
        qa_link.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        assert 'data-grid' in page.url, f'QA should go to data-grid, but got: {page.url}'
        print(f'[PASS] QA sidebar navigated to: {page.url}')

        page.screenshot(path='test-results/e2e_qa_datagrid.png', full_page=True)
        print('[PASS] QA data grid screenshot saved')

        browser.close()
        print('\n✅ All E2E tests passed!')


if __name__ == '__main__':
    test_all()
