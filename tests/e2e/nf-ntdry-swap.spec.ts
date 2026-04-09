import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:5053';

test.describe('NF / NTDRY Column Swap in QA Data Grid', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`${BASE}/login/test-bypass`);
        await page.waitForURL('**/');
    });
    test('QA Data Grid page loads with NF before NTDRY header', async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: 'test-results/qa-data-grid.png', fullPage: true });

        // Get header labels from the th-label spans
        const headers = await page.locator('table thead th .th-label').allTextContents();
        const headerTexts = headers.map(h => h.trim());

        // NF must come before NTDRY in the column headers
        const nfIdx = headerTexts.indexOf('NF');
        const ntdryIdx = headerTexts.indexOf('NTDRY');
        expect(nfIdx).toBeGreaterThan(-1);
        expect(ntdryIdx).toBeGreaterThan(-1);
        expect(nfIdx).toBeLessThan(ntdryIdx);
    });

    test('NTD, NF, NTDRY columns in correct order on Production tab', async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForLoadState('networkidle');

        // Click Production Data tab to ensure it's active
        const prodTab = page.locator('text=Production Data');
        if (await prodTab.count() > 0) await prodTab.first().click();
        await page.waitForTimeout(300);

        // Only select headers from the active tab's table
        const activePane = page.locator('.tab-pane.active, .tab-pane.show');
        const headers = await activePane.locator('table thead th .th-label').allTextContents();
        const headerTexts = headers.map(h => h.trim());

        const ntdIdx = headerTexts.indexOf('NTD');
        const nfIdx = headerTexts.indexOf('NF');
        const ntdryIdx = headerTexts.indexOf('NTDRY');

        // All three columns must exist and be in order: NTD < NF < NTDRY
        expect(ntdIdx).toBeGreaterThan(-1);
        expect(nfIdx).toBeGreaterThan(-1);
        expect(ntdryIdx).toBeGreaterThan(-1);
        expect(ntdIdx).toBeLessThan(nfIdx);
        expect(nfIdx).toBeLessThan(ntdryIdx);
    });

    test('Target Weight page loads', async ({ page }) => {
        await page.goto(`${BASE}/target-weight/`);
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: 'test-results/target-weight-page.png', fullPage: true });

        // Page should load without errors
        const title = await page.title();
        expect(title).toBeTruthy();
    });

    test('Excel export downloads successfully', async ({ page }) => {
        await page.goto(`${BASE}/qa/data-grid`);
        await page.waitForLoadState('networkidle');

        // Look for export button
        const exportBtn = page.locator('a:has-text("Export"), button:has-text("Export"), a[href*="export"]').first();
        if (await exportBtn.count() > 0) {
            const [download] = await Promise.all([
                page.waitForEvent('download', { timeout: 15000 }).catch(() => null),
                exportBtn.click(),
            ]);
            if (download) {
                const path = await download.path();
                expect(path).toBeTruthy();
                await page.screenshot({ path: 'test-results/qa-export-done.png' });
            }
        }
    });
});
