import { test, expect } from '@playwright/test';

test('J1-04: administrator can open the dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Network Status Overview' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Active Alerts' })).toBeVisible();
});
