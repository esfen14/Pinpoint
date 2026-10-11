import { test, expect } from '@playwright/test';

test.describe('Role Smoke Tests', () => {
  test('J1-04: admin dashboard smoke', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: 'Network Status Overview' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Active Alerts' })).toBeVisible();
  });
});
