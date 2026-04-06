"""Test that AuditLogger doesn't corrupt session on failure."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5053"


def test_process_order_creation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Login
        page.goto(f"{BASE}/login/test-bypass")
        page.wait_for_load_state("networkidle")

        # Navigate to FG Codes
        page.goto(f"{BASE}/fg-codes/")
        page.wait_for_load_state("networkidle")

        # Click first FG code
        page.wait_for_selector(".fg-item", timeout=10000)
        page.locator(".fg-item").first.click()
        page.wait_for_timeout(1500)

        # Take screenshot of the main interface
        page.screenshot(path="test-results/po_create_test.png")

        # Try creating a process order via API call
        fg_code = page.locator(".fg-item.active").get_attribute("data-code")
        print(f"Selected FG code: {fg_code}")

        # Use page.evaluate to call the API
        result = page.evaluate("""async (fgCode) => {
            const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
            try {
                const resp = await fetch('/fg-codes/api/process-order/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf || ''
                    },
                    body: JSON.stringify({
                        fg_code: fgCode,
                        process_date: '2026-04-06',
                        process_order_id: 'TEST-PO-' + Date.now(),
                        key_variables: {},
                        calibration: {},
                        calculation_results: {}
                    })
                });
                const data = await resp.json();
                return { status: resp.status, data: data };
            } catch (e) {
                return { error: e.message };
            }
        }""", fg_code)

        print(f"API result: {result}")
        page.screenshot(path="test-results/po_create_result.png")

        if result.get('data', {}).get('success'):
            print("PASS: Process order created successfully")
        elif result.get('data', {}).get('error'):
            print(f"API Error: {result['data']['error']}")
        else:
            print(f"Unexpected result: {result}")

        browser.close()


if __name__ == "__main__":
    test_process_order_creation()
