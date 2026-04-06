import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:5053';

test('Admin: Auth URL change and test connection', async ({ page }) => {
    // 1. Bypass auth for testing
    await page.goto(`${BASE}/login/test-bypass`);
    await page.waitForURL('**/');

    // 2. Navigate to admin system config
    await page.goto(`${BASE}/admin/system-config`);
    await expect(page.locator('h2')).toContainText('System Configuration');

    // 3. Verify the auth URL field exists
    const authUrlField = page.locator('#auth_app_url');
    await expect(authUrlField).toBeVisible();

    // 4. Verify the Test Connection button exists
    const testBtn = page.locator('#btn-test-auth');
    await expect(testBtn).toBeVisible();
    await expect(testBtn).toContainText('Test Connection');

    // 5. Clear and enter a known-bad URL to test failure case
    await authUrlField.fill('http://localhost:9999');
    await testBtn.click();

    // Wait for result to appear
    const resultMsg = page.locator('#auth-test-message');
    await expect(resultMsg).toBeVisible({ timeout: 15000 });
    // Should show error since nothing is on port 9999
    await expect(resultMsg).toContainText(/Cannot reach|failed|error/i);

    // 6. Take screenshot of the error state
    await page.screenshot({ path: 'test-results/admin-auth-test-error.png', fullPage: true });

    // 7. Now enter the actual auth URL and test
    await authUrlField.fill('http://ams-it-126:5000');
    await testBtn.click();

    // Wait for result
    await expect(resultMsg).toBeVisible({ timeout: 15000 });
    // Take screenshot of whatever result we get
    await page.screenshot({ path: 'test-results/admin-auth-test-result.png', fullPage: true });

    // 8. Verify Save button exists
    const saveBtn = page.locator('button[type="submit"]');
    await expect(saveBtn).toBeVisible();
    await expect(saveBtn).toContainText('Save Configuration');
});
