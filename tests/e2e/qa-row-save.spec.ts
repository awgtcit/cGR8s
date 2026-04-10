import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5053';

test('editing one row does not affect other rows', async ({ page }) => {
    // Login via test bypass
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForLoadState('networkidle');

    // Navigate to QA data grid
    await page.goto(`${BASE}/qa/data-grid`);
    await page.waitForLoadState('networkidle');

    // Click on QA Analysis tab to make the QA grid visible
    const qaTab = page.locator('text=QA Analysis');
    await qaTab.click();
    await page.waitForTimeout(500);

    // Wait for the QA grid table
    await page.waitForSelector('#qa-grid tbody tr[data-po-number]', { state: 'attached' });

    // Get all rows
    const rows = page.locator('#qa-grid tbody tr[data-po-number]');
    const rowCount = await rows.count();
    console.log(`Total rows: ${rowCount}`);

    if (rowCount < 2) {
        test.skip(true, 'Need at least 2 rows to test row isolation');
        return;
    }

    // Get PO IDs for row 1 and row 2
    const row1PoId = await rows.nth(0).getAttribute('data-po-id');
    const row2PoId = await rows.nth(1).getAttribute('data-po-id');
    const row1PoNum = await rows.nth(0).getAttribute('data-po-number');
    const row2PoNum = await rows.nth(1).getAttribute('data-po-number');
    console.log(`Row 1: PO ID=${row1PoId}, PO Num=${row1PoNum}`);
    console.log(`Row 2: PO ID=${row2PoId}, PO Num=${row2PoNum}`);

    // Read current filling_power values from both rows
    const fp1Input = rows.nth(0).locator('input[data-field="filling_power"]');
    const fp2Input = rows.nth(1).locator('input[data-field="filling_power"]');
    const originalFP1 = await fp1Input.inputValue();
    const originalFP2 = await fp2Input.inputValue();
    console.log(`Original filling_power: Row1=${originalFP1}, Row2=${originalFP2}`);

    // Read current lamina_cpi for row 2 (should remain unchanged)
    const lc2Input = rows.nth(1).locator('input[data-field="lamina_cpi"]');
    const originalLC2 = await lc2Input.inputValue();
    console.log(`Original lamina_cpi Row2=${originalLC2}`);

    // Edit ONLY row 1's filling_power — add 0.01
    const newFP1 = originalFP1 ? (parseFloat(originalFP1) + 0.01).toFixed(2) : '9.99';
    await fp1Input.fill(newFP1);
    await fp1Input.dispatchEvent('input'); // trigger dirty mark
    console.log(`Set Row1 filling_power to ${newFP1}`);

    // Verify only row 1's input is dirty
    const row1Dirty = await fp1Input.evaluate(el => el.classList.contains('dirty'));
    const row2FPDirty = await fp2Input.evaluate(el => el.classList.contains('dirty'));
    const row2LCDirty = await lc2Input.evaluate(el => el.classList.contains('dirty'));
    console.log(`Row1 FP dirty: ${row1Dirty}, Row2 FP dirty: ${row2FPDirty}, Row2 LC dirty: ${row2LCDirty}`);
    expect(row1Dirty).toBe(true);
    expect(row2FPDirty).toBe(false);
    expect(row2LCDirty).toBe(false);

    // Register dialog handler BEFORE clicking save
    page.on('dialog', async dialog => {
        console.log(`Dialog: ${dialog.message()}`);
        await dialog.accept();
    });

    // Click Save All
    const saveBtn = page.locator('#btn-save-qa');
    await saveBtn.click();

    // Wait for page reload after save
    await page.waitForLoadState('networkidle');
    // Re-click QA Analysis tab after reload
    await page.locator('text=QA Analysis').click();
    await page.waitForTimeout(500);
    await page.waitForSelector('#qa-grid tbody tr[data-po-number]', { state: 'attached' });

    // Re-read values after save/reload
    const rowsAfter = page.locator('#qa-grid tbody tr[data-po-number]');
    const fp1After = await rowsAfter.nth(0).locator('input[data-field="filling_power"]').inputValue();
    const fp2After = await rowsAfter.nth(1).locator('input[data-field="filling_power"]').inputValue();
    const lc2After = await rowsAfter.nth(1).locator('input[data-field="lamina_cpi"]').inputValue();

    console.log(`After save — Row1 FP: ${fp1After}, Row2 FP: ${fp2After}, Row2 LC: ${lc2After}`);

    // Row 1's filling_power should be updated
    expect(fp1After).toBe(newFP1);

    // Row 2's values should be UNCHANGED
    expect(fp2After).toBe(originalFP2);
    expect(lc2After).toBe(originalLC2);

    console.log('✅ Row isolation test passed — editing row 1 did not affect row 2');
});
