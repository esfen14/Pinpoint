import { expect, test, type Page } from '@playwright/test'

// Opt-in against the exclusively owned #182 VM through the private Unix-socket tunnel.
test.skip(process.env.PINPOINT_ISSUE182_LIVE !== '1', 'Requires the reserved issue182 appliance and target.')
const base = 'http://127.0.0.1:18080'
const settingsPath = '/api/system/deployment/ncpa/1/remote-restart'
function credential(name: string) {
  const value = process.env[name]
  if (!value) throw new Error(`Missing private runtime credential: ${name}`)
  return value
}
async function login(page: Page, reader = false) {
  await page.goto(`${base}/login`)
  await page.locator('input[type=email]').fill(credential(reader ? 'PINPOINT_READER_USER' : 'PINPOINT_ADMIN_USER'))
  await page.locator('input[type=password]').fill(credential(reader ? 'PINPOINT_READER_PASSWORD' : 'PINPOINT_ADMIN_PASSWORD'))
  await page.locator('button[type=submit]').click()
  await expect(page).toHaveURL(reader ? /\/remediation$/ : /\/dashboard$/)
}
async function ownedTarget(page: Page) {
  const response = await page.request.get(`${base}/api/system/deployment/ncpa/devices`)
  expect(response.ok()).toBeTruthy()
  const devices = (await response.json()).data.devices
  expect(devices).toHaveLength(1)
  expect(devices[0].device_id).toBe(1)
  expect(devices[0].ip_address).toBe('10.77.0.2')
  expect(devices[0].trusted).toBe(true)
  expect(devices[0].agent_status).toBe('Deployed NCPA')
}

test('RR-12 settings loading, retry, real validation, persistence and cleanup/redeployment', async ({ page }) => {
  test.setTimeout(180_000)
  await login(page)
  await ownedTarget(page)
  const original = (await (await page.request.get(`${base}${settingsPath}`)).json()).data
  await page.goto(`${base}/ncpa-deployment`)
  let release!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  // Only this load-error observation is fault injected; successful saves and all deployment operations use the real API.
  await page.route(`**${settingsPath}`, async route => {
    await gate
    await route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ success: false, message: 'Issue182 simulated load failure' }) })
  })
  await page.getByRole('button', { name: 'Remote restart', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: /^Remote restart:/ })
  try { await expect(dialog.getByText('Loading restart settings…')).toBeVisible() } finally { release() }
  await expect(dialog.getByRole('alert')).toHaveText('Issue182 simulated load failure')
  await expect(dialog.getByRole('button', { name: 'Save settings' })).toHaveCount(0)
  await page.unroute(`**${settingsPath}`)
  await dialog.getByRole('button', { name: 'Retry', exact: true }).click()
  await expect(dialog.getByLabel('Services allowed to restart')).toHaveValue(original.services.join('\n'))
  await expect(dialog.getByText(/Devices deployed before this feature need NCPA cleanup/)).toBeVisible()
  await dialog.getByLabel('Allow remote service restart').check()
  await dialog.getByLabel('Services allowed to restart').fill('')
  await dialog.getByRole('button', { name: 'Save settings' }).click()
  await expect(dialog.getByRole('alert')).toHaveText('Choose at least one service before turning remote restart on.')
  await expect(dialog.getByLabel('Allow remote service restart')).toBeChecked()
  await dialog.getByLabel('Services allowed to restart').fill('issue182-fixture\nissue182-slow\nissue182-browser')
  await dialog.getByRole('button', { name: 'Save settings' }).click()
  await expect(dialog.getByRole('status')).toHaveText(/Saved\. Clean up.*redeploy NCPA/)
  await dialog.getByRole('button', { name: 'Close', exact: true }).click()
  await page.getByRole('button', { name: 'Remote restart', exact: true }).click()
  await expect(dialog.getByLabel('Services allowed to restart')).toHaveValue('issue182-browser\nissue182-fixture\nissue182-slow')
  await expect(dialog.getByLabel('Allow remote service restart')).toBeChecked()
  await page.screenshot({ path: 'test-results/issue182-settings.png' })
  await dialog.getByLabel('Allow remote service restart').uncheck()
  await dialog.getByLabel('Services allowed to restart').fill(original.services.join('\n'))
  await dialog.getByRole('button', { name: 'Save settings' }).click()
  await expect(dialog.getByRole('status')).toContainText('Saved.')
  await dialog.getByRole('button', { name: 'Close', exact: true }).click()

  await page.getByRole('button', { name: 'Clean up', exact: true }).click()
  const cleanup = page.getByRole('dialog', { name: /^Clean up / })
  await expect(cleanup.getByText(/Remote service restarts stop working after cleanup/)).toBeVisible()
  await page.screenshot({ path: 'test-results/issue182-cleanup-warning.png' })
  await cleanup.getByLabel('SSH username').fill('demo')
  await cleanup.getByLabel('SSH password').fill(credential('PINPOINT_TARGET_PASSWORD'))
  await cleanup.getByRole('button', { name: 'Run cleanup', exact: true }).click()
  await expect(cleanup.getByText('Cleanup completed. Device is ready to deploy again.')).toBeVisible({ timeout: 45_000 })
  await expect(cleanup.getByLabel('SSH username')).toHaveValue('')
  await expect(cleanup.getByLabel('SSH password')).toHaveValue('')
  await cleanup.getByRole('button', { name: 'Close', exact: true }).click()
  await page.getByRole('checkbox', { name: /^Select / }).check()
  await page.getByRole('button', { name: 'Deploy selected', exact: true }).click()
  const wizard = page.getByRole('dialog', { name: 'Deploy NCPA', exact: true })
  await wizard.getByRole('button', { name: 'Next', exact: true }).click()
  await wizard.getByRole('button', { name: 'Next', exact: true }).click()
  await wizard.getByLabel('SSH username', { exact: true }).fill('demo')
  await wizard.getByLabel('Password', { exact: true }).fill(credential('PINPOINT_TARGET_PASSWORD'))
  await wizard.getByRole('button', { name: 'Check logins', exact: true }).click()
  await expect(wizard.getByText('Login and sudo verified.')).toBeVisible({ timeout: 30_000 })
  await wizard.getByRole('button', { name: 'Next', exact: true }).click()
  await wizard.getByRole('button', { name: 'Deploy NCPA', exact: true }).click()
  await expect(wizard).toHaveCount(0)
  await expect.poll(async () => {
    const response = await page.request.get(`${base}/api/system/deployment/ncpa/status`)
    return (await response.json()).data.status
  }, { timeout: 100_000, intervals: [2000, 4000] }).toBe('Success')
  await page.reload()
  await expect(page.getByRole('button', { name: 'Clean up', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Remote restart', exact: true }).click()
  await expect(dialog.getByLabel('Allow remote service restart')).not.toBeChecked()
  await expect(dialog.getByLabel('Services allowed to restart')).toHaveValue(original.services.join('\n'))
})

test('RR-12 remote/local action unit fields validate, persist and reload', async ({ page }) => {
  test.setTimeout(90_000)
  await login(page)
  await ownedTarget(page)
  const created: number[] = []
  try {
    await page.goto(`${base}/remediation`)
    await page.getByRole('button', { name: 'Add action', exact: true }).click()
    const form = page.getByRole('dialog', { name: 'Add action', exact: true })
    await form.getByLabel('Name', { exact: true }).fill('Issue182 browser remote')
    await form.getByLabel('Action type').selectOption('restart_remote_service')
    await form.getByLabel('Device').fill('dev-*')
    await form.getByLabel('Service', { exact: true }).fill('Issue182BrowserOnly')
    const unit = form.getByLabel('Service to restart')
    await unit.fill('bad/name')
    await form.getByRole('button', { name: 'Save action' }).click()
    await expect(unit).toHaveAttribute('aria-invalid', 'true')
    await expect(unit).toHaveValue('bad/name')
    await unit.fill('issue182-fixture')
    const saving = page.waitForResponse(r => r.url().endsWith('/api/system/remediation/actions') && r.request().method() === 'POST')
    await form.getByRole('button', { name: 'Save action' }).click()
    const saved = await saving
    expect(saved.status()).toBe(201)
    const remote = (await saved.json()).data
    created.push(remote.id)
    expect(remote.parameters).toEqual({ unit: 'issue182-fixture' })
    expect(remote.enabled).toBe(false)
    await page.getByRole('button', { name: 'Edit Issue182 browser remote', exact: true }).click()
    const edit = page.getByRole('dialog', { name: 'Edit action', exact: true })
    await expect(edit.getByLabel('Service to restart')).toHaveValue('issue182-fixture')
    await edit.getByLabel('Service to restart').fill('issue182-slow')
    await edit.getByRole('button', { name: 'Save action' }).click()
    await expect(edit).toHaveCount(0)
    await page.reload()
    await page.getByRole('button', { name: 'Edit Issue182 browser remote', exact: true }).click()
    await expect(edit.getByLabel('Service to restart')).toHaveValue('issue182-slow')
    await page.screenshot({ path: 'test-results/issue182-action-remote.png' })
    await edit.getByRole('button', { name: 'Cancel', exact: true }).click()
    await page.getByRole('button', { name: 'Add action', exact: true }).click()
    await form.getByLabel('Name', { exact: true }).fill('Issue182 browser local')
    await form.getByLabel('Action type').selectOption('restart_local_service')
    await form.getByLabel('Device').fill('dev-*')
    await form.getByLabel('Service', { exact: true }).fill('Issue182BrowserOnly')
    const choice = form.getByRole('combobox', { name: 'Service to restart' })
    await expect(choice.locator('option')).toHaveText(['Choose a service', 'nagios'])
    await choice.selectOption('nagios')
    const localSave = page.waitForResponse(r => r.url().endsWith('/api/system/remediation/actions') && r.request().method() === 'POST')
    await form.getByRole('button', { name: 'Save action' }).click()
    const localResponse = await localSave
    expect(localResponse.status()).toBe(201)
    const local = (await localResponse.json()).data
    created.push(local.id)
    expect(local.parameters).toEqual({ unit: 'nagios' })
    expect(local.enabled).toBe(false)
    await page.getByRole('button', { name: 'Edit Issue182 browser local', exact: true }).click()
    await expect(edit.getByLabel('Service to restart')).toHaveValue('nagios')
    await page.screenshot({ path: 'test-results/issue182-action-local.png' })
  } finally {
    for (const id of created) expect((await page.request.delete(`${base}/api/system/remediation/actions/${id}`)).ok()).toBeTruthy()
  }
})

test('RR-12 real read-only permissions hide editors and deny deployment/mutation routes', async ({ page }) => {
  await login(page, true)
  await expect(page.getByRole('heading', { name: 'Remediation', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Add action', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /^Edit / })).toHaveCount(0)
  const switches = page.getByRole('switch')
  await expect(switches.first()).toBeDisabled()
  expect((await page.request.get(`${base}${settingsPath}`)).status()).toBe(403)
  expect((await page.request.put(`${base}${settingsPath}`, { data: { enabled: true, services: ['issue182-fixture'] } })).status()).toBe(403)
  expect((await page.request.post(`${base}/api/system/remediation/actions`, { data: {} })).status()).toBe(403)
  await page.goto(`${base}/ncpa-deployment`)
  await expect(page).toHaveURL(/\/remediation$/)
  await expect(page.getByRole('button', { name: 'Remote restart', exact: true })).toHaveCount(0)
  await page.screenshot({ path: 'test-results/issue182-read-only.png' })
})
