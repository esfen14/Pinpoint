import { test, expect } from '@playwright/test'

// Disposable Staff account has no system.history permission. No live state is changed.
test('issue 133: History is denied without permission', async ({ page }) => {
  await page.goto('/history')
  await expect(page).toHaveURL('/settings')
  await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible()
  const response = await page.request.get('/api/system/history/alerts?preset=24h')
  expect(response.status()).toBe(403)
})
