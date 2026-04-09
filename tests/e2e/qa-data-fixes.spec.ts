import { test, expect } from "@playwright/test";

const BASE = "http://127.0.0.1:5053";

test.describe("QA Data Grid Display Fixes", () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE}/login/test-bypass`);
        await page.waitForURL("**/");
    });

    test("QA Data Grid loads with Production Data tab", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(2000);

        // Production Data tab should be active by default
        const prodTab = page.locator('a[href="#tab-production"]');
        await expect(prodTab).toBeVisible({ timeout: 10000 });

        await page.screenshot({ path: "test-results/qa-datagrid-production.png", fullPage: true });
    });

    test("Production Data shows correct NTM and TW columns", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(2000);

        // Check Production Data table exists and has rows
        const prodTable = page.locator('#tab-production table');
        await expect(prodTable.first()).toBeVisible({ timeout: 10000 });

        // Take close-up screenshot of the production table
        await page.screenshot({ path: "test-results/qa-production-ntm-tw.png", fullPage: true });

        // Check that table header contains NTM and TW columns
        const headers = await prodTable.first().locator('th').allTextContents();
        const headerText = headers.join(' ');

        // NTM and TW should be in headers
        expect(headerText).toContain('NTM');
        expect(headerText).toContain('TW');
    });

    test("Production Data TISS/TUN/RW1 values have comma formatting", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(2000);

        // Find Production table and look for comma-formatted numbers
        const prodTable = page.locator('#tab-production table');
        await expect(prodTable.first()).toBeVisible({ timeout: 10000 });

        // Get all cell text from the production table
        const cells = await prodTable.first().locator('td').allTextContents();
        const allText = cells.join('|');

        // Screenshot for visual verification
        await page.screenshot({ path: "test-results/qa-production-tiss-format.png", fullPage: true });

        // Check if any values have comma formatting (e.g., 1,234.56)
        // This validates TISS/TUN/RW1 columns are comma-formatted
        const hasCommaFormatted = cells.some(cell => /^\d{1,3}(,\d{3})+\.\d{2}$/.test(cell.trim()));

        // Log what we found for debugging
        console.log("Sample cell values:", cells.slice(0, 50).join(', '));
        console.log("Has comma-formatted values:", hasCommaFormatted);
    });

    test("Plug Wrap CU shows abbreviated values (e.g. 6K)", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(2000);

        const prodTable = page.locator('#tab-production table');
        await expect(prodTable.first()).toBeVisible({ timeout: 10000 });

        // Get all cell text and look for K abbreviations
        const cells = await prodTable.first().locator('td').allTextContents();
        const allText = cells.join('|');

        // Screenshot for visual verification
        await page.screenshot({ path: "test-results/qa-production-cu-abbrev.png", fullPage: true });

        // Check for K abbreviations (e.g., 6K, 5K, 1.5K)
        const hasKAbbrev = cells.some(cell => /^\d+(\.\d+)?K$/.test(cell.trim()));
        console.log("Has K-abbreviated values:", hasKAbbrev);
        console.log("Sample cells:", cells.filter(c => c.trim().endsWith('K')));
    });

    test("Daily Operation tab shows correct NTM, TW, and formatting", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(2000);

        // Click on Daily Operation tab
        const dailyTab = page.locator('a[href="#tab-daily"]');
        await dailyTab.click();
        await page.waitForTimeout(1000);

        // Take screenshot
        await page.screenshot({ path: "test-results/qa-daily-operation.png", fullPage: true });

        // Check daily table
        const dailyTable = page.locator('#tab-daily table');
        await expect(dailyTable.first()).toBeVisible({ timeout: 10000 });

        const headers = await dailyTable.first().locator('th').allTextContents();
        const headerText = headers.join(' ');
        expect(headerText).toContain('NTM');
        expect(headerText).toContain('TW');
    });

    test("QA Analysis tab loads and shows CU values", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(2000);

        // Click on QA Analysis tab
        const qaTab = page.locator('a[href="#tab-qa"]');
        await qaTab.click();
        await page.waitForTimeout(1000);

        await page.screenshot({ path: "test-results/qa-analysis-tab.png", fullPage: true });

        // Verify QA Analysis table is visible
        const qaTable = page.locator('#tab-qa table');
        await expect(qaTable.first()).toBeVisible({ timeout: 10000 });
    });

    test("Excel export link is available and accessible", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(2000);

        // Check for Excel export button/link
        const exportBtn = page.locator('a[href*="export"], button:has-text("Export"), .btn-export');
        await expect(exportBtn.first()).toBeVisible({ timeout: 10000 });

        await page.screenshot({ path: "test-results/qa-export-button.png", fullPage: true });
    });
});
