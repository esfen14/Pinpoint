# Test run: {{SLUG}}

| | |
|---|---|
| Date | {{DATE}} |
| Commit tested | `{{COMMIT}}` |
| Plan | {{PLAN}} |
| Tester / executor mode | Human manual / AI-assisted / scripted / mixed; name actual contributors |
| Catalog revision and SHA-256 | |
| Queue / set / session / batch | |
| Deployed application / installer revision | Verify separately from this checkout |
| Baseline / preflight / restoration | Record actual observations and approved recovery |
| Start / end / time zone | |
| Environment | OS and version, Nagios version, lab network range, database state (fresh / upgraded copy) |
| Raw evidence | Host and path of the harness `output_root` (not committed) |

## Result

**Overall: Pass / Fail / Partial.** One or two sentences: what was covered and
what blocks sign-off.

Totals (unique TC): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial; link reviewed mappings separately.
Attempts and setup operations are not extra unique cases. Historical credit is not a new execution.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| | Pass / Fail / Partially Pass / Blocked / Inconclusive / Not run | | |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| | E1 | | | | |

Include E2E step outcomes, effective timings and all diagnostic attempts. No Pass
unless every required item is observed on the stated revision and cleanup is verified.
An inconclusive or partial run never silently replaces the earlier failure.

## Deviations from the plan

Cases changed, reordered or skipped, and why.

## Follow-up

- Defects found: link each issue. Do not describe defects only here.
- Cases to repeat in the next run:

## Sanitization checklist

- [ ] No passwords, tokens, keys, SNMP communities or private key paths
- [ ] No addresses outside the documented lab range
- [ ] Evidence is referenced by name and location, not pasted
