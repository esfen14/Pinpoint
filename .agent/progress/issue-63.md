# Issue #63: Complete QA loop readiness

Branch: `issue-63-qa-loop-readiness`
Status: in-progress

## Finish condition

- [ ] Complete traceability including BB cases, spec headings and observed evidence; tested drift checker.
- [ ] Resumable qa-run and thin adapters with consistent safety and retest rules.
- [ ] Labels, draft severity rubric and enforceable lab/browser boundaries.
- [ ] Exact-pinned Playwright, credential-safe role setup, Vitest exclusion and both-role live smoke passes.
- [ ] Actual planted-failure J2/J3 dry run and sanitized report.
- [ ] Full verification and CI green; retain draft while live checks pending.

## Plan

- [ ] Restore accurate state; test and fix Playwright credential/artifact defaults.
- [ ] Test-first complete traceability checker and matrix; integrate docs drift check.
- [ ] Complete qa-run progress validation, safety, issue search and merged-fix retest semantics.
- [ ] Complete role setup, forced-change handling, mock validation and teammate installation instructions.
- [ ] After owner releases lab, execute live role smoke and real dry run.
- [ ] Verify all and update PR checklist with only observed results.

## Round log

| Round | Change | Check | Result |
|---|---|---|---|
| Recovery 1 | Restore progress; exact pin, fail-closed credentials, ignored auth/artifacts and disabled login captures; expand qa-run | `python3 -I scripts/test_playwright_safety.py` red then green (4 tests); `scripts/verify.sh docs` | passed offline checks only; live lab untouched |

## State for the next session

- Last check run: `git status --short`
- Result: clean before recovery changes.
- Hypothesis: previous scaffolding lacks security protections and acceptance evidence.
- Next action: Add and run isolated browser configuration safety tests, fix failures without contacting the lab.

## Decisions and notes

Owner currently owns shared VM for #86. Do not access/reset it, discover, deploy,
or mutate accounts/settings. Live role smoke and J2/J3 dry run wait for release.
Fresh reset and Playwright installation were approved earlier, but lab ownership
restriction takes precedence. No PR merges. PR #88 remains draft, based on #62.
Previous fabricated dry-run evidence is withdrawn in its report; it is not a pass.
Full test timeout never means success. Existing checker does not validate headings,
BB rows are absent, role tests have not run, and safety rules are not enforced yet.
