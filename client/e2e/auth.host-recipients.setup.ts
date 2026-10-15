import { test as setup, expect } from '@playwright/test'

// This reader has network-health access but lacks system.hosts.alerts.
// Unlike the minimal smoke account, its first permitted landing page is Network Health.
setup('authenticate the host reader after mandatory password change', async ({ page }) => {
  const email = process.env.PINPOINT_RESTRICTED_USER
  const temporary = process.env.PINPOINT_RESTRICTED_PASSWORD
  const password = process.env.PINPOINT_RESTRICTED_NEW_PASSWORD
  if (!email || !temporary || !password) throw new Error('Private restricted lab credentials are required')
  await page.goto('/login')
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', temporary)
  await page.click('button[type="submit"]')
  await expect(page.getByRole('heading', { name: 'Change your password' })).toBeVisible()
  await page.getByLabel('Current (temporary) password').fill(temporary)
  await page.getByLabel('New password', { exact: true }).fill(password)
  await page.getByLabel('Confirm new password').fill(password)
  await page.getByRole('button', { name: 'Change password' }).click()
  await expect(page).toHaveURL('/network-health')
  await page.context().storageState({ path: '.auth/issue-79-reader.json' })
})
