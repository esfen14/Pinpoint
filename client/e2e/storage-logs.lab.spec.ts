import { readFileSync } from 'node:fs'
import { test, expect } from '@playwright/test'

// Explicit opt-in: an exclusively owned appliance and private credential files.
// Run through the repository's no-network browser/Unix-socket lab boundary.
const baseUrl = process.env.ISSUE124_LAB_URL
const stateDir = process.env.ISSUE124_STATE_DIR

async function signIn(page: import('@playwright/test').Page, account: string) {
  await page.goto(`${baseUrl}/login`)
  await page.locator('input[type="email"]').fill(readFileSync(`${stateDir}/${account}-email`, 'utf8').trim())
  await page.locator('input[type="password"]').fill(readFileSync(`${stateDir}/${account}-password`, 'utf8').trim())
  await page.getByRole('button', { name: /sign in|log in/i }).click()
  await expect(page).not.toHaveURL(/\/login$/)
}

test.beforeEach(() => {
  test.skip(!baseUrl || !stateDir, 'Requires ISSUE124_LAB_URL and private ISSUE124_STATE_DIR on an exclusively owned appliance.')
})

test('administrator sees storage, latest log and real refresh', async ({ page }) => {
  await signIn(page, 'admin')
  await page.goto(`${baseUrl}/dashboard`)
  const storage = page.getByRole('region', { name: 'Appliance storage' })
  await expect(storage.getByText('system.db', { exact: true })).toBeVisible()
  await expect(storage.getByText('history.db', { exact: true })).toBeVisible()
  await expect(storage).toContainText('free of')
  await expect(storage).toContainText('below 10%')
  await page.goto(`${baseUrl}/system-logs`)
  await page.getByRole('button', { name: 'Nagios log', exact: true }).click()
  const log = page.getByRole('region', { name: 'Nagios log' })
  await expect(log.locator('pre')).toBeVisible()
  await expect(log).toContainText('Only the latest 200 lines within 64 KiB')
  const refreshed = page.waitForResponse((response) => response.url().includes('/api/system/log/nagios?lines=200'))
  await log.getByRole('button', { name: 'Refresh Nagios log' }).click()
  expect((await refreshed).status()).toBe(200)
  await expect(log.locator('pre')).toBeVisible()
  await page.getByRole('button', { name: 'Activity Log', exact: true }).click()
  await expect(page.getByPlaceholder('Search', { exact: true })).toBeVisible()
})

test('dashboard-only role sees storage despite denied network sources', async ({ page }) => {
  await signIn(page, 'dashboard')
  await page.goto(`${baseUrl}/dashboard`)
  await expect(page.getByRole('region', { name: 'Appliance storage' }).getByText('system.db', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'System Logs', exact: true })).toHaveCount(0)
})

test('logs-only role sees log and hides dashboard', async ({ page }) => {
  await signIn(page, 'logs')
  await page.goto(`${baseUrl}/system-logs`)
  await page.getByRole('button', { name: 'Nagios log', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Nagios log' }).locator('pre')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toHaveCount(0)
})

test('reader sees neither element and direct URLs are guarded', async ({ page }) => {
  await signIn(page, 'reader')
  await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'System Logs', exact: true })).toHaveCount(0)
  await page.goto(`${baseUrl}/dashboard`)
  await expect(page).not.toHaveURL(/\/dashboard$/)
  await expect(page.getByRole('region', { name: 'Appliance storage' })).toHaveCount(0)
  await page.goto(`${baseUrl}/system-logs`)
  await expect(page).not.toHaveURL(/\/system-logs$/)
  await expect(page.getByRole('button', { name: 'Nagios log', exact: true })).toHaveCount(0)
})
