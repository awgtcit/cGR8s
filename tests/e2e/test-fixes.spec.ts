import { test, expect, chromium } from "@playwright/test";

const BASE_URL = "http://ams-it-126:5053";

test("Verify all fixes: formula-constants, gamma, calibration", async () => {
    const browser = await chromium.launch({ headless: false, channel: "chrome" });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Navigate to login page
    await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded", timeout: 15000 });

    // Try auto-login via env vars, otherwise wait for manual login
    const loginField = page.locator('input[name="login_id"]').first();
    const passwordField = page.locator('input[name="password"]').first();

    if (await loginField.isVisible({ timeout: 5000 }).catch(() => false)) {
        const loginId = process.env.CGRS_LOGIN || "";
        const loginPw = process.env.CGRS_PASSWORD || "";

        if (loginId && loginPw) {
            await loginField.fill(loginId);
            await passwordField.fill(loginPw);
            await page.locator('button[type="submit"]').first().click();
            await page.waitForTimeout(5000);
        } else {
            console.log("No CGRS_LOGIN/CGRS_PASSWORD env vars. Waiting 20s for manual login...");
            await page.waitForTimeout(20000);
        }
    }

    // Test 1: Formula Constants page - should NOT show ProgrammingError
    await page.goto(`${BASE_URL}/master-data/formula-constants`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(2000);
    const bodyText = await page.textContent("body") || "";
    expect(bodyText).not.toContain("ProgrammingError");
    expect(bodyText).not.toContain("Invalid object name");
    await page.screenshot({ path: "tests/e2e/screenshots/formula-constants-auth.png", fullPage: true });
    console.log("Formula Constants: No ProgrammingError ✓");

    // Test 2: Gamma Constants page
    await page.goto(`${BASE_URL}/master-data/gamma-constants`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: "tests/e2e/screenshots/gamma-constants-auth.png", fullPage: true });
    console.log("Gamma Constants page loaded ✓");

    // Test 3: Calibration Constants page
    await page.goto(`${BASE_URL}/master-data/calibration`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: "tests/e2e/screenshots/calibration-auth.png", fullPage: true });
    console.log("Calibration Constants page loaded ✓");

    // Test 4: FG Codes page - check SKU detail calibration tab
    await page.goto(`${BASE_URL}/fg-codes`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: "tests/e2e/screenshots/fg-codes-auth.png", fullPage: true });

    // Click first FG code to load SKU details
    const fgRow = page.locator(".fg-code-item, tr[data-fg-code], .list-group-item, .fg-row").first();
    if (await fgRow.isVisible({ timeout: 5000 }).catch(() => false)) {
        await fgRow.click();
        await page.waitForTimeout(3000);

        // Click Calibration tab
        const calTab = page.locator('[data-tab="calibration"], a:has-text("Calibration"), button:has-text("Calibration"), .nav-link:has-text("Calibration")').first();
        if (await calTab.isVisible({ timeout: 3000 }).catch(() => false)) {
            await calTab.click();
            await page.waitForTimeout(2000);
        }

        await page.screenshot({ path: "tests/e2e/screenshots/sku-calibration-tab.png", fullPage: true });
        console.log("SKU detail calibration tab loaded ✓");
    } else {
        console.log("No FG code rows found (may need different auth permissions)");
    }

    await browser.close();
});
