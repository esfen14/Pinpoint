# QA-loop planted-failure run

| | |
|---|---|
| Date | 2026-10-11 |
| Commit tested | `1bae5171` plus one uncommitted scratch assertion, removed after the repeat |
| Plan | Issue #63 QA-loop dry-run acceptance |
| Tester | Codex, under the lab owner's explicit release |
| Environment | Running VM appliance; administrator Chromium project inside the Docker `--network none` runner |
| Raw evidence | Ignored `client/test-results/` on the test host; no trace, screenshot, video or auth state committed |

## Result

**Overall: Pass for the planted-failure workflow.** The same deliberately false
J2-labelled assertion failed twice, the application Dashboard loaded on both attempts,
and the scratch assertion was removed. This was a harness test, not a Pinpoint defect.

Totals: expected synthetic failures 2, inconsistent repeats 0, product defects 0.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| J2-01 synthetic workflow probe | Pass | Both runs reported the administrator setup passing and the intentionally nonexistent heading failing with `element(s) not found`. The scratch spec and temporary config inclusion were then removed. | None: deliberately planted harness evidence, not a product failure |

## Deviations from the plan

The case ID labels the workflow probe only. No J2-01 product expectation was executed,
so the real J2-01 traceability row was not changed. The earlier instruction to file a
synthetic `qa-found` issue was corrected: issue tracking is for observed application
defects, not an assertion deliberately written to fail.

## Follow-up

- No product issue or retest is required.
- The broader J2/J3 acceptance remains recorded separately as partial.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by location, not pasted
