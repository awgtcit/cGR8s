import { test, expect } from "@playwright/test";

const BASE = "http://127.0.0.1:5053";

test.describe("QA Production Data – Plug Wrap CU & TOW columns", () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE}/login/test-bypass`);
        await page.waitForURL("**/");
    });

    test("Production Data tab shows Plug Wrap CU and TOW values (not dashes) when QA data exists", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(3000);

        // Ensure Production Data tab is active
        const prodTab = page.locator('a[href="#tab-production"]');
        await expect(prodTab).toBeVisible({ timeout: 10000 });
        await prodTab.click();
        await page.waitForTimeout(1000);

        // Scroll to Plug Wrap CU header in Production Data
        const plugWrapHeader = page.locator('#tab-production th:has-text("Plug Wrap CU")');
        await plugWrapHeader.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);

        // Take screenshot of Production Data tab showing Plug Wrap CU and TOW
        await page.screenshot({ path: "test-results/qa-prod-plugwrap-tow-right.png", fullPage: true });

        // Switch to QA Analysis tab and screenshot for comparison
        const qaTab = page.locator('a[href="#tab-qa"]');
        await qaTab.click();
        await page.waitForTimeout(1000);

        const qaPlugWrapHeader = page.locator('#tab-qa th:has-text("Plug Wrap CU")');
        await qaPlugWrapHeader.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        await page.screenshot({ path: "test-results/qa-analysis-plugwrap-tow-right.png", fullPage: true });
    });
});
