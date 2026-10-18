/** Exact current-case selection for the broader module adapter source suite. */
import { lstatSync, realpathSync, readdirSync } from 'node:fs';
import { isAbsolute, resolve, join } from 'node:path';

export const CASES = Object.freeze({
  'TC-ACC-10': 'TC-ACC-10: Add User uses the default role',
  'TC-ACC-08': 'TC-ACC-08: "Send this user email alerts" depends on permission',
  'TC-ROL-04': 'TC-ROL-04: A dashboard-only user is limited to the Dashboard',
  'TC-DI-02': 'TC-DI-02: Port groups and their order',
  'TC-DI-03': 'TC-DI-03: One reason per port',
  'TC-DI-08': 'TC-DI-08: The Checked by line',
  'TC-DASH-07': 'TC-DASH-07: "No data" instead of blank cards',
});

export function moduleSelection(env) {
  const ids = (env.PINPOINT_QA_CASES ?? '').split(',');
  if (!ids.length || new Set(ids).size !== ids.length || ids.some((id) => !Object.hasOwn(CASES, id))) {
    throw new Error('PINPOINT_QA_CASES must explicitly select unique supported module case IDs');
  }
  const dir = env.PINPOINT_QA_RUN_DIR;
  if (!dir || !isAbsolute(dir)) throw new Error('An absolute private PINPOINT_QA_RUN_DIR is required');
  const stat = lstatSync(dir);
  if (!stat.isDirectory() || stat.isSymbolicLink() || realpathSync(dir) !== resolve(dir)
    || typeof process.getuid !== 'function' || stat.uid !== process.getuid() || (stat.mode & 0o077) !== 0) {
    throw new Error('The run directory must be a same-owner private directory without symlinks');
  }
  if (readdirSync(dir).length !== 0) throw new Error('Run directory is not empty; preserve prior evidence and use a new run');
  const escape = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return {
    ids,
    grep: new RegExp(`(?:^| )(?:${ids.map((id) => escape(CASES[id])).join('|')})$`),
    report: join(dir, 'results.json'),
    artifacts: join(dir, 'artifacts'),
  };
}
