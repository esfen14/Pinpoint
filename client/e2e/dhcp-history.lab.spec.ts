import { test, expect } from '@playwright/test'

// Opt-in issue #187: run only while the dedicated DHCP lab is exclusively owned.
const base = process.env.ISSUE187_LAB_URL
const firstHost = process.env.ISSUE187_FIRST_HOST
const secondHost = process.env.ISSUE187_SECOND_HOST
const evidence = process.env.ISSUE187_EVIDENCE_DIR

test('real DHCP move and A reuse remain distinct in Inventory and old History', async ({ page }) => {
  test.skip(!base || !firstHost || !secondHost || !evidence, 'Requires the live owned DHCP lab.')
  test.setTimeout(120_000)
  const email = process.env.PINPOINT_ADMIN_USER
  const password = process.env.PINPOINT_ADMIN_PASSWORD
  if (!email || !password) throw new Error('Supply the lab administrator credentials privately.')

  await page.goto(`${base}/login`)
  await page.locator('input[type=email]').fill(email)
  await page.locator('input[type=password]').fill(password)
  await page.locator('button[type=submit]').click()
  await expect(page).toHaveURL(/\/dashboard$/)

  await page.goto(`${base}/device-inventory`)
  const search = page.getByPlaceholder('Search hostname')
  await search.fill(firstHost!)
  const firstRow = page.getByRole('row').filter({ hasText: firstHost! })
  await expect(firstRow.getByText('10.79.0.6', { exact: true })).toBeVisible()
  await page.screenshot({ path: `${evidence}/inventory-client1-b.png` })
  await search.fill(secondHost!)
  const secondRow = page.getByRole('row').filter({ hasText: secondHost! })
  await expect(secondRow.getByText('10.79.0.5', { exact: true })).toBeVisible({ timeout: 15_000 })
  await page.screenshot({ path: `${evidence}/inventory-client2-a.png` })

  await page.goto(`${base}/history`)
  await page.getByRole('textbox', { name: 'Host', exact: true }).fill(firstHost!)
  await page.getByRole('button', { name: 'Apply', exact: true }).click()
  const preMove = page.locator('tbody tr').filter({ hasText: firstHost! }).filter({ hasText: 'DOWN' }).first()
  await expect(preMove).toBeVisible()
  await page.screenshot({ path: `${evidence}/history-client1-before-move.png` })
})
