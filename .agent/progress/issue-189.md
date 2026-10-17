# Issue #189: Deterministic backfilled NCPA configuration comparison

Branch: `issue-189-deterministic-ncpa-config`
Status: ready-for-review

## Finish condition

- [x] A deterministic regression forces two renders across a minute boundary and passes without hiding real configuration changes.
- [x] Normalize the generated timestamp using the existing whitespace-tolerant convention or control time in this test.
- [x] Focused configuration tests and `scripts/verify.sh backend` pass.

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Reproduce minute-boundary failure deterministically | 1 | Backfill regression with mocked generator clock; observe failure before normalization fix |
| Ignore only timestamp while retaining configuration differences | 1, 2 | Existing whitespace-tolerant timestamp regex; actual changed-interval render compares unequal |
| Focused and backend checks pass | 3 | Focused config modules; scripts/verify.sh backend |

## Plan

1. [x] Update `server/tests/unit/test_create_host_cfg.py`: first force adjacent-minute renders and observe the existing assertion fail; then use the existing timestamp convention and prove a real check-interval change remains visible. Run focused configuration modules and backend verification.
2. [x] Document deterministic comparison coverage in `spec files/Engineering_Standards.md` and `server/tests/README.md`; re-read issue, verify docs and all stages, remove progress, open PR and check CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Forced 12:19:59 / 12:20:00; observed timestamp-only failure; fixed whitespace-tolerant normalization and retained actual check-interval differences | Focused config modules; scripts/verify.sh backend | 140 focused passed; 3934 backend passed, 14 skipped |
| 2 | Updated engineering test guidance and coverage inventory; re-read unchanged issue and confirmed every requirement | scripts/verify.sh docs; scripts/verify.sh all; git diff --check | green; all stages pass; lint has 0 errors and 30 existing warnings |
| Intake | Issue requirements fully covered; isolated worktree from origin/main | gh issue view 189; git status | Ready for test-first change |

## State for the next session

- Last check run (exact command): `scripts/verify.sh all > test-results/issue-189-all.log 2>&1`
- Result (first failing lines, or "green"): green; verify: all OK; backend 3934 passed / 14 skipped; frontend tests/build pass; lint 0 errors / 30 warnings.
- Hypothesis: Confirmed: single-space regex missed the generated header; whitespace-tolerant normalization resolves it.
- Next action (one specific step, not "continue"): Remove the progress file, commit and push the completed change, create the PR from the template, and confirm CI is green.

## Decisions and notes

- No production behavior changes; only tests and testing documentation. Sensitive generation code is inspected but will not be edited.
- Use an isolated checkout at `/tmp/pinpoint-issue-189`; original checkout has unrelated dev-script edits.
- Existing pinned dependencies copied into independent worktree directories; no new dependency required.
- No live labs or integration tests are in scope.

- The real-change control uses Check_Interval rather than a port change: this directly exercises a rendered directive while leaving the port-backfill scenario intact.

- Issue re-read after implementation: no new comments or changed requirements. All issue requirements are proven; no implementation-status feature gap changed.
