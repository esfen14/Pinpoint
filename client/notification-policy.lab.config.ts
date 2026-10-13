import { defineConfig, devices } from '@playwright/test'
export default defineConfig({ testDir: './e2e', testMatch: 'notification-policy.lab.spec.ts', projects: [{ name: 'lab', use: { ...devices['Desktop Chrome'] } }], reporter: 'line', use: { trace: 'off', screenshot: 'off', video: 'off' } })
