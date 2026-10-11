import { test, expect } from '@playwright/test';

test('admin smoke: login and dashboard', async ({ page }) => {
  const email = process.env.PINPOINT_ADMIN_USER;
  const password = process.env.PINPOINT_ADMIN_PASSWORD;
  if (!email || !password) throw new Error('PINPOINT_ADMIN_USER and PINPOINT_ADMIN_PASSWORD must be set (no defaults)');
  await page.goto('http://127.0.0.1:18080/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*dashboard/);
});
