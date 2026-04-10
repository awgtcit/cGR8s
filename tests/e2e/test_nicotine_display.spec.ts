import { test, expect } from "@playwright/test";

const BASE = "http://localhost:5053";

test.beforeEach(async ({ page }) => {
    // Bypass auth for Playwright testing
    await page.goto(`${BASE}/auth/login/test-bypass`);
    await page.waitForLoadState("networkidle");
});

test("TW Last Calc shows NTD, NF, NTDRY labels", async ({ page }) => {
    await page.goto(`${BASE}/target-weight`);
    await page.waitForLoadState("networkidle");
    const content = await page.content();
    expect(content).toContain("Total (NTD)");
    expect(content).toContain(">NF<");
    expect(content).toContain(">NTDRY<");
    await page.screenshot({ path: "test-results/tw-last-calc-nicotine.png", fullPage: true });
});

test("FG Codes calc results show nicotine demand section", async ({ page }) => {
    await page.goto(`${BASE}/fg-codes`);
    await page.waitForLoadState("networkidle");

    // Wait for FG list to load, then search
    await page.waitForSelector(".fg-item", { timeout: 15000 });
    await page.fill("#searchInput", "15110123");
    await page.waitForTimeout(1500);

    // Click first FG item
    const firstItem = page.locator(".fg-item").first();
    await firstItem.click();
    await page.waitForTimeout(2000);

    // Screenshot after selecting FG code
    await page.screenshot({ path: "test-results/fg-codes-selected.png", fullPage: true });

    // Click Calculate Target button
    const calcBtn = page.locator("#calculateBtn");
    await expect(calcBtn).toBeEnabled({ timeout: 5000 });
    await calcBtn.click();
    await page.waitForTimeout(3000);

    // Check the results panel for nicotine demand section
    const resultsContent = await page.locator("#resultsContent").innerHTML();
    expect(resultsContent).toContain("Pacifying Nicotine Demand");
    expect(resultsContent).toContain("NTD");
    expect(resultsContent).toContain("NF");
    expect(resultsContent).toContain("NTDRY");

    // Screenshot after calculation
    await page.screenshot({ path: "test-results/fg-codes-calc-nicotine.png", fullPage: true });
});
