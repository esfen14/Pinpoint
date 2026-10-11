import { test as setup, expect } from '@playwright/test';

setup('authenticate as admin', async ({ page }) => {
  const email = process.env.PINPOINT_ADMIN_USER;
  const password = process.env.PINPOINT_ADMIN_PASSWORD;
  if (!email || !password) {
    throw new Error('Set PINPOINT_ADMIN_USER and PINPOINT_ADMIN_PASSWORD privately before running live setup');
  }

  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await page.context().storageState({ path: '.auth/admin.json' });
});
