/** Opt-in browser comparison against service_reports_core.py --serve only. */
import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'

const origin = process.env.ISSUE198_LAB_URL
// The fixture has a temporary local login; never point these tests at production.
test.skip(origin !== 'http://127.0.0.1:19198', 'Requires the dedicated isolated Core/browser fixture on loopback port 19198.')

for (const [label, slug, title] of [
  ['Network Services', 'network-services', 'Network Services Report'],
  ['Device Services', 'device-services', 'Device Services Report'],
]) {
  test(`${label}: native outage availability, coverage, current context and all exports`, async ({ page, context }) => {
    await context.addInitScript(() => { window.print = () => {} })
    await page.goto(origin + '/reports')
    await expect(page.getByRole('button', { name: 'Run Report', exact: true })).toBeEnabled()
    const loaded = page.waitForResponse(r => r.url().includes('/api/system/report/'+slug+'?') && r.status() === 200)
    await page.getByRole('button', { name: label, exact: true }).click()
    await loaded
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible()
    await page.getByRole('combobox').selectOption('custom')
    await page.getByLabel('Report start date').fill('2024-01-01')
    await page.getByLabel('Report end date').fill('2024-01-01')
    const rerun = page.waitForResponse(r => r.url().includes('/api/system/report/'+slug+'?period=custom') && r.status() === 200)
    await page.getByRole('button', { name: 'Run Report', exact: true }).click()
    const response = await rerun
    const data = (await response.json()).data
    expect(data.summary.critical_seconds).toBeGreaterThan(0)
    expect(data.summary.uptime_pct).toBeLessThan(100)
    expect(data.summary.no_recorded_data_seconds).toBe(0)
    expect(JSON.stringify(data)).not.toMatch(/snapshot/i)
    await expect(page.getByText(/Availability during recorded time =/)).toBeVisible()
    await expect(page.getByText(/Current status: observed/)).toBeVisible()
    await expect(page.getByRole('columnheader', { name: 'Recorded time (seconds)', exact: true })).toBeVisible()
    await expect(page.getByRole('columnheader', { name: 'No recorded data (seconds)', exact: true })).toBeVisible()
    await expect(page.locator('tbody')).toContainText(String(data.summary.uptime_pct))
    for (const format of ['CSV', 'XLS']) {
      await page.getByRole('button', { name: 'Export', exact: true }).click()
      const downloading = page.waitForEvent('download')
      await page.getByRole('button', { name: format, exact: true }).click()
      const download = await downloading
      const path = await download.path()
      const body = await readFile(path!, 'utf8')
      expect(body).toContain('Recorded time (seconds)')
      expect(body).toContain('No recorded data (seconds)')
      expect(body).not.toMatch(/snapshot/i)
      expect(body).toContain(String(data.summary.uptime_pct))
    }
    await page.getByRole('button', { name: 'Export', exact: true }).click()
    const opening = page.waitForEvent('popup')
    await page.getByRole('button', { name: 'PDF', exact: true }).click()
    const popup = await opening
    await expect(popup.getByRole('columnheader', { name: 'Recorded time (seconds)', exact: true })).toBeVisible()
    await expect(popup.locator('tbody')).toContainText(String(data.summary.uptime_pct))
    const pdf = await popup.pdf()
    expect(pdf.length).toBeGreaterThan(1000)
    await popup.close()
    console.log(JSON.stringify({ view: slug, availability: data.summary.uptime_pct, known_seconds: data.summary.known_seconds,
      critical_seconds: data.summary.critical_seconds, exports: ['CSV', 'XLS', 'PDF'], result: 'pass' }))
  })
}
