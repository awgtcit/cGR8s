import { test, expect } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:5053";

test.describe("Process Order Delete", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE_URL}/login/test-bypass`);
        await page.waitForURL("**/");
    });

    test("delete button is visible on PO detail page with correct confirm message", async ({
        page,
    }) => {
        await page.goto(`${BASE_URL}/process-orders/`);
        await expect(page).toHaveURL(/process-orders/);

        const firstLink = page.locator("table tbody tr:first-child a").first();
        await expect(firstLink).toBeVisible({ timeout: 10000 });
        await firstLink.click();

        // Wait for detail page - heading is h2
        await expect(page.locator("h2")).toBeVisible({ timeout: 10000 });

        const deleteBtn = page.locator("button[data-confirm]");
        await expect(deleteBtn).toBeVisible();

        const confirmMsg = await deleteBtn.getAttribute("data-confirm");
        expect(confirmMsg).toContain("permanently delete");
        expect(confirmMsg).toContain("ALL related data");
    });

    test("delete confirmation dialog prevents accidental deletion", async ({
        page,
    }) => {
        await page.goto(`${BASE_URL}/process-orders/`);

        const firstLink = page.locator("table tbody tr:first-child a").first();
        await expect(firstLink).toBeVisible({ timeout: 10000 });
        await firstLink.click();

        await expect(page.locator("h2")).toBeVisible({ timeout: 10000 });

        page.on("dialog", (dialog) => dialog.dismiss());

        const deleteBtn = page.locator("button[data-confirm]");
        await deleteBtn.click();

        // Should stay on same page (dialog was dismissed)
        await expect(page.locator("h2")).toBeVisible();
    });
});
