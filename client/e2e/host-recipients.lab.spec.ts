import { test, expect } from '@playwright/test'
import type { HostRecipients } from '../src/types/hostRecipients'

// Opt-in: scripts/playwright-lab --project issue-79-live.
// Uses real APIs and Nagios apply; always restores the original assignment.
test('host recipients save, survive reload, and return to default in the browser', async ({ page }) => {
  test.setTimeout(120_000)
  const response = await page.request.get('/api/system/network-health/hosts?per_page=100')
  expect(response.ok()).toBeTruthy()
  const hosts = (await response.json()).data.items as { hostname: string; device_id: number | null; ip_address: string | null }[]
  const host = hosts.find((item) => item.device_id && item.ip_address?.startsWith('10.77.0.'))
  expect(host, 'a discovered lab host is required').toBeTruthy()
  const path = `/api/system/hosts/${host!.device_id}/recipients`
  const originalResponse = await page.request.get(path)
  expect(originalResponse.ok()).toBeTruthy()
  const original = (await originalResponse.json()).data as HostRecipients
  const eligible = original.users.filter((user) => user.eligible)
  expect(eligible.length, 'at least two opted-in lab accounts are required').toBeGreaterThanOrEqual(2)

  const open = async () => {
    await page.goto('/device-inventory')
    await page.getByRole('button', { name: host!.hostname, exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Email alert recipients' })).toBeVisible()
  }
  try {
    await open()
    const section = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Email alert recipients' }) })
    for (const user of original.users) {
      await section.getByRole('checkbox', { name: `${user.name} (${user.email})`, exact: user.eligible }).setChecked(user.id === eligible[0].id)
    }
    if (!(original.recipient_ids.length === 1 && original.recipient_ids[0] === eligible[0].id)) {
      const saved = page.waitForResponse((r) => r.url().endsWith(path) && r.request().method() === 'PUT')
      await section.getByRole('button', { name: 'Save recipients' }).click()
      const result = await saved
      expect(result.request().postDataJSON()).toEqual({ recipient_ids: [eligible[0].id] })
      expect(result.ok()).toBeTruthy()
      await expect(section.getByText('Alert recipients saved.', { exact: true })).toBeVisible()
    }
    await open()
    await expect(section.getByRole('checkbox', { name: `${eligible[0].name} (${eligible[0].email})`, exact: true })).toBeChecked()
    for (const user of original.users) {
      await section.getByRole('checkbox', { name: `${user.name} (${user.email})`, exact: user.eligible }).uncheck()
    }
    await expect(section.getByText('Using the default recipients: all active accounts with email alerts on.')).toBeVisible()
    await section.getByRole('button', { name: 'Save recipients' }).click()
    await expect(section.getByText('Alert recipients saved.', { exact: true })).toBeVisible()
    await open()
    await expect(section.locator('input[type="checkbox"]:checked')).toHaveCount(0)
    const persisted = await page.request.get(path)
    expect((await persisted.json()).data.recipient_ids).toEqual([])
    await expect(section.getByRole('button', { name: 'Save recipients' })).toBeDisabled()
  } finally {
    const restored = await page.request.put(path, { data: { recipient_ids: original.recipient_ids } })
    expect(restored.ok(), 'restore the original recipient selection').toBeTruthy()
  }
})
