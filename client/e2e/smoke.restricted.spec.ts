import { test, expect } from '@playwright/test';

test('J9-04: restricted user is redirected to permitted settings', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL('/settings');
  await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'General Settings' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Security' })).toHaveCount(0);

  const response = await page.request.get('/api/system/dashboard/status');
  expect(response.status()).toBe(403);
});
