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

test('issue 133: browser pagination with intercepted totals and list failure recovery', async ({ page }) => {
  // The preserved lab has fewer than 26 alert events. Simulate only pagination
  // metadata with real returned rows; this does not verify backend page 2.
  await page.route('**/api/system/history/alerts?*', async (route) => {
    const upstream = await route.fetch()
    const body = await upstream.json()
    const url = new URL(route.request().url())
    if (upstream.ok() && url.searchParams.get('per_page') === '25') {
      const current = Number(url.searchParams.get('page') ?? 1)
      // This fixture exercises page controls, not the backend count or identity.
      body.data = { ...body.data, items: current === 1 ? body.data.items : [body.data.items[0]].filter(Boolean), page: current, pages: 2, total: 26 }
      await route.fulfill({ response: upstream, json: body })
    } else {
      await route.fulfill({ response: upstream })
    }
  })
  await page.goto('/history')
  await expect(page.getByText('Showing 1–25 of 26 events')).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Pagination' })).toBeVisible()
  await page.getByRole('navigation', { name: 'Pagination' }).getByRole('button', { name: 'Next' }).click()
  await expect(page.getByText('Showing 26–26 of 26 events')).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Pagination' }).locator('[aria-current="page"]')).toHaveText('2')
  await page.getByRole('navigation', { name: 'Pagination' }).getByRole('button', { name: 'Previous' }).click()
  await expect(page.getByText('Showing 1–25 of 26 events')).toBeVisible()
  await page.unrouteAll({ behavior: 'wait' })

  let intercepted = false
  await page.route('**/api/system/history/alerts?*', async (route) => {
    if (!intercepted) {
      intercepted = true
      await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ success: false, message: 'History temporarily unavailable.' }) })
    } else {
      await route.continue()
    }
  })
  await page.getByRole('button', { name: 'Refresh' }).click()
  await expect(page.getByText('History temporarily unavailable.')).toBeVisible()
  expect(intercepted).toBe(true)
  await page.getByRole('button', { name: 'Refresh' }).click()
  await expect(page.getByText('History temporarily unavailable.')).toHaveCount(0)
  await expect(page.getByText(/Showing 1–\d+ of \d+ events/)).toBeVisible()
  await page.getByRole('combobox', { name: 'Rows per page' }).selectOption('50')
  await expect(page.getByText(/Showing 1–\d+ of \d+ events/)).toBeVisible()
})
