import { test as setup, expect } from '@playwright/test';
// Restricted-role smoke: must use env-only credentials; fails closed if missing.
// Forced-first-login / password-change verification requires a live restricted account.
setup('restricted-role auth', async ({ page }) => {
  const email = process.env.PINPOINT_RESTRICTED_USER;
  const password = process.env.PINPOINT_RESTRICTED_PASSWORD;
  if (!email || !password) {
    throw new Error('PINPOINT_RESTRICTED_USER / PINPOINT_RESTRICTED_PASSWORD must be set (no fallback)');
  }
  await page.goto('http://127.0.0.1:18080/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  // After restricted login, the first-login / forced-change path must occur.
  // Exact assertion depends on the application's restricted-role behavior.
  await expect(page).not.toHaveURL(/.*login/); // must have moved past login
  await page.context().storageState({ path: '.auth/restricted.json' });
});
