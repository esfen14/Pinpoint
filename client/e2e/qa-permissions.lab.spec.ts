import { test, expect, type Page, type TestInfo } from '@playwright/test';

/** Evidence contains only fixed case observations, never login data or raw responses. */
async function observe(info: TestInfo, item: string, observed: string) {
  const id = info.title.split(':', 1)[0];
  await info.attach(`${id}-${item}`, {
    body: JSON.stringify({ case_id: id, item, verdict: 'PASS', observed, at: new Date().toISOString() }),
    contentType: 'application/json',
  });
}

/** Use an already initialized disposable Staff account; never repair account setup in a run. */
test.beforeEach(async ({ page }) => {
  const email = process.env.PINPOINT_RESTRICTED_USER;
  const password = process.env.PINPOINT_RESTRICTED_NEW_PASSWORD;
  if (!email || !password) throw new Error('A private initialized disposable Staff account is required');
  await page.goto('/login');
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL('/settings');
  const response = await page.request.get('/api/user/me');
  expect(response.status(), 'Staff precondition: authenticated session').toBe(200);
  const { data } = await response.json();
  // Boolean assertions prevent failed matchers from printing private account data.
  expect(data.role === 'Staff', 'Staff precondition: role').toBe(true);
  expect(Array.isArray(data.permissions) && data.permissions.length === 0,
    'Staff precondition: no page-management permissions').toBe(true);
  expect(data.needs_setup === false && data.must_change_password === false,
    'Staff precondition: setup/password change already complete').toBe(true);
});

test.afterEach(async ({ page }, info) => {
  // Cleanup is a supported API operation, not a substitute for any case UI step.
  const response = await page.request.post('/api/user/logout');
  expect([200, 401].includes(response.status()), 'Session cleanup response').toBe(true);
  expect((await page.request.get('/api/user/me')).status(), 'Session no longer authenticated').toBe(401);
  await info.attach('cleanup', { body: JSON.stringify({ session_closed: true }), contentType: 'application/json' });
});

/** Navigate as written, verify hidden sidebar item and the actual redirected page. */
async function deniedPage(page: Page, path: string, label: string) {
  await page.goto(path);
  await expect(page).toHaveURL('/settings');
  await expect(page.getByRole('heading', { name: 'System Settings', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: label, exact: true })).toHaveCount(0);
}

/** Open the API address in the browser as written; do not replace navigation with a mocked request. */
async function deniedApi(page: Page, path: string) {
  const response = await page.goto(path);
  expect(response?.status(), 'Protected API denies Staff').toBe(403);
}

test('TC-ACC-09: The accounts page needs permission', async ({ page }, info) => {
  await deniedPage(page, '/accounts', 'Manage Accounts');
  // qa-evidence:TC-ACC-09:E1
  await observe(info, 'E1', 'Manage Accounts absent from sidebar; direct address redirects to Settings.');
  await deniedApi(page, '/api/user/accounts');
  // qa-evidence:TC-ACC-09:E2
  await observe(info, 'E2', 'Accounts API address returns 403.');
});

test('TC-NCPA-08: NCPA Deployment needs permission', async ({ page }, info) => {
  await deniedPage(page, '/ncpa-deployment', 'NCPA Deployment');
  // qa-evidence:TC-NCPA-08:E1
  await observe(info, 'E1', 'NCPA Deployment absent from sidebar; direct address redirects to Settings.');
});

test('TC-SS-04: System Status needs permission', async ({ page }, info) => {
  await deniedPage(page, '/system-status', 'System Status');
  // qa-evidence:TC-SS-04:E1
  await observe(info, 'E1', 'System Status absent from sidebar; direct address redirects to Settings.');
});

test('TC-HIS-01: History needs permission', async ({ page }, info) => {
  await deniedPage(page, '/history', 'History');
  await deniedApi(page, '/api/system/history/alerts');
  // qa-evidence:TC-HIS-01:E1
  await observe(info, 'E1', 'History absent from sidebar; direct address redirects to Settings; API address returns 403.');
});

test('TC-RPT-07: Reports need permission', async ({ page }, info) => {
  await deniedPage(page, '/reports', 'Report');
  await deniedApi(page, '/api/system/report/availability');
  // qa-evidence:TC-RPT-07:E1
  await observe(info, 'E1', 'Report absent from sidebar; direct address redirects to Settings; API address returns 403.');
});

test('TC-LOG-05: System Logs need permission', async ({ page }, info) => {
  await deniedPage(page, '/system-logs', 'System Logs');
  await deniedApi(page, '/api/system/log');
  // qa-evidence:TC-LOG-05:E1
  await observe(info, 'E1', 'System Logs absent from sidebar; direct address redirects to Settings; API address returns 403.');
});

test('TC-PLG-07: Plugins need permission', async ({ page }, info) => {
  await deniedPage(page, '/plugins', 'Plugins');
  await deniedApi(page, '/api/plugin/summary');
  // qa-evidence:TC-PLG-07:E1
  await observe(info, 'E1', 'Plugins absent from sidebar; direct address redirects to Settings; API address returns 403.');
});
