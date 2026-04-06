"""Playwright E2E test: N Target inline editing from Calibration tab."""
import re
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5053"


def test_n_target_editable():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Login via test bypass
        page.goto(f"{BASE}/login/test-bypass")
        page.wait_for_load_state("networkidle")

        # Navigate to FG Codes
        page.goto(f"{BASE}/fg-codes/")
        page.wait_for_load_state("networkidle")

        # Click on the first FG code in the list
        page.wait_for_selector(".fg-item", timeout=10000)
        page.locator(".fg-item").first.click()
        page.wait_for_timeout(1500)

        # Click the Calibration tab button
        page.locator('button[data-tab="calibration"]').click()
        page.wait_for_timeout(500)

        # Screenshot before edit
        page.screenshot(path="test-results/n_target_before.png")

        # Verify the N Target input exists
        n_input = page.locator("#nTargetInput")
        assert n_input.is_visible(), "N Target input should be visible"

        # Save button should be visible
        save_btn = page.locator("button:has-text('Save')")
        assert save_btn.is_visible(), "Save button should be visible"

        # Get current value
        current_val = n_input.input_value()
        print(f"Current N Target value: {current_val}")

        # Edit the value
        test_val = "0.55"
        n_input.fill(test_val)

        # Listen for network response
        with page.expect_response("**/api/update-n-target**", timeout=10000) as response_info:
            save_btn.click()

        response = response_info.value
        print(f"Response status: {response.status}")
        print(f"Response body: {response.text()}")

        page.wait_for_timeout(500)

        # Screenshot after edit
        page.screenshot(path="test-results/n_target_after_save.png")

        # Check success status
        status = page.locator("#nTargetStatus")
        status_text = status.inner_text()
        print(f"Status: {status_text}")
        assert "Saved" in status_text, f"Expected 'Saved' status but got '{status_text}'"

        # Restore original value
        if current_val:
            n_input.fill(current_val)
            save_btn.click()
            page.wait_for_timeout(1500)

        page.screenshot(path="test-results/n_target_restored.png")
        print("PASS: N Target is editable and saves successfully")
        browser.close()


if __name__ == "__main__":
    test_n_target_editable()
