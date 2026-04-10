import { test, expect } from "@playwright/test";

const BASE = "http://127.0.0.1:5053";

test.describe("QA Analysis – single cell save", () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE}/login/test-bypass`);
        await page.waitForURL("**/");
    });

    test("Editing one cell only updates that cell, not other cells in the row", async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForTimeout(3000);

        // Switch to QA Analysis tab
        const qaTab = page.locator('a[href="#tab-qa"]');
        await expect(qaTab).toBeVisible({ timeout: 10000 });
        await qaTab.click();
        await page.waitForTimeout(1500);

        // Screenshot before any edit
        await page.screenshot({ path: "test-results/qa-cell-save-before.png", fullPage: true });

        // Find the first row with data in the QA grid
        const firstRow = page.locator('#qa-grid tbody tr[data-po-number]').first();
        await expect(firstRow).toBeVisible({ timeout: 5000 });

        // Read the current filling_power value in the first row
        const fpInput = firstRow.locator('input.cell-input[data-field="filling_power"]');
        const originalFP = await fpInput.inputValue();
        console.log(`Original filling_power: "${originalFP}"`);

        // Read another cell that we will NOT edit (e.g. lamina_cpi)
        const lcInput = firstRow.locator('input.cell-input[data-field="lamina_cpi"]');
        const originalLC = await lcInput.inputValue();
        console.log(`Original lamina_cpi: "${originalLC}"`);

        // Edit ONLY filling_power — change it to a test value then back
        const testValue = originalFP ? String((parseFloat(originalFP) + 0.01).toFixed(2)) : "99.99";
        await fpInput.click();
        await fpInput.fill(testValue);
        await fpInput.press("Tab");
        await page.waitForTimeout(500);

        // Verify only the edited cell has the "dirty" class
        const fpDirty = await fpInput.evaluate(el => el.classList.contains('dirty'));
        const lcDirty = await lcInput.evaluate(el => el.classList.contains('dirty'));
        console.log(`filling_power dirty: ${fpDirty}, lamina_cpi dirty: ${lcDirty}`);
        expect(fpDirty).toBe(true);
        expect(lcDirty).toBe(false);

        // Screenshot before save
        await page.screenshot({ path: "test-results/qa-cell-save-edited.png", fullPage: true });

        // Click Save All
        const saveBtn = page.locator('#btn-save-qa');
        await expect(saveBtn).toBeVisible();
        await saveBtn.click();
        await page.waitForTimeout(3000);

        // Handle the alert
        page.on('dialog', async dialog => {
            console.log(`Alert: ${dialog.message()}`);
            await dialog.accept();
        });

        // Wait for reload
        await page.waitForTimeout(3000);

        // Screenshot after save
        await page.screenshot({ path: "test-results/qa-cell-save-after.png", fullPage: true });

        // Switch to QA Analysis tab again (page reloaded)
        const qaTab2 = page.locator('a[href="#tab-qa"]');
        await qaTab2.click();
        await page.waitForTimeout(1500);

        // Re-read lamina_cpi — it should NOT have changed
        const firstRow2 = page.locator('#qa-grid tbody tr[data-po-number]').first();
        const lcInput2 = firstRow2.locator('input.cell-input[data-field="lamina_cpi"]');
        const afterLC = await lcInput2.inputValue();
        console.log(`After save lamina_cpi: "${afterLC}"`);

        // The untouched cell should keep its original value
        expect(afterLC).toBe(originalLC);

        // Screenshot final state
        await page.screenshot({ path: "test-results/qa-cell-save-final.png", fullPage: true });
    });
});
