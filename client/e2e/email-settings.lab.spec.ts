import { execFileSync } from 'node:child_process'
import { expect, test } from '@playwright/test'

// Explicitly scoped disposable #115 appliance; never operate on the shared lab.
const labUrl = process.env.PINPOINT_SMTP_LAB_URL
const container = 'issue-115-smtp-appliance'
const quote = (value: string) => `'${value.replaceAll("'", "'\\''")}'`
function docker(args: string[], input?: string) {
  return execFileSync('sg', ['docker', '-c', ['docker', ...args].map(quote).join(' ')], {
    encoding: 'utf8', input, timeout: 15000,
  }).trim()
}
function count() {
  return JSON.parse(docker(['exec', container, 'cat', '/opt/issue115/counts.json'])).messages as number
}

test('live relay save/test and failure notice polling preserve password and edits', async ({ page }) => {
  test.setTimeout(90000)
  expect(labUrl).toBe('http://127.0.0.1:18115')
  expect(docker(['inspect', container, '--format', '{{index .Config.Labels "pinpoint.issue"}}'])).toBe('115')
  await page.goto(`${labUrl}/login`)
  await page.locator('input[type="email"]').fill('admin@test.com')
  await page.locator('input[type="password"]').fill('Password123!')
  await page.getByRole('button', { name: 'LOG IN', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  // Stop before any writes if this fixture has been repurposed for a real relay.
  const initial = await page.request.get(`${labUrl}/api/system/smtp-settings`)
  expect(initial.ok()).toBe(true)
  const { settings } = (await initial.json()).data
  expect(settings.provider).toBe('custom')
  expect(settings.host).toBe('localhost')
  expect(settings.port).toBe(2525)
  expect(settings.username).toBe('monitoring')
  await page.goto(`${labUrl}/settings`)
  await page.getByRole('button', { name: 'Email', exact: true }).click()
  const notice = page.getByText(/Last notification failure:/)
  await expect(notice).toBeVisible()
  await expect(page.getByText(/Notification command failed \(exit code 3\)/)).toBeVisible()
  await expect(page.getByRole('link', { name: 'Test email settings' })).toHaveAttribute('href', '#smtp-test-email')
  await page.getByRole('link', { name: 'Test email settings' }).click()
  await expect(page.getByLabel('Password', { exact: true })).toHaveValue('')
  await expect(page.getByLabel('Password', { exact: true })).toHaveAttribute('type', 'password')

  await page.getByLabel('Provider', { exact: true }).selectOption('gmail')
  await expect(page.getByLabel('Host', { exact: true })).toHaveValue('smtp.gmail.com')
  await expect(page.getByLabel('Host', { exact: true })).toBeDisabled()
  await expect(page.getByText(/Gmail does not accept your normal password here/)).toBeVisible()
  await page.getByLabel('Provider', { exact: true }).selectOption('custom')
  await page.getByLabel('Host', { exact: true }).fill('bad host')
  await page.getByRole('button', { name: /Save Changes/ }).click()
  await expect(page.getByText('The host must be a host name or IPv4 address, at most 253 characters.')).toBeVisible()
  await page.getByLabel('Host', { exact: true }).fill('localhost')
  await page.getByLabel('Port', { exact: true }).fill('2525')
  await page.getByLabel('Sender', { exact: true }).fill('browser-alerts@example.org')
  const saved = page.waitForResponse(r => r.url().endsWith('/api/system/smtp-settings') && r.request().method() === 'PUT')
  await page.getByRole('button', { name: /Save Changes/ }).click()
  const response = await saved
  expect(response.status()).toBe(200)
  expect(Object.hasOwn(response.request().postDataJSON(), 'password')).toBe(false)
  expect(await response.text()).not.toContain('synthetic-smtp-test-token')
  await expect(page.getByLabel('Password', { exact: true })).toHaveValue('')
  const before = count()
  await page.getByRole('button', { name: 'Send test email', exact: true }).click()
  await expect(page.getByText(/Test email sent to admin@test.com/)).toBeVisible()
  expect(count()).toBe(before + 1)
  await expect(notice).toBeVisible()
  expect(await page.evaluate(() => JSON.stringify([localStorage, sessionStorage]))).not.toContain('synthetic-smtp-test-token')

  // Rotation is owned test state. Polling must clear history without discarding edits.
  await page.getByLabel('Username', { exact: true }).fill('unsaved-monitoring')
  docker(['exec', '-i', container, '/usr/bin/python3', '-'],
    'from pathlib import Path\nimport os,pwd\np=Path("/usr/local/nagios/var/nagios.log")\np.rename(p.with_name("issue115-before-rotation.log"))\np.touch()\nu=pwd.getpwnam("nagios")\nos.chown(p,u.pw_uid,u.pw_gid)\np.chmod(0o644)\n')
  await expect(notice).toHaveCount(0, { timeout: 35000 })
  await expect(page.getByLabel('Username', { exact: true })).toHaveValue('unsaved-monitoring')
})
