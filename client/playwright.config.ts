import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['json', { outputFile: 'test-results/playwright-results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:18080',
    // Login artifacts can expose passwords; opt-in capture must never cover setup.
    trace: 'off',
    screenshot: 'off',
    video: 'off',
  },
  projects: [
    {
      name: 'setup-admin',
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: 'setup-restricted',
      testMatch: /auth\.restricted\.setup\.ts/,
    },
    {
      name: 'admin',
      testMatch: /smoke\.admin\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/admin.json',
      },
      dependencies: ['setup-admin'],
    },
    {
      name: 'restricted',
      testMatch: /smoke\.restricted\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/restricted.json',
      },
      dependencies: ['setup-restricted'],
    },
  ],
});
