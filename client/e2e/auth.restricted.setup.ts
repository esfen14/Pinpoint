import { test as setup, expect } from '@playwright/test';

setup('restricted-role auth', async ({ page }) => {
  const email = process.env.PINPOINT_RESTRICTED_USER;
  const temporaryPassword = process.env.PINPOINT_RESTRICTED_PASSWORD;
  const newPassword = process.env.PINPOINT_RESTRICTED_NEW_PASSWORD;
  if (!email || !temporaryPassword || !newPassword) {
    throw new Error(
      'PINPOINT_RESTRICTED_USER / PINPOINT_RESTRICTED_PASSWORD / '
      + 'PINPOINT_RESTRICTED_NEW_PASSWORD must be set (no fallback)',
    );
  }

  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', temporaryPassword);
  await page.click('button[type="submit"]');

  await expect(page.getByRole('heading', { name: 'Change your password' })).toBeVisible();
  await page.getByLabel('Current (temporary) password').fill(temporaryPassword);
  await page.getByLabel('New password', { exact: true }).fill(newPassword);
  await page.getByLabel('Confirm new password').fill(newPassword);
  await page.getByRole('button', { name: 'Change password' }).click();
  await expect(page).toHaveURL('/settings');
  await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible();
  await page.context().storageState({ path: '.auth/restricted.json' });
});
