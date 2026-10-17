# Issue #189: Deterministic backfilled NCPA configuration comparison

Branch: `issue-189-deterministic-ncpa-config`
Status: in-progress

## Finish condition

- [ ] A deterministic regression forces two renders across a minute boundary and passes without hiding real configuration changes.
- [ ] Normalize the generated timestamp using the existing whitespace-tolerant convention or control time in this test.
- [ ] Focused configuration tests and `scripts/verify.sh backend` pass.

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Reproduce minute-boundary failure deterministically | 1 | Backfill regression with mocked generator clock; observe failure before normalization fix |
| Ignore only timestamp while retaining configuration differences | 1, 2 | Existing whitespace-tolerant timestamp regex; actual changed-port render compares unequal |
| Focused and backend checks pass | 3 | Focused config modules; scripts/verify.sh backend |

## Plan

1. [ ] Update `server/tests/unit/test_create_host_cfg.py`: first force adjacent-minute renders and observe the existing assertion fail; then use the existing timestamp convention and prove a real port change remains visible. Run focused configuration modules and backend verification.
2. [ ] Document deterministic comparison coverage in `spec files/Engineering_Standards.md` and `server/tests/README.md`; re-read issue, verify docs and all stages, remove progress, open PR and check CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| Intake | Issue requirements fully covered; isolated worktree from origin/main | gh issue view 189; git status | Ready for test-first change |

## State for the next session

- Last check run (exact command): `gh issue view 189 --json number,title,body,comments,state`
- Result (first failing lines, or "green"): green; open issue with three complete finish items.
- Hypothesis: The test's single-space timestamp regex misses the generator's multi-space header.
- Next action (one specific step, not "continue"): Mock the generator datetime across 19:59 to 20:00 in the backfill regression and run it before fixing normalization.

## Decisions and notes

- No production behavior changes; only tests and testing documentation. Sensitive generation code is inspected but will not be edited.
- Use an isolated checkout at `/tmp/pinpoint-issue-189`; original checkout has unrelated dev-script edits.
- Existing pinned dependencies copied into independent worktree directories; no new dependency required.
- No live labs or integration tests are in scope.
