import { test, expect } from '@playwright/test'

test('restricted user cannot read or change host recipients and sees no editor', async ({ page }) => {
  await page.goto('/device-inventory')
  const response = await page.request.get('/api/system/network-health/hosts?per_page=100')
  expect(response.ok()).toBeTruthy()
  const hosts = (await response.json()).data.items as { hostname: string; device_id: number | null; ip_address: string | null }[]
  const host = hosts.find((item) => item.device_id && item.ip_address?.startsWith('10.77.0.'))
  expect(host, 'a discovered lab host is required').toBeTruthy()
  await page.getByRole('button', { name: host!.hostname, exact: true }).click()
  // Wait for detail data, so absence of the editor cannot pass during loading.
  await expect(page.getByRole('heading', { name: 'Timestamps', exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Email alert recipients' })).toHaveCount(0)
  const path = `/api/system/hosts/${host!.device_id}/recipients`
  expect((await page.request.get(path)).status()).toBe(403)
  expect((await page.request.put(path, { data: { recipient_ids: [] } })).status()).toBe(403)
})
