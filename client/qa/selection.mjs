/** Exact current-case selection and private, non-overwriting evidence paths. No browser/lab access. */
import { lstatSync, realpathSync, readdirSync } from 'node:fs';
import { isAbsolute, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const CASES = Object.freeze({
  'TC-ACC-09': 'TC-ACC-09: The accounts page needs permission',
  'TC-NCPA-08': 'TC-NCPA-08: NCPA Deployment needs permission',
  'TC-SS-04': 'TC-SS-04: System Status needs permission',
  'TC-HIS-01': 'TC-HIS-01: History needs permission',
  'TC-RPT-07': 'TC-RPT-07: Reports need permission',
  'TC-LOG-05': 'TC-LOG-05: System Logs need permission',
  'TC-PLG-07': 'TC-PLG-07: Plugins need permission',
});

export function selection(env) {
  const ids = (env.PINPOINT_QA_CASES ?? '').split(',');
  if (!ids.length || new Set(ids).size !== ids.length || ids.some((id) => !Object.hasOwn(CASES, id))) {
    throw new Error('PINPOINT_QA_CASES must explicitly select unique supported current case IDs');
  }
  const dir = env.PINPOINT_QA_RUN_DIR;
  if (!dir || !isAbsolute(dir)) throw new Error('An absolute private PINPOINT_QA_RUN_DIR is required');
  const stat = lstatSync(dir);
  if (!stat.isDirectory() || stat.isSymbolicLink() || realpathSync(dir) !== resolve(dir)
    || typeof process.getuid !== 'function' || stat.uid !== process.getuid() || (stat.mode & 0o077) !== 0) {
    throw new Error('The run directory must be a same-owner private directory without symlinks');
  }
  const entries = readdirSync(dir);
  if (entries.length) {
    // Playwright creates outputDir before its real IPC worker reloads this
    // configuration. Environment markers alone must not permit evidence reuse.
    const workerEntry = fileURLToPath(new URL('../node_modules/playwright/lib/worker/workerProcessEntry.js', import.meta.url));
    const worker = typeof process.send === 'function' && /^\d+$/.test(env.TEST_WORKER_INDEX ?? '')
      && env.TEST_PARALLEL_INDEX === '0' && process.argv[1]
      && realpathSync(process.argv[1]) === realpathSync(workerEntry);
    if (!worker || entries.length !== 1 || entries[0] !== 'artifacts') {
      throw new Error('Run directory is not empty; preserve previous evidence and use a new run');
    }
    const artifacts = join(dir, 'artifacts');
    const output = lstatSync(artifacts);
    if (!output.isDirectory() || output.isSymbolicLink() || output.uid !== process.getuid()
      || (output.mode & 0o077) !== 0 || realpathSync(artifacts) !== resolve(artifacts)) {
      throw new Error('Worker output must remain a private owned directory');
    }
  }
  // Titles are fixed literals, but escape regex syntax to keep selection exact.
  const escape = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return { ids, grep: new RegExp(`(?:^| )(?:${ids.map((id) => escape(CASES[id])).join('|')})$`),
    report: join(dir, 'results.json'), artifacts: join(dir, 'artifacts') };
}
