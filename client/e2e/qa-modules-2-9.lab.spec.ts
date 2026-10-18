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

async function signInSuperAdmin(page: Page) {
  const email = process.env.PINPOINT_ADMIN_USER;
  const password = process.env.PINPOINT_ADMIN_PASSWORD;
  if (!email || !password) throw new Error('Use the existing Super Admin credentials from the private store.');
  await signIn(page, email, password, 'Super Admin', ['system.network_health', 'system.hosts'], []);
}

async function openDevicePorts(page: Page) {
  const hostname = process.env.PINPOINT_QA_DEVICE_HOST;
  if (!hostname) throw new Error('Set PINPOINT_QA_DEVICE_HOST to the pre-reviewed fixture host.');
  await signInSuperAdmin(page);
  await page.goto('/device-inventory');
  await page.getByPlaceholder('Search hostname').fill(hostname);
  const hostButton = page.getByRole('button', { name: hostname, exact: true });
  await expect(hostButton).toBeVisible();
  await hostButton.click();
  await expect(page.getByRole('heading', { name: hostname, exact: true, level: 2 })).toBeVisible();
  const portsHeading = page.getByRole('heading', { name: 'Ports', exact: true, level: 3 });
  await expect(portsHeading).toBeVisible();
  return portsHeading.locator('..');
}

let tcAcc10Emails: string[] = [];

async function deactivateAccountIfPresent(page: Page, email: string) {
  await page.goto('/accounts');
  const search = page.getByPlaceholder('Search', { exact: true });
  await expect(search).toBeVisible();
  await search.fill(email);
  const row = page.getByRole('row').filter({ hasText: email });
  const count = await row.count();
  expect(count, 'A disposable account identity is unique').toBeLessThanOrEqual(1);
  if (count === 0) return false;
  if (await row.getByText('inactive', { exact: true }).count() === 1) return true;

  await row.getByTitle('Edit', { exact: true }).click();
  await page.locator('#edit-account-status').selectOption('inactive');
  await page.getByRole('button', { name: 'Save Changes', exact: true }).click();
  await expect(row.getByText('inactive', { exact: true }), 'Created QA account is inactive after cleanup').toBeVisible();
  return true;
}

test.afterEach(async ({ page }, info) => {
  if (info.title.startsWith('TC-ACC-10:')) {
    let deactivated = 0;
    for (const email of tcAcc10Emails) {
      if (await deactivateAccountIfPresent(page, email)) deactivated += 1;
    }
    await info.attach('account-cleanup', {
      body: JSON.stringify({ created_accounts_deactivated: deactivated, persistent_records_retained: true }),
      contentType: 'application/json',
    });
    tcAcc10Emails = [];
  }
  const response = await page.request.post('/api/user/logout');
  expect([200, 401].includes(response.status()), 'Session cleanup response').toBe(true);
  expect((await page.request.get('/api/user/me')).status(), 'Session no longer authenticated').toBe(401);
  await info.attach('cleanup', { body: JSON.stringify({ session_closed: true }), contentType: 'application/json' });
});

test('TC-ACC-10: Add User uses the default role', async ({ page }, info) => {
  const adminEmail = process.env.PINPOINT_ADMIN_USER;
  const adminPassword = process.env.PINPOINT_ADMIN_PASSWORD;
  const runToken = process.env.PINPOINT_QA_ACC10_RUN_TOKEN;
  const password = process.env.PINPOINT_QA_ACC10_PASSWORD;
  if (!adminEmail || !adminPassword || !runToken || !/^[a-z0-9-]{8,24}$/.test(runToken) || !password) {
    throw new Error('Use a unique reviewed run token and private password from the case card.');
  }

  await signIn(page, adminEmail, adminPassword, 'Super Admin', ['account.view', 'account.edit', 'account.alerts'], []);
  const rolesResponse = await page.request.get('/api/user/roles/options');
  expect(rolesResponse.status(), 'Active role list available to Super Admin').toBe(200);
  const rolesBody = await rolesResponse.json();
  const activeRoles = rolesBody.data.items;
  expect(Array.isArray(activeRoles) && activeRoles.length > 0, 'At least one active role is available').toBe(true);
  const firstRole = activeRoles[0];
  expect(Number.isInteger(firstRole.id) && typeof firstRole.name === 'string').toBe(true);
  const accountSummary = await page.request.get('/api/user/accounts?per_page=1');
  expect(accountSummary.status(), 'Account-list fixture preflight').toBe(200);
  expect((await accountSummary.json()).data.total, 'UI can display every account created in this case').toBeLessThanOrEqual(98);

  const email1 = `qa-acc10-${runToken}-1@example.invalid`;
  const email2 = `qa-acc10-${runToken}-2@example.invalid`;
  for (const email of [email1, email2]) {
    const existing = await page.request.get(`/api/user/accounts?per_page=2&search=${encodeURIComponent(email)}`);
    expect(existing.status(), 'Check the disposable address before creating it').toBe(200);
    expect((await existing.json()).data.items, 'Never modify an account from an earlier run').toHaveLength(0);
  }

  await page.goto('/accounts', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: '+ Add User', exact: true }).click();
  tcAcc10Emails = [email1, email2];

  for (const email of tcAcc10Emails) {
    await expect(page.getByRole('heading', { name: 'Profile Info', exact: true })).toBeVisible();
    const role = page.locator('select').first();
    await expect(role.locator('option')).not.toHaveCount(0);
    await expect(role).toHaveValue(String(firstRole.id));
    await expect(role.locator('option:checked')).toHaveText(firstRole.name);

    await page.getByPlaceholder('e.g. JUAN').fill('QA');
    await page.getByPlaceholder('e.g. CRUZ').fill('ACC10');
    await page.getByPlaceholder('e.g. juan.cruz@email.com').fill(email);
    await page.locator('select').nth(1).selectOption('inactive');
    const alerts = page.getByRole('checkbox', { name: 'Send this user email alerts', exact: true });
    await expect(alerts).toBeVisible();
    if (await alerts.isChecked()) await alerts.uncheck();
    const [passwordInput, confirmInput] = await page.locator('input[type="password"]').all();
    await passwordInput.fill(password);
    await confirmInput.fill(password);
    await expect(page.getByRole('button', { name: 'SAVE CHANGES', exact: true })).toBeEnabled();

    if (email === email1) {
      // qa-evidence:TC-ACC-10:E1
      await observe(info, 'TC-ACC-10', 'E1', 'The first active role is selected and Save is enabled for a valid form.');
    }

    await page.getByRole('button', { name: 'SAVE CHANGES', exact: true }).click();
    const row = page.getByRole('row').filter({ hasText: email });
    await expect(row, 'Created account appears without reloading').toHaveCount(1);
    await expect(row.getByText('inactive', { exact: true }), 'Disposable account is inactive').toBeVisible();
    if (email === email1) await page.getByRole('button', { name: '+ Add User', exact: true }).click();
  }

  await expect(page.getByRole('row').filter({ hasText: email1 })).toHaveCount(1);
  await expect(page.getByRole('row').filter({ hasText: email2 })).toHaveCount(1);
  await page.reload();
  await page.getByPlaceholder('Search', { exact: true }).fill(email1);
  await expect(page.getByRole('row').filter({ hasText: email1 })).toHaveCount(1);
  await page.getByPlaceholder('Search', { exact: true }).fill(email2);
  await expect(page.getByRole('row').filter({ hasText: email2 })).toHaveCount(1);
  // qa-evidence:TC-ACC-10:E2
  await observe(info, 'TC-ACC-10', 'E2', 'Both accounts appear without a reload and remain after reloading the page.');

  // E3 requires all active role options to be absent. The current safe fixture must
  // not disable system roles, so that condition remains a human-reviewed blocker.
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

test('TC-DI-02: Port groups and their order', async ({ page }, info) => {
  const ports = await openDevicePorts(page);
  const archived = ports.getByRole('button', { name: /^Archived \(\d+\)$/ });
  await expect(archived, 'The prepared fixture includes archived ports').toBeVisible();
  await archived.click();

  const groupHeadings = ports.locator('h4, button[aria-expanded="true"]');
  const labels = (await groupHeadings.allTextContents()).map((text) => text.trim());
  const groups = labels.map((label) => {
    const match = /^(Needs attention|Monitored|Suggested|Stopped|Archived) \((\d+)\)$/.exec(label);
    expect(match, `Valid group title and count: ${label}`).not.toBeNull();
    return { title: match![1], count: Number(match![2]) };
  });
  const expectedOrder = ['Needs attention', 'Monitored', 'Suggested', 'Stopped', 'Archived'];
  const actualOrder = groups.map(({ title }) => title);
  expect(actualOrder, 'Visible nonempty groups follow the required order').toEqual(
    expectedOrder.filter((title) => actualOrder.includes(title)),
  );
  expect(['Monitored', 'Suggested', 'Stopped', 'Archived'].every((title) => actualOrder.includes(title)),
    'The prepared device has each required lifecycle group').toBe(true);
  // qa-evidence:TC-DI-02:E1
  await observe(info, 'TC-DI-02', 'E1', 'Port group headers appear in the required order.');

  for (const { title, count } of groups) {
    const heading = ports.locator('h4, button[aria-expanded="true"]').filter({ hasText: new RegExp(`^${title} \\(\\d+\\)$`) });
    const group = heading.locator('..');
    const rows = group.locator('ul > li');
    await expect(rows, `${title} count matches its rows`).toHaveCount(count);
    expect(count, `${title} is shown only when nonempty`).toBeGreaterThan(0);
  }
  // qa-evidence:TC-DI-02:E2
  await observe(info, 'TC-DI-02', 'E2', 'Every shown group has a matching positive count; empty groups are absent.');

  for (const { title } of groups) {
    const heading = ports.locator('h4, button[aria-expanded="true"]').filter({ hasText: new RegExp(`^${title} \\(\\d+\\)$`) });
    const rows = heading.locator('..').locator('ul > li');
    const portLabels = await rows.evaluateAll((nodes) => nodes.map((node) => (
      node.querySelector(':scope > div > span')?.textContent?.trim() ?? ''
    )));
    const parsed = portLabels.map((label) => {
      const match = /^(tcp|udp)\/(\d+)$/i.exec(label.trim());
      expect(match, `Port label has protocol and number: ${label}`).not.toBeNull();
      return { label: label.trim(), protocolRank: match![1].toLowerCase() === 'tcp' ? 0 : 1, number: Number(match![2]) };
    });
    const sorted = [...parsed].sort((a, b) => a.protocolRank - b.protocolRank || a.number - b.number);
    expect(parsed.map((item) => item.label), `${title} ports are TCP then UDP, ordered by number`)
      .toEqual(sorted.map((item) => item.label));
  }
  // qa-evidence:TC-DI-02:E3
  await observe(info, 'TC-DI-02', 'E3', 'Each visible port group is ordered TCP then UDP, by port number.');
});

test('TC-DI-03: One reason per port', async ({ page }, info) => {
  const ports = await openDevicePorts(page);
  const label = process.env.PINPOINT_QA_HELD_MISMATCH_PORT;
  if (!label || !/^(tcp|udp)\/\d+$/i.test(label)) {
    throw new Error('Set PINPOINT_QA_HELD_MISMATCH_PORT to the pre-reviewed held mismatch port label.');
  }
  const portLabel = ports.getByText(label, { exact: true });
  const row = ports.locator('li').filter({ has: portLabel });
  await expect(row).toHaveCount(1);
  await expect(row.getByText('Held', { exact: true })).toBeVisible();
  await expect(row.getByText('Not used as intended', { exact: true })).toBeVisible();
  const reason = row.locator('p').filter({ hasText: /^Not used as intended:/ });
  await expect(reason, 'Only the first matching reason is shown').toHaveCount(1);
  await expect(row.getByText(/Held back/)).toHaveCount(0);
  // qa-evidence:TC-DI-03:E1
  await observe(info, 'TC-DI-03', 'E1', 'Exactly one reason is shown and the held-back reason is absent.');
  await expect(reason).toHaveText(/^Not used as intended: expected .+, found .+\. Not monitored until acknowledged\.$/);

  // qa-evidence:TC-DI-03:E2
  await observe(info, 'TC-DI-03', 'E2', 'The reason explains the expected/found names and says monitoring waits for acknowledgement.');
});

test('TC-DI-08: The Checked by line', async ({ page }, info) => {
  const tcpLabel = process.env.PINPOINT_QA_TCP_PORT;
  const udpLabel = process.env.PINPOINT_QA_UDP_PORT;
  if (!tcpLabel || !/^tcp\/\d+$/.test(tcpLabel) || !udpLabel || !/^udp\/\d+$/.test(udpLabel)) {
    throw new Error('Set PINPOINT_QA_TCP_PORT and PINPOINT_QA_UDP_PORT to reviewed existing port labels.');
  }
  const ports = await openDevicePorts(page);
  const current = await page.request.get('/api/user/me');
  expect(current.status()).toBe(200);
  const user = await current.json();
  expect(user.data.permissions, 'Opening Set service requires edit permission').toContain('system.hosts.edit');

  // This case must stay read-only even if the UI or adapter changes unexpectedly.
  const blockedWrites: string[] = [];
  await page.route('**/api/system/hosts/*/ports/*/*', async (route) => {
    if (route.request().method() === 'PUT') {
      blockedWrites.push(new URL(route.request().url()).pathname);
      await route.abort('blockedbyclient');
      return;
    }
    await route.continue();
  });

  const openDialog = async (label: string) => {
    const portText = ports.getByText(label, { exact: true });
    const row = ports.locator('li').filter({ has: portText });
    await expect(row, `Reviewed fixture port ${label} is present exactly once`).toHaveCount(1);
    await row.getByRole('button', { name: new RegExp(`^Set service.*${label.replace('/', '\\/')}`) }).click();
    return page.getByRole('dialog', { name: new RegExp(`Set service for ${label.replace('/', '\\/')}`) });
  };

  const tcp = await openDialog(tcpLabel);
  const input = tcp.getByRole('textbox', { name: 'Service name' });
  await input.fill('http');
  await expect(tcp.getByText('check_http', { exact: true })).toBeVisible();
  await expect(tcp.getByText("Scans will no longer change this port's service on this device.", { exact: false })).toBeVisible();
  // qa-evidence:TC-DI-08:E1
  await observe(info, 'TC-DI-08', 'E1', 'Known TCP service http resolves to check_http.');
  await input.fill('myapp');
  await expect(tcp.getByText('check_tcp (generic TCP check)', { exact: true })).toBeVisible();
  // qa-evidence:TC-DI-08:E2
  await observe(info, 'TC-DI-08', 'E2', 'Unknown TCP service resolves to the generic check_tcp label.');
  await tcp.getByRole('button', { name: 'Cancel', exact: true }).click();

  const udp = await openDialog(udpLabel);
  await udp.getByRole('textbox', { name: 'Service name' }).fill('myapp');
  await expect(udp.getByText('Skipped: no check exists for this UDP service', { exact: true })).toBeVisible();
  await expect(udp.getByText("Scans will no longer change this port's service on this device.", { exact: false })).toBeVisible();
  // qa-evidence:TC-DI-08:E3
  await observe(info, 'TC-DI-08', 'E3', 'Unknown UDP service shows that no UDP check exists.');
  // qa-evidence:TC-DI-08:E4
  await observe(info, 'TC-DI-08', 'E4', 'The service pin warning appears for TCP and UDP without saving either change.');
  await udp.getByRole('button', { name: 'Cancel', exact: true }).click();
  expect(blockedWrites, 'The adapter made no port mutation request').toEqual([]);
});

test('TC-DI-07: Service name rules in Set service', async ({ page }, info) => {
  const editableLabel = process.env.PINPOINT_QA_DI07_PORT;
  const sshLabel = process.env.PINPOINT_QA_DI07_SSH_PORT;
  if (!editableLabel || !/^(tcp|udp)\/\d+$/.test(editableLabel)
    || !sshLabel || !/^(tcp|udp)\/\d+$/.test(sshLabel) || editableLabel === sshLabel) {
    throw new Error('Set PINPOINT_QA_DI07_PORT and PINPOINT_QA_DI07_SSH_PORT to two reviewed port labels.');
  }
  const ports = await openDevicePorts(page);
  const current = await page.request.get('/api/user/me');
  expect(current.status()).toBe(200);
  expect((await current.json()).data.permissions, 'Opening Set service requires edit permission')
    .toContain('system.hosts.edit');
  const blockedWrites: string[] = [];
  await page.route('**/api/system/hosts/*/ports/*/*', async (route) => {
    if (route.request().method() === 'PUT') {
      blockedWrites.push(new URL(route.request().url()).pathname);
      await route.abort('blockedbyclient');
      return;
    }
    await route.continue();
  });

  const openDialog = async (label: string) => {
    const portText = ports.getByText(label, { exact: true });
    const row = ports.locator('li').filter({ has: portText });
    await expect(row, `Reviewed fixture port ${label} is present exactly once`).toHaveCount(1);
    await row.getByRole('button', { name: new RegExp(`^Set service.*${label.replace('/', '\\/')}`) }).click();
    return page.getByRole('dialog', { name: new RegExp(`Set service for ${label.replace('/', '\\/')}`) });
  };
  const name = await openDialog(editableLabel);
  const input = name.getByRole('textbox', { name: 'Service name' });
  const save = name.getByRole('button', { name: 'Save', exact: true });
  await expect(input, 'The editable fixture port must not already use ssh').not.toHaveValue('ssh');
  await input.fill('ssh');
  await expect(save, 'Valid ssh enables Save when it changes the current service').toBeEnabled();
  await input.fill('my_svc-1');
  await expect(save, 'Valid service name with underscore and hyphen enables Save').toBeEnabled();
  await input.fill('a'.repeat(32));
  await expect(save, 'A 32-character service name is valid').toBeEnabled();
  // qa-evidence:TC-DI-07:E1
  await observe(info, 'TC-DI-07', 'E1', 'ssh, my_svc-1 and a 32-character name are valid and enable Save when changed.');

  for (const invalid of ['SSH', '-ssh', 'a'.repeat(33), '']) {
    await input.fill(invalid);
    await expect(save, `Invalid service name ${invalid || '(empty)'} keeps Save disabled`).toBeDisabled();
  }
  // qa-evidence:TC-DI-07:E2
  await observe(info, 'TC-DI-07', 'E2', 'Uppercase, leading hyphen, 33 characters and empty service names keep Save disabled.');
  await name.getByRole('button', { name: 'Cancel', exact: true }).click();

  const ssh = await openDialog(sshLabel);
  const sshInput = ssh.getByRole('textbox', { name: 'Service name' });
  await expect(sshInput).toHaveValue('ssh');
  await expect(ssh.getByRole('button', { name: 'Save', exact: true }), 'Unchanged ssh keeps Save disabled').toBeDisabled();
  // qa-evidence:TC-DI-07:E3
  await observe(info, 'TC-DI-07', 'E3', 'Save is disabled when ssh is unchanged on a port already named ssh.');
  await ssh.getByRole('button', { name: 'Cancel', exact: true }).click();
  expect(blockedWrites, 'The adapter made no port mutation request').toEqual([]);
});

test('TC-HIS-04: Date range rules (API)', async ({ page }, info) => {
  const email = process.env.PINPOINT_ADMIN_USER;
  const password = process.env.PINPOINT_ADMIN_PASSWORD;
  if (!email || !password) throw new Error('Use the existing Super Admin credentials from the private store.');
  await signIn(page, email, password, 'Super Admin', ['system.history'], []);

  const valid = await page.request.get('/api/system/history/alerts?start_date=2026-10-01&end_date=2026-10-02');
  expect(valid.status(), 'A complete date range is accepted').toBe(200);
  const validBody = await valid.json();
  expect(validBody.success).toBe(true);
  expect(Array.isArray(validBody.data?.items), 'Valid range returns a list, including when it is empty').toBe(true);
  // qa-evidence:TC-HIS-04:E1
  await observe(info, 'TC-HIS-04', 'E1', 'A complete valid date range returns a list response.');

  const invalidUrls = [
    '/api/system/history/alerts?start_date=2026-10-01',
    '/api/system/history/alerts?start_date=2026-10-02&end_date=2026-10-01',
    '/api/system/history/alerts?start_date=abc&end_date=def',
  ];
  for (const url of invalidUrls) {
    const response = await page.request.get(url);
    expect(response.status(), `Invalid range ${url} is refused`).toBe(400);
    const body = await response.json();
    expect(body.success).toBe(false);
    expect(body).not.toHaveProperty('data');
  }
  // qa-evidence:TC-HIS-04:E2
  await observe(info, 'TC-HIS-04', 'E2', 'Missing, reversed and malformed date ranges return 400 without data.');

  const now = Math.floor(Date.now() / 1000);
  const startDate = new Date((now - 30 * 86400) * 1000).toISOString().slice(0, 10);
  const endDate = new Date(now * 1000).toISOString().slice(0, 10);
  const oldEventsResponse = await page.request.get(
    `/api/system/history/alerts?start_date=${startDate}&end_date=${endDate}&sort_by=timestamp&order=asc&per_page=100`,
  );
  expect(oldEventsResponse.status(), 'Existing history is available to confirm default filtering').toBe(200);
  const oldEvents = (await oldEventsResponse.json()).data.items as Array<{ event_id: string; timestamp: number }>;
  const oldEvent = oldEvents.find((event) => event.timestamp < now - 25 * 3600);
  expect(oldEvent, 'Fixture includes an event older than 25 hours within the last 30 days').toBeTruthy();

  const defaultRange = await page.request.get('/api/system/history/alerts?per_page=100');
  expect(defaultRange.status(), 'The no-date request uses the default range').toBe(200);
  const defaultEvents = (await defaultRange.json()).data.items as Array<{ event_id: string; timestamp: number }>;
  expect(defaultEvents.some((event) => event.event_id === oldEvent!.event_id),
    'An event known to be older than 25 hours is outside the default range').toBe(false);
  expect(defaultEvents.every((event) => event.timestamp >= now - 25 * 3600),
    'All returned default-range events fall within 24 hours with clock tolerance').toBe(true);
  // qa-evidence:TC-HIS-04:E3
  await observe(info, 'TC-HIS-04', 'E3', 'A known event older than 25 hours is excluded when dates and preset are omitted.');
});

test('TC-DASH-07: "No data" instead of blank cards', async ({ page }, info) => {
  await signInSuperAdmin(page);
  await page.goto('/dashboard');

  const latencyTitle = page.getByText('Network Latency', { exact: true });
  await expect(latencyTitle).toBeVisible();
  const latencyCard = latencyTitle.locator('..').locator('..');
  await expect(latencyCard.getByText('No data', { exact: true })).toBeVisible();

  const performanceTitle = page.getByRole('heading', { name: 'Network Performance', exact: true });
  const performance = performanceTitle.locator('..').locator('..');
  await expect(performance).toBeVisible();
  await expect(performance.getByText('No data', { exact: true })).toHaveCount(2);
  // qa-evidence:TC-DASH-07:E1
  await observe(info, 'TC-DASH-07', 'E1', 'Network Latency and both Network Performance metrics show No data.');

  await expect(page.getByRole('heading', { name: 'Average Resource Utilization', exact: true })).toHaveCount(0);
  // qa-evidence:TC-DASH-07:E2
  await observe(info, 'TC-DASH-07', 'E2', 'Average Resource Utilization is absent without NCPA data.');
});
