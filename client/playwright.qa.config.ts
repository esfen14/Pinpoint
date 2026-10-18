import { defineConfig, devices } from '@playwright/test';
import { selection } from './qa/selection.mjs';

// Source adapters only. A future reviewed launcher must supply this environment
// inside the existing no-network container after verifying scope and lab ownership.
// No default case selection, auth setup dependency or existing project is inherited.
const scope = selection(process.env);
export default defineConfig({
  testDir: './e2e',
  testMatch: /qa-permissions\.lab\.spec\.ts$/,
  grep: scope.grep,
  forbidOnly: true,
  failOnFlakyTests: true,
  fullyParallel: false,
  workers: 1,
  maxFailures: 1,
  globalTimeout: scope.ids.length * 90000,
  retries: 0,
  timeout: 60000,
  expect: { timeout: 10000 },
  outputDir: scope.artifacts,
  reporter: [['json', { outputFile: scope.report }]],
  metadata: { currentCaseIds: scope.ids, mode: 'scripted automation' },
  use: {
    ...devices['Desktop Chrome'],
    baseURL: 'http://127.0.0.1:18080',
    trace: 'off', screenshot: 'off', video: 'off',
    actionTimeout: 10000, navigationTimeout: 15000,
  },
  projects: [{ name: 'qa-permissions' }],
});
