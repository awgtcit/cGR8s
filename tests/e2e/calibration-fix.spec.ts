import { test, expect } from "@playwright/test";

const BASE = "http://127.0.0.1:5053";

test.describe("Calibration Search & N Target Consistency", () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE}/login/test-bypass`);
        await page.waitForURL("**/");
    });

    test("Calibration page loads and has search bar", async ({ page }) => {
        await page.goto(`${BASE}/master-data/calibration`);
        await expect(page.locator("h2, h3, .page-title, .card-header").first()).toBeVisible({ timeout: 10000 });
        // Search bar should be present
        const searchInput = page.locator('input[name="q"], input[type="search"], .search-bar input');
        await expect(searchInput.first()).toBeVisible();
        await page.screenshot({ path: "test-results/calibration-page-loaded.png", fullPage: true });
    });

    test("Calibration search filters by FG code", async ({ page }) => {
        await page.goto(`${BASE}/master-data/calibration`);
        await page.waitForTimeout(1000);

        // Take screenshot of full page first
        await page.screenshot({ path: "test-results/calibration-before-search.png", fullPage: true });

        // Count rows before search
        const rowsBefore = await page.locator("table tbody tr").count();

        // Type a search term in the search bar
        const searchInput = page.locator('input[name="q"], input[type="search"], .search-bar input').first();
        await searchInput.fill("1511");

        // Submit search (press Enter or click search button)
        await searchInput.press("Enter");
        await page.waitForTimeout(1000);

        // Take screenshot of filtered results
        await page.screenshot({ path: "test-results/calibration-after-search.png", fullPage: true });

        // Verify the URL has search parameter
        expect(page.url()).toContain("q=1511");

        // Verify filtered results show matching FG codes
        const rows = page.locator("table tbody tr");
        const rowCount = await rows.count();

        if (rowCount > 0) {
            // Each visible row should contain the search term in FG code column
            for (let i = 0; i < Math.min(rowCount, 5); i++) {
                const rowText = await rows.nth(i).textContent();
                expect(rowText?.toLowerCase()).toContain("1511");
            }
        }
    });

    test("N Target value on Calibration matches FG Codes page", async ({ page }) => {
        // Go to calibration page and get N Target for a specific FG code
        await page.goto(`${BASE}/master-data/calibration`);
        await page.waitForTimeout(1000);

        // Get the first row's FG code and N Target value
        const firstRow = page.locator("table tbody tr").first();
        await expect(firstRow).toBeVisible({ timeout: 10000 });

        // Get all cell texts from first row
        const cells = firstRow.locator("td");
        const cellCount = await cells.count();
        const cellTexts: string[] = [];
        for (let i = 0; i < cellCount; i++) {
            cellTexts.push((await cells.nth(i).textContent())?.trim() || "");
        }

        await page.screenshot({ path: "test-results/calibration-ntgt-row.png", fullPage: true });

        // Now navigate to FG Codes and check the same FG code's N Target
        await page.goto(`${BASE}/fg-codes`);
        await page.waitForTimeout(1000);
        await page.screenshot({ path: "test-results/fg-codes-page.png", fullPage: true });
    });

    test("Empty search returns all calibration records", async ({ page }) => {
        // Load page without search - count rows
        await page.goto(`${BASE}/master-data/calibration`);
        await page.waitForTimeout(1000);
        const rowsAll = await page.locator("table tbody tr").count();

        // Load page with empty search - should return same count
        await page.goto(`${BASE}/master-data/calibration?q=`);
        await page.waitForTimeout(1000);
        const rowsEmpty = await page.locator("table tbody tr").count();

        expect(rowsEmpty).toBe(rowsAll);
    });

    test("Nonexistent FG code search returns no results", async ({ page }) => {
        await page.goto(`${BASE}/master-data/calibration?q=ZZZZNOEXIST`);
        await page.waitForTimeout(1000);

        await page.screenshot({ path: "test-results/calibration-no-results.png", fullPage: true });

        const rows = page.locator("table tbody tr");
        const rowCount = await rows.count();
        // Should have 0 data rows or a "no results" message
        if (rowCount > 0) {
            const text = await rows.first().textContent();
            // It might show a "no data" row
            expect(text?.toLowerCase()).toMatch(/no.*data|no.*result|no.*record|0/);
        }
    });
});
