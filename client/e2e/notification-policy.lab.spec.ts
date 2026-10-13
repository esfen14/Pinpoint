import { test, expect } from '@playwright/test'

// Opt-in Docker lab check, deliberately outside the configured smoke projects.
test('administrator saves and reloads notification policy in the browser', async ({ page }) => {
  await page.goto('http://127.0.0.1:5173/login')
  await page.getByPlaceholder('Enter your email').fill(process.env.LAB_ADMIN_EMAIL ?? 'admin@test.com')
  await page.locator('input[type="password"]').fill(process.env.LAB_ADMIN_PASSWORD ?? '')
  await page.getByRole('button', { name: /sign in|log in/i }).click()
  await expect(page).not.toHaveURL(/\/login$/)
  await page.goto('http://127.0.0.1:5173/settings')
  await page.getByRole('button', { name: 'System', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Notification policy' })).toBeVisible()
  await page.getByRole('button', { name: 'Add quiet hours' }).click()
  await page.getByLabel('Start 1').fill('09:00')
  await page.getByLabel('End 1').fill('10:00')
  await page.getByRole('button', { name: 'Save Changes' }).last().click()
  await expect(page.getByText('Policy saved.')).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: 'System', exact: true }).click()
  await expect(page.getByLabel('Start 1')).toHaveValue('09:00')
  await page.getByRole('button', { name: 'Remove quiet hours 1' }).click()
  await page.getByRole('button', { name: 'Save Changes' }).last().click()
  await expect(page.getByText('Policy saved.')).toBeVisible()
})
