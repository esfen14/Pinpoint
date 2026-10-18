import assert from 'node:assert/strict';
import { chmodSync, mkdtempSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { CASES, moduleSelection } from './module-selection.mjs';

function fixture(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'pinpoint-module-selection-'));
  chmodSync(dir, 0o700);
  try { fn(dir); } finally { rmSync(dir, { recursive: true, force: true }); }
}

test('requires explicit unique supported case IDs and a private run directory', () => {
  fixture((dir) => {
    const env = { PINPOINT_QA_CASES: 'TC-ACC-08', PINPOINT_QA_RUN_DIR: dir };
    assert.deepEqual(moduleSelection(env).ids, ['TC-ACC-08']);
    for (const ids of ['', 'TC-UNKNOWN-01', 'TC-ACC-08,TC-ACC-08', 'TC-ACC-08,']) {
      assert.throws(() => moduleSelection({ ...env, PINPOINT_QA_CASES: ids }));
    }
    assert.throws(() => moduleSelection({ ...env, PINPOINT_QA_RUN_DIR: 'relative' }));
    chmodSync(dir, 0o755);
    assert.throws(() => moduleSelection(env));
  });
});

test('rejects symlinked and reused run directories', () => {
  fixture((dir) => {
    const link = join(dir, 'linked');
    symlinkSync(dir, link);
    const env = { PINPOINT_QA_CASES: 'TC-ROL-04', PINPOINT_QA_RUN_DIR: link };
    assert.throws(() => moduleSelection(env));
    assert.throws(() => moduleSelection({ ...env, PINPOINT_QA_RUN_DIR: dir }));
  });
});

function collect(ids, dir) {
  return spawnSync(process.execPath, ['node_modules/@playwright/test/cli.js', 'test',
    '--config=playwright.modules.qa.config.ts', '--list', '--reporter=json'], {
    cwd: resolve(import.meta.dirname, '..'), encoding: 'utf8',
    env: { ...process.env, CI: '1', PINPOINT_QA_CASES: ids, PINPOINT_QA_RUN_DIR: dir },
    timeout: 30000,
  });
}

function titles(suites) {
  return suites.flatMap((suite) => [...(suite.specs ?? []).map((spec) => spec.title), ...titles(suite.suites ?? [])]);
}

test('offline collection selects exactly the requested module adapter with no setup project', () => {
  fixture((dir) => {
    const result = collect('TC-ROL-04', dir);
    assert.equal(result.status, 0, result.stderr + result.stdout);
    const report = JSON.parse(result.stdout);
    assert.deepEqual(titles(report.suites), [CASES['TC-ROL-04']]);
    assert.equal(report.config.workers, 1);
    assert.deepEqual(report.config.projects.map((project) => project.name), ['qa-modules-2-9']);
    assert.equal(report.config.projects[0].retries, 0);
    assert.deepEqual(report.config.filteredProjects[0].dependencies, []);
  });
});

test('offline collection selects exactly TC-ACC-10', () => {
  fixture((dir) => {
    const result = collect('TC-ACC-10', dir);
    assert.equal(result.status, 0, result.stderr + result.stdout);
    assert.deepEqual(titles(JSON.parse(result.stdout).suites), [CASES['TC-ACC-10']]);
  });
});

test('offline collection selects only source-reviewed module adapters', () => {
  fixture((dir) => {
    const result = collect(Object.keys(CASES).join(','), dir);
    assert.equal(result.status, 0, result.stderr + result.stdout);
    assert.deepEqual(titles(JSON.parse(result.stdout).suites).sort(), Object.values(CASES).sort());
  });
});

test('offline collection rejects missing and unknown module selections', () => {
  fixture((dir) => {
    assert.notEqual(collect('', dir).status, 0);
    assert.notEqual(collect('TC-NH-99', dir).status, 0);
  });
});
