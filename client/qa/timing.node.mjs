import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

test('pinned worker duration excludes a separately timed beforeAll slot', () => {
  const dir = mkdtempSync(join(tmpdir(), 'pinpoint-qa-clock-'));
  try {
    const playwright = new URL('../node_modules/@playwright/test/index.mjs', import.meta.url).href;
    const reportPath = join(dir, 'results.json');
    const config = join(dir, 'timing.config.mjs');
    writeFileSync(config, `import { defineConfig } from ${JSON.stringify(playwright)};
      process.umask(0o077);
      export default defineConfig({ testDir: ${JSON.stringify(dir)}, testMatch: 'timing.spec.mjs',
        outputDir: ${JSON.stringify(join(dir, 'artifacts'))}, workers: 1, retries: 0,
        metadata: { syntheticClockFixture: true },
        reporter: [['json', { outputFile: ${JSON.stringify(reportPath)} }]],
        projects: [{ name: 'offline-clock' }] });`);
    // No acceptance module, credentials, page, browser, network or lab fixture.
    writeFileSync(join(dir, 'timing.spec.mjs'), `import { test } from ${JSON.stringify(playwright)};
      test.beforeAll(async () => { await new Promise(resolve => setTimeout(resolve, 200)); });
      test('synthetic clock semantics only', async ({}, info) => {
        await info.attach('synthetic-clock', { contentType: 'application/json',
          body: JSON.stringify({ at: new Date().toISOString() }) });
      });`);
    const result = spawnSync(process.execPath, ['node_modules/@playwright/test/cli.js', 'test', `--config=${config}`], {
      cwd: resolve(import.meta.dirname, '..'), encoding: 'utf8', timeout: 30000,
      env: { ...process.env, CI: '1' },
    });
    assert.equal(result.status, 0, result.stderr + result.stdout);
    const report = JSON.parse(readFileSync(reportPath, 'utf8'));
    assert.equal(report.config.version, '1.64.0');
    assert.equal(report.config.metadata.syntheticClockFixture, true);
    assert.deepEqual(report.config.projects.map(p => p.name), ['offline-clock']);
    const specs = suites => suites.flatMap(s => [...(s.specs ?? []), ...specs(s.suites ?? [])]);
    const selected = specs(report.suites);
    assert.equal(selected.length, 1);
    const attempts = selected[0].tests[0].results;
    assert.equal(attempts.length, 1);
    const attempt = attempts[0];
    const observation = JSON.parse(Buffer.from(attempt.attachments[0].body, 'base64'));
    assert.ok(Date.parse(observation.at) > Date.parse(attempt.startTime) + attempt.duration,
      'wall observation can follow startTime + selected-slot duration');
    assert.ok(report.stats.duration > attempt.duration);
    assert.equal(attempt.retry, 0);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
