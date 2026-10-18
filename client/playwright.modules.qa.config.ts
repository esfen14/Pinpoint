import { defineConfig, devices } from '@playwright/test';
import { moduleSelection } from './qa/module-selection.mjs';

// Exact source selection for the supervised module pilot. Direct legacy
// playwright-lab dispatch remains blocked; only qa_pilot.py run may execute the
// six complete read-only mappings with reviewed cards and a separate start.
const scope = moduleSelection(process.env);
export default defineConfig({
  testDir: './e2e',
  testMatch: /qa-modules-2-9\.lab\.spec\.ts$/,
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
  projects: [{ name: 'qa-modules-2-9' }],
});
