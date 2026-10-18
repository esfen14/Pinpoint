import { test, expect, type Page, type TestInfo } from '@playwright/test';

/** Attach only fixed reviewed observations; never include account values or raw API bodies. */
async function observe(info: TestInfo, id: string, item: string, observed: string) {
  await info.attach(`${id}-${item}`, {
    body: JSON.stringify({ case_id: id, item, verdict: 'PASS', observed, at: new Date().toISOString() }),
    contentType: 'application/json',
  });
}

async function signIn(page: Page, email: string, password: string, role: string, required: string[], forbidden: string[]) {
  await page.goto('/login');
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  const current = await page.request.get('/api/user/me');
  expect(current.status(), 'Authenticated prerequisite account').toBe(200);
  const { data } = await current.json();
  expect(data.role === role, 'Prerequisite account role').toBe(true);
  expect(Array.isArray(data.permissions) && required.every((item) => data.permissions.includes(item)),
    'Prerequisite account required permissions').toBe(true);
  expect(Array.isArray(data.permissions) && forbidden.every((item) => !data.permissions.includes(item)),
    'Prerequisite account forbidden permissions').toBe(true);
}

test.afterEach(async ({ page }, info) => {
  const response = await page.request.post('/api/user/logout');
  expect([200, 401].includes(response.status()), 'Session cleanup response').toBe(true);
  expect((await page.request.get('/api/user/me')).status(), 'Session no longer authenticated').toBe(401);
  await info.attach('cleanup', { body: JSON.stringify({ session_closed: true }), contentType: 'application/json' });
});

test('TC-ACC-08: "Send this user email alerts" depends on permission', async ({ page }, info) => {
  const adminEmail = process.env.PINPOINT_ADMIN_USER;
  const adminPassword = process.env.PINPOINT_ADMIN_PASSWORD;
  const accountsEmail = process.env.PINPOINT_QA_ACCOUNTS_USER;
  const accountsPassword = process.env.PINPOINT_QA_ACCOUNTS_PASSWORD;
  if (!adminEmail || !adminPassword || !accountsEmail || !accountsPassword) {
    throw new Error('Use private credentials for Super Admin and the pre-created qa-accounts user.');
  }

  await signIn(page, adminEmail, adminPassword, 'Super Admin', ['account.view', 'account.alerts'], []);
  await page.goto('/accounts');
  await expect(page.getByRole('columnheader', { name: 'Email Alerts', exact: true })).toBeVisible();
  await expect(page.locator('table tbody tr').first().locator('td').nth(4)).toHaveText(/^(On|Off)$/);
  await expect(page.getByRole('button', { name: '+ Add User', exact: true })).toBeVisible();
  await page.getByRole('button', { name: '+ Add User', exact: true }).click();
  await expect(page.getByRole('checkbox', { name: 'Send this user email alerts', exact: true })).toBeVisible();

  // E1 covers the administrator-only checkbox and the per-user On/Off column.
  // qa-evidence:TC-ACC-08:E1
  await observe(info, 'TC-ACC-08', 'E1', 'Super Admin sees the Email Alerts column and email-alert checkbox.');

  const logout = await page.request.post('/api/user/logout');
  expect(logout.status(), 'End the Super Admin session before switching accounts').toBe(200);
  await signIn(page, accountsEmail, accountsPassword, 'qa-accounts', ['account.view', 'account.edit'], ['account.alerts']);
  await page.goto('/accounts');
  await expect(page.getByText('User Management', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: '+ Add User', exact: true }).click();
  await expect(page.getByText('Send this user email alerts', { exact: true })).toHaveCount(0);
  // qa-evidence:TC-ACC-08:E2
  await observe(info, 'TC-ACC-08', 'E2', 'The qa-accounts user does not see the email-alert checkbox.');
});

test('TC-ROL-04: A dashboard-only user is limited to the Dashboard', async ({ page }, info) => {
  const email = process.env.PINPOINT_QA_DASHBOARD_USER;
  const password = process.env.PINPOINT_QA_DASHBOARD_PASSWORD;
  if (!email || !password) throw new Error('Use private credentials for the pre-created qa-view user.');

  await signIn(page, email, password, 'qa-view', ['system.dashboard'], [
    'system.network_health', 'system.hosts', 'system.hosts.edit', 'plugin.view',
    'system.deploy.ncpa', 'maintenance.manage', 'remediation.view', 'system.history',
    'system.report', 'system.logs', 'account.view', 'role.view',
  ]);
  await page.goto('/dashboard');
  const links = await page.locator('aside a').evaluateAll((nodes) => nodes.map((node) => node.getAttribute('href')));
  expect(links, 'Only Overview and Settings are available in the sidebar').toEqual(['/dashboard', '/settings']);
  // qa-evidence:TC-ROL-04:E1
  await observe(info, 'TC-ROL-04', 'E1', 'Sidebar contains Overview and Settings only.');

  const protectedPages = [
    '/network-health', '/device-inventory', '/topology', '/system-status', '/plugins',
    '/ncpa-deployment', '/maintenance', '/remediation', '/history', '/reports',
    '/system-logs', '/accounts', '/manage-roles',
  ];
  for (const path of protectedPages) {
    await page.goto(path);
    await expect(page, `Restricted page ${path} redirects to Dashboard`).toHaveURL('/dashboard');
  }
  // qa-evidence:TC-ROL-04:E2
  await observe(info, 'TC-ROL-04', 'E2', 'All 13 protected page addresses redirect to the Dashboard.');

  const protectedApis = ['/api/system/log', '/api/system/report/availability', '/api/user/accounts'];
  for (const path of protectedApis) {
    const response = await page.goto(path);
    expect(response?.status(), `Restricted API ${path}`).toBe(403);
  }
  // qa-evidence:TC-ROL-04:E3
  await observe(info, 'TC-ROL-04', 'E3', 'All three protected API addresses return 403.');
});
