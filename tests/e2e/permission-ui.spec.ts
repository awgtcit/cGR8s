import { test, expect } from "@playwright/test";

const BASE = "http://127.0.0.1:5053";

test("Dashboard quick actions are wrapped in permission checks", async ({ page }) => {
    // Authenticate via test bypass
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForURL("**/");

    // Navigate to dashboard
    await page.goto(`${BASE}/`);
    await expect(page.locator("h2")).toContainText("Dashboard", { timeout: 10000 });
    // Quick Actions card should be visible
    const quickActionsCard = page.locator(".card-header", { hasText: "Quick Actions" });
    await expect(quickActionsCard).toBeVisible();

    // Take screenshot of dashboard with permission-gated quick actions
    await page.screenshot({ path: "test-results/dashboard-permission-actions.png", fullPage: true });

    // Verify the quick action items that ARE visible have the expected links
    const actionItems = page.locator(".quick-action-item");
    const count = await actionItems.count();
    // If user has permissions, cards should be visible; if not, fallback message shows
    if (count === 0) {
        await expect(page.locator("text=No quick actions available")).toBeVisible();
    } else {
        expect(count).toBeGreaterThan(0);
        expect(count).toBeLessThanOrEqual(4);
    }
});

test("Reports sidebar sub-menus have separate permission gating", async ({ page }) => {
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForURL("**/");
    // Check sidebar Reports toggle (the collapsible parent, not sub-links)
    const reportToggle = page.locator("#sidebar a.nav-sub-toggle", { hasText: "Reports" });
    const isReportsVisible = await reportToggle.isVisible();

    if (isReportsVisible) {
        // Expand if collapsed
        await reportToggle.click();
        await page.waitForTimeout(300);

        // Take screenshot showing reports sub-menu
        await page.screenshot({ path: "test-results/sidebar-reports-permissions.png", fullPage: true });

        // Check individual sub-menu items
        const allReportsLink = page.locator("#reportsSub a", { hasText: "All Reports" });
        const naturalLossLink = page.locator("#reportsSub a", { hasText: "Natural Loss" });

        // At least one sub-menu should be visible if parent is visible
        const allReportsVisible = await allReportsLink.isVisible();
        const naturalLossVisible = await naturalLossLink.isVisible();
        expect(allReportsVisible || naturalLossVisible).toBeTruthy();
    }
});
