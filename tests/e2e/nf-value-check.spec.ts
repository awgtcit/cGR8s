import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:5053';

test('Check NF and NTDRY values for PO 2004038', async ({ page }) => {
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForURL('**/');
    await page.goto(`${BASE}/qa/data-grid`);
    await page.waitForLoadState('networkidle');

    // Find PO 2004038 row in the production table
    const row = page.locator('tr:has(td:has-text("2004038"))').first();
    await expect(row).toBeVisible({ timeout: 5000 });

    // Get all cells in that row
    const cells = await row.locator('td').allTextContents();
    console.log('All cells for PO 2004038:', cells.map(c => c.trim()));

    // Get headers to find NF and NTDRY column indices
    const headers = await page.locator('table thead th .th-label').allTextContents();
    const headerTexts = headers.map(h => h.trim());
    console.log('Headers:', headerTexts);

    const nfIdx = headerTexts.indexOf('NF');
    const ntdryIdx = headerTexts.indexOf('NTDRY');
    console.log(`NF index: ${nfIdx}, NTDRY index: ${ntdryIdx}`);

    if (nfIdx >= 0) {
        const nfVal = cells[nfIdx]?.trim();
        console.log(`NF value: "${nfVal}"`);
        // NF should be approximately 7.674
        expect(parseFloat(nfVal)).toBeCloseTo(7.674, 1);
    }

    if (ntdryIdx >= 0) {
        const ntdryVal = cells[ntdryIdx]?.trim();
        console.log(`NTDRY value: "${ntdryVal}"`);
        // NTDRY should be approximately 10.181
        expect(parseFloat(ntdryVal)).toBeCloseTo(10.181, 1);
    }

    // Take screenshot with NF column visible
    if (nfIdx >= 0) {
        const nfCell = row.locator('td').nth(nfIdx);
        await nfCell.scrollIntoViewIfNeeded();
    }
    await page.screenshot({ path: 'test-results/nf-value-check.png', fullPage: true });
});
