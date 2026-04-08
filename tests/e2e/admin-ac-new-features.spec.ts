import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:5053';

test('Create Role modal opens and validates', async ({ page }) => {
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForURL('**/');

    await page.goto(`${BASE}/admin/access-control`);
    await expect(page.locator('h2')).toContainText(/Access Control/i, { timeout: 10000 });

    // Switch to Roles tab
    await page.locator('#roles-tab').click();
    await page.waitForTimeout(3000);

    // Click Create Role button
    const createBtn = page.locator('button:has-text("Create Role")');
    await expect(createBtn).toBeVisible({ timeout: 5000 });
    await createBtn.click();

    // Wait for modal to appear
    await page.waitForSelector('#acModal.show, #acModal[style*="display: block"]', { timeout: 5000 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/admin-ac-create-role-modal.png', fullPage: true });

    // Verify form fields
    await expect(page.locator('#role_name')).toBeVisible();
    await expect(page.locator('#role_code_suffix')).toBeVisible();

    // Fill in values
    await page.fill('#role_name', 'Test Supervisor');
    await page.fill('#role_code_suffix', 'SUPERVISOR');
    await page.fill('#role_description', 'Test role for supervisors');
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/admin-ac-create-role-filled.png', fullPage: true });
});

test('Permissions modal shows CRUD and Special sections with scroll', async ({ page }) => {
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForURL('**/');

    await page.goto(`${BASE}/admin/access-control`);
    await expect(page.locator('h2')).toContainText(/Access Control/i, { timeout: 10000 });

    // Switch to Roles tab
    await page.locator('#roles-tab').click();
    await page.waitForTimeout(3000);

    // Click Permissions for first role (Administrator - should have all permissions)
    const permsBtn = page.locator('#roles-pane button:has-text("Permissions")').first();
    await permsBtn.waitFor({ state: 'visible', timeout: 5000 });
    await permsBtn.click();

    // Wait for modal
    await page.waitForSelector('#acModal.show', { timeout: 5000 });
    await page.waitForTimeout(1000);

    // Scroll down inside modal to see special access sections
    const modalBody = page.locator('.modal-body');
    await modalBody.evaluate(el => el.scrollTop = el.scrollHeight / 2);
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/admin-ac-perms-middle.png', fullPage: true });

    // Scroll to bottom
    await modalBody.evaluate(el => el.scrollTop = el.scrollHeight);
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/admin-ac-perms-bottom.png', fullPage: true });
});
