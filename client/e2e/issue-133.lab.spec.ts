import { test, expect } from '@playwright/test'

// Run only with scripts/playwright-lab --project issue-133-live against the approved VM.
// The real SSH failure/recovery is driven separately by scripts/vmlab targets.
test('issue 133: real History events can be filtered and inspected', async ({ page }) => {
  const host = 'dev-28829a'
  const service = 'ssh-22-tcp'

  await page.goto('/history')
  await expect(page.getByRole('button', { name: 'Alerts History' })).toBeVisible()
  await page.getByRole('textbox', { name: 'Host', exact: true }).fill(host)
  await page.getByRole('textbox', { name: 'Service', exact: true }).fill(service)
  await page.getByRole('button', { name: 'Apply' }).click()
  await expect(page.getByText(/Showing .* events/)).toBeVisible()
  const rows = page.locator('tbody tr').filter({ hasText: host })
  await expect(rows.first()).toBeVisible()
  await rows.first().click()
  await expect(page.getByText('Plugin output', { exact: true })).toBeVisible()
  await page.getByRole('combobox', { name: 'Rows per page' }).selectOption('50')
  await expect(page.getByText(/Showing .* events/)).toBeVisible()
  await page.getByRole('button', { name: 'Refresh' }).click()
  await expect(page.getByText(/Loaded /)).toBeVisible()
  await page.getByRole('button', { name: 'Host', exact: true }).click()
  await expect(page.getByText(/Showing .* events/)).toBeVisible()
  await page.getByRole('combobox', { name: 'Time range' }).selectOption('custom')
  await page.getByRole('button', { name: 'Apply' }).click()
  await expect(page.getByText('Pick a start and end date for a custom range.')).toBeVisible()
  await page.getByRole('button', { name: 'Clear filters' }).first().click()
  await expect(page.getByText(/Showing .* events/)).toBeVisible()

  await page.getByRole('button', { name: 'Notifications History' }).click()
  await expect(page.getByRole('combobox', { name: 'Source' })).toBeVisible()
  await page.getByRole('combobox', { name: 'Source' }).selectOption('nagios')
  await page.getByRole('button', { name: 'Apply' }).click()
  await expect(page.getByText(/Showing .* notifications/)).toBeVisible()
  await expect(page.locator('tbody').getByText('Nagios', { exact: true }).first()).toBeVisible()
  await page.locator('tbody tr').filter({ hasText: 'Nagios' }).first().click()
  await expect(page.getByText('Message', { exact: true })).toBeVisible()
  await expect(page.getByText('Contacts notified:')).toBeVisible()
  await page.getByRole('combobox', { name: 'Source' }).selectOption('pinpoint')
  await page.getByRole('button', { name: 'Apply' }).click()
  await expect(page.locator('tbody').getByText('Pinpoint', { exact: true }).first()).toBeVisible()
  await page.locator('tbody tr').filter({ hasText: 'Pinpoint' }).first().click()
  await expect(page.getByText('Message', { exact: true })).toBeVisible()

  await page.getByRole('textbox', { name: 'Host', exact: true }).fill('no-such-issue-133-host')
  await page.getByRole('button', { name: 'Apply' }).click()
  await expect(page.getByText('No events match the current filters.')).toBeVisible()
  await page.getByRole('button', { name: 'Clear filters' }).first().click()
  await expect(page.getByText(/Showing .* notifications/)).toBeVisible()
})
