import { test, expect } from '@playwright/test'

// Opt-in only: source and target are expendable fixtures on an exclusively owned lab.
const base = process.env.ISSUE164_LAB_URL
const sourceId = process.env.ISSUE164_SOURCE_ID
const targetId = process.env.ISSUE164_TARGET_ID
const expectWarning = process.env.ISSUE164_EXPECT_CONFIG_WARNING === '1'

test('identity review to comparison, cancellation, explicit merge and surviving record', async ({ page }) => {
  test.skip(!base || !sourceId || !targetId, 'Requires a reserved Docker lab with controlled identity fixtures.')
  test.setTimeout(90_000)
  const email = process.env.PINPOINT_ADMIN_USER
  const password = process.env.PINPOINT_ADMIN_PASSWORD
  if (!email || !password) throw new Error('Supply lab administrator credentials privately.')
  await page.goto(`${base}/login`)
  await page.locator('input[type=email]').fill(email)
  await page.locator('input[type=password]').fill(password)
  await page.locator('button[type=submit]').click()
  await expect(page).toHaveURL(/\/dashboard$/)
  const reviewsBefore = await page.request.get(`${base}/api/system/discover/review`)
  expect(reviewsBefore.ok()).toBeTruthy()
  const before = (await reviewsBefore.json()).data.items
  const review = before.find((r: { kind: string; devices: { id: number }[] }) => r.kind !== 'SERVICE_CHANGED' && r.devices.some(d => String(d.id) === sourceId))
  expect(review).toBeTruthy()
  expect(before.some((r: { kind: string }) => r.kind === 'SERVICE_CHANGED')).toBeTruthy()
  const detail = await page.request.get(`${base}/api/system/hosts/${sourceId}/identifiers`)
  const source = (await detail.json()).data.device
  expect(source.monitoring_state).not.toBe('monitored')
  const targetBefore = (await (await page.request.get(`${base}/api/system/hosts/${targetId}/identifiers`)).json()).data.device
  await page.goto(`${base}/device-inventory`)
  const section = page.getByRole('region', { name: 'Device identity reviews', exact: true })
  await expect(section.getByRole('heading', { name: 'Needs Review (1)' })).toBeVisible()
  await expect(page.getByRole('table').last().getByText(source.nagios_host_name, { exact: true })).toHaveCount(0)
  const row = section.getByRole('row').filter({ hasText: `ID ${sourceId} ·` })
  await row.getByRole('button', { name: 'Review', exact: true }).click()
  let drawer = page.getByRole('dialog', { name: 'Review device identity', exact: true })
  await expect(drawer).toBeFocused()
  await expect(drawer.getByText('Identity confidence:')).toBeVisible()
  await drawer.getByRole('button', { name: 'Load address history' }).first().click()
  await expect(drawer.getByText(/Previous|Current/).first()).toBeVisible()
  // Real preference changes and reloads verify both themes with the application CSS.
  const preferences = await (await page.request.get(`${base}/api/user/preferences`)).json()
  for (const theme of ['light', 'dark']) {
    expect((await page.request.put(`${base}/api/user/preferences`, { data: { theme } })).ok()).toBeTruthy()
    await page.reload()
    await row.getByRole('button', { name: 'Review', exact: true }).click()
    drawer = page.getByRole('dialog', { name: 'Review device identity', exact: true })
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
    await expect(drawer).toBeVisible()
    await expect(drawer).toBeFocused()
    await page.screenshot({ path: `test-results/issue164-${theme}${expectWarning ? '-warning' : ''}.png` })
  }
  await page.setViewportSize({ width: 560, height: 850 })
  await expect(drawer).toBeVisible()
  const overflows = await drawer.evaluate(el => el.scrollWidth > el.clientWidth)
  expect(overflows).toBeFalsy()
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.keyboard.press('Escape')
  await expect(drawer).toHaveCount(0)
  await expect(row.getByRole('button', { name: 'Review', exact: true })).toBeFocused()
  const afterCancel = (await (await page.request.get(`${base}/api/system/discover/review`)).json()).data.items
  expect(afterCancel.map((r: { id: number }) => r.id)).toEqual(before.map((r: { id: number }) => r.id))
  if (process.env.ISSUE164_CHECK_NOTICE === '1') {
    await page.getByRole('button', { name: 'Filter', exact: true }).click()
    await page.getByRole('button', { name: 'Not monitored', exact: true }).click()
    await page.getByRole('table').last().getByRole('button', { name: source.nagios_host_name, exact: true }).click()
    const notice = page.getByRole('region', { name: 'Device identity notice', exact: true })
    await expect(notice.getByText('This device needs identity review')).toBeVisible()
    await notice.getByRole('button', { name: 'Review', exact: true }).click()
    await expect(page.getByRole('dialog', { name: 'Review device identity', exact: true })).toBeVisible()
    await page.keyboard.press('Escape')
    await page.getByRole('button', { name: 'Close', exact: true }).click()
    await page.getByRole('button', { name: 'Filter', exact: true }).click()
    await page.getByRole('button', { name: 'Monitored', exact: true }).click()
  }
  await row.getByRole('button', { name: 'Review', exact: true }).click()
  drawer = page.getByRole('dialog', { name: 'Review device identity', exact: true })
  await expect(drawer.getByLabel('Device record to keep')).toHaveValue('')
  await expect(drawer.getByLabel('Duplicate record to merge')).toHaveValue('')
  // Generated IP-reuse reviews have only the previous holder: find the new record.
  await drawer.getByLabel('Search discovered devices').fill(targetId!)
  await drawer.getByRole('button', { name: 'Search', exact: true }).click()
  await drawer.getByRole('button', { name: new RegExp(`Add .*ID ${targetId} ·`) }).click()
  await drawer.getByLabel('Device record to keep').selectOption(targetId!)
  await drawer.getByLabel('Duplicate record to merge').selectOption(sourceId!)
  await page.screenshot({ path: `test-results/issue164-comparison${expectWarning ? '-warning' : ''}.png` })
  await drawer.getByRole('button', { name: 'Review merge', exact: true }).click()
  const confirmation = page.getByRole('dialog', { name: 'Confirm device merge', exact: true })
  await expect(confirmation).toBeFocused()
  for (const phrase of [/retains its current address/, /leaves monitoring/, /Target records take precedence/, /Historical monitoring snapshots/, /No undo/]) await expect(confirmation.getByText(phrase)).toBeVisible()
  await page.keyboard.press('Shift+Tab')
  await expect(confirmation.getByRole('button', { name: 'Merge duplicate', exact: true })).toBeFocused()
  let submissions = 0
  page.on('request', request => { if (request.method() === 'POST' && request.url().endsWith(`/hosts/${sourceId}/merge`)) submissions++ })
  const responsePromise = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/hosts/${sourceId}/merge`))
  await confirmation.getByRole('button', { name: 'Merge duplicate', exact: true }).click()
  const response = await responsePromise
  expect(response.ok()).toBeTruthy()
  expect((await response.json()).data.config_ok).toBe(!expectWarning)
  await expect(page.getByText('No device identity issues need review.')).toBeVisible()
  await expect(page.getByText(expectWarning ? /Merge saved.*Nagios configuration warning/ : 'Merge saved.', { exact: !expectWarning }).first()).toBeVisible()
  expect(submissions).toBe(1)
  await expect(page.getByRole('dialog')).toHaveCount(0)
  const sourceAfter = (await (await page.request.get(`${base}/api/system/hosts/${sourceId}/identifiers`)).json()).data.device
  const targetAfter = (await (await page.request.get(`${base}/api/system/hosts/${targetId}/identifiers`)).json()).data.device
  expect(sourceAfter.state).toBe('MERGED')
  expect(targetAfter.id).toBe(targetBefore.id)
  expect(targetAfter.ip_address).toBe(targetBefore.ip_address)
  expect((await (await page.request.get(`${base}/api/system/discover/review`)).json()).data.items).toHaveLength(0)
  await page.screenshot({ path: `test-results/issue164-${expectWarning ? 'warning' : 'success'}.png` })
  await page.request.put(`${base}/api/user/preferences`, { data: { theme: preferences.theme } })
})
