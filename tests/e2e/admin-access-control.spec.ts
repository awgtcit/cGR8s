import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:5053';

test('Admin Access Control – full page loads', async ({ page }) => {
    // 1. Bypass auth
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForURL('**/');

    // 2. Navigate to access control
    await page.goto(`${BASE}/admin/access-control`);
    await expect(page.locator('h2')).toContainText(/Access Control/i, { timeout: 10000 });

    // 3. Wait for users to load (HTMX auto-load on tab)
    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await page.screenshot({ path: 'test-results/admin-ac-users.png', fullPage: true });

    // 4. Verify user data loaded (table has rows)
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();

    // 5. Click "Manage Roles" button
    const manageBtn = page.locator('button:has-text("Manage Roles"), a:has-text("Manage Roles")').first();
    if (await manageBtn.isVisible()) {
        await manageBtn.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'test-results/admin-ac-user-roles-modal.png', fullPage: true });
        // Close modal
        const closeBtn = page.locator('.modal .btn-close, .modal [data-bs-dismiss="modal"]').first();
        if (await closeBtn.isVisible()) await closeBtn.click();
        await page.waitForTimeout(500);
    }

    // 6. Click Roles tab
    await page.locator('#roles-tab').click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'test-results/admin-ac-roles.png', fullPage: true });

    // 7. Click "Permissions" button for a role — wait for HTMX response + modal
    const permsBtn = page.locator('#roles-pane button:has-text("Permissions")').first();
    await permsBtn.waitFor({ state: 'visible', timeout: 5000 });
    const roleDetailPromise = page.waitForResponse(
        resp => resp.url().includes('/access-control/roles/'),
        { timeout: 10000 }
    ).catch(() => null);
    await permsBtn.click();
    const roleResp = await roleDetailPromise;
    if (roleResp) {
        console.log(`Role detail response: ${roleResp.status()} ${roleResp.url()}`);
    }
    // Wait for modal to be visible
    await page.waitForSelector('#acModal.show, #acModal[style*="display: block"]', { timeout: 5000 }).catch(() => null);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-results/admin-ac-role-perms-modal.png', fullPage: true });
    // Close modal
    const closeBtn2 = page.locator('#acModal .btn-close, #acModal [data-bs-dismiss="modal"]').first();
    if (await closeBtn2.isVisible()) await closeBtn2.click();
    await page.waitForTimeout(500);

    // 8. Click Matrix tab — wait for HTMX to finish loading
    const matrixResponsePromise = page.waitForResponse(
        resp => resp.url().includes('/access-control/matrix'),
        { timeout: 15000 }
    ).catch(() => null);
    await page.locator('#matrix-tab').click();
    const matrixResp = await matrixResponsePromise;
    if (matrixResp) {
        console.log(`Matrix response: ${matrixResp.status()}`);
    }
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/admin-ac-matrix.png', fullPage: true });
});
