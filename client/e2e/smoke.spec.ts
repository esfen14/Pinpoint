import { test, expect } from '@playwright/test';

test.describe('Role Smoke Tests', () => {
  test('J1-04: admin dashboard smoke', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1, h2')).toContainText(['Dashboard', 'Pinpoint']);
  });
});
