import { test, expect, type Page } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Captures the manual screenshots (docs/images/manual/). Read-only: it navigates and
// screenshots, and never submits a form. Needs a lab in the fixture state described in
// docs/plans/TEMP_Manual_Screenshots_Plan.md. Light theme only, fixed 1440x900 window.
const OUT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs/images/manual');

test.use({ viewport: { width: 1440, height: 900 }, colorScheme: 'light', deviceScaleFactor: 1 });

async function settle(page: Page) {
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1500);
}

async function shoot(page: Page, name: string, fullPage = false) {
  await settle(page);
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage });
}

async function open(page: Page, route: string, name: string) {
  await page.goto(route);
  await shoot(page, name);
}

test.describe('sign-in page (no session)', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('UM-01 sign-in', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await shoot(page, 'UM-01-sign-in');
  });
});

test('UM-02 interface overview', async ({ page }) => {
  await open(page, '/dashboard', 'UM-02-interface-overview');
});

test('UM-03 dashboard with alerts', async ({ page }) => {
  await page.goto('/dashboard');
  await shoot(page, 'UM-03-dashboard-alerts', true);
});

test('UM-04 device inventory drawer', async ({ page }) => {
  await page.goto('/device-inventory');
  await settle(page);
  await page.getByRole('row').filter({ hasText: '10.77.1.4' }).getByTitle('View host details').click();
  await page.getByRole('heading', { name: /Ports/ }).first().scrollIntoViewIfNeeded();
  await shoot(page, 'UM-04-device-drawer');
});

const pages: Array<[string, string]> = [
  ['/network-health', 'network-health'],
  ['/system-status', 'network-status'],
  ['/device-inventory', 'device-inventory'],
  ['/history', 'history'],
  ['/plugins', 'plugin-manager'],
  ['/ncpa-deployment', 'ncpa-deployment'],
  ['/maintenance', 'maintenance'],
  ['/remediation', 'remediation'],
  ['/reports', 'reports'],
  ['/system-logs', 'system-logs'],
  ['/accounts', 'accounts'],
  ['/manage-roles', 'manage-roles'],
];
for (const [route, name] of pages) {
  test(`page ${name}`, async ({ page }) => {
    await open(page, route, `page-${name}`);
  });
}

const settingsTabs = ['General', 'Security', 'System', 'Discovery', 'Plugins', 'Email'];
for (const tab of settingsTabs) {
  test(`settings ${tab}`, async ({ page }) => {
    await page.goto('/settings');
    await settle(page);
    await page.getByRole('button', { name: new RegExp(tab, 'i') }).first().click();
    await shoot(page, `settings-${tab.toLowerCase()}`);
  });
}

test('page topology', async ({ page }) => {
  await page.goto('/topology');
  await settle(page);
  await page.getByRole('button', { name: /fit view/i }).click();
  await shoot(page, 'page-topology');
});

test('maintenance new window form', async ({ page }) => {
  await page.goto('/maintenance');
  await page.getByRole('button', { name: 'New window' }).click();
  await shoot(page, 'maintenance-new-window');
});

test('ncpa register-agent dialog', async ({ page }) => {
  await page.goto('/ncpa-deployment');
  await settle(page);
  await page.getByRole('button', { name: /Register an agent I installed on 10\.77\.1\./ }).first().click();
  await page.getByText('Installing NCPA on Windows').click();
  await shoot(page, 'ncpa-register-agent');
});
