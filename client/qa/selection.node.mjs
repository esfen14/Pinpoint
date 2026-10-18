import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, chmodSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { selection, CASES } from './selection.mjs';

function fixture(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'pinpoint-qa-selection-'));
  chmodSync(dir, 0o700);
  try { fn(dir); } finally { rmSync(dir, { recursive: true, force: true }); }
}

test('requires explicit known nonduplicate case IDs and private run directory', () => {
  fixture((dir) => {
    const env = { PINPOINT_QA_CASES: 'TC-SS-04', PINPOINT_QA_RUN_DIR: dir };
    assert.deepEqual(selection(env).ids, ['TC-SS-04']);
    for (const ids of ['', 'TC-UNKNOWN-01', 'TC-SS-04,TC-SS-04', 'TC-SS-04,']) {
      assert.throws(() => selection({ ...env, PINPOINT_QA_CASES: ids }));
    }
    assert.throws(() => selection({ ...env, PINPOINT_QA_RUN_DIR: 'relative' }));
    chmodSync(dir, 0o755);
    assert.throws(() => selection(env));
  });
});

test('rejects symlinked evidence directory and reused result location', () => {
  fixture((dir) => {
    const link = join(dir, 'link'); symlinkSync(dir, link);
    assert.throws(() => selection({ PINPOINT_QA_CASES: 'TC-SS-04', PINPOINT_QA_RUN_DIR: link }));
    assert.throws(() => selection({ PINPOINT_QA_CASES: 'TC-SS-04', PINPOINT_QA_RUN_DIR: dir }));
  });
});

function collect(ids, dir) {
  return spawnSync(process.execPath, ['node_modules/@playwright/test/cli.js', 'test',
    '--config=playwright.qa.config.ts', '--list', '--reporter=json'], {
    cwd: resolve(import.meta.dirname, '..'), encoding: 'utf8',
    env: { ...process.env, CI: '1', PINPOINT_QA_CASES: ids, PINPOINT_QA_RUN_DIR: dir },
    timeout: 30000,
  });
}
function titles(suites) {
  return suites.flatMap((suite) => [...(suite.specs ?? []).map((spec) => spec.title), ...titles(suite.suites ?? [])]);
}

test('offline Playwright collection selects exactly one current case, with no setup projects', () => {
  fixture((dir) => {
    const result = collect('TC-SS-04', dir);
    assert.equal(result.status, 0, result.stderr + result.stdout);
    const report = JSON.parse(result.stdout);
    assert.deepEqual(titles(report.suites), [CASES['TC-SS-04']]);
    assert.equal(report.config.workers, 1);
    assert.deepEqual(report.config.projects.map((p) => p.name), ['qa-permissions']);
    assert.equal(report.config.projects[0].retries, 0);
    assert.deepEqual(report.config.filteredProjects[0].dependencies, []);
  });
});

test('offline collection can select all five adapters without executing login or assertions', () => {
  fixture((dir) => {
    const result = collect(Object.keys(CASES).join(','), dir);
    assert.equal(result.status, 0, result.stderr + result.stdout);
    assert.deepEqual(titles(JSON.parse(result.stdout).suites).sort(), Object.values(CASES).sort());
  });
});

test('offline collection rejects missing/unknown selection rather than launching default projects', () => {
  fixture((dir) => {
    for (const ids of ['', 'TC-NCPA-09']) assert.notEqual(collect(ids, dir).status, 0);
  });
});
