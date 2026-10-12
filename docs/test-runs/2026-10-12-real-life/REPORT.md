# Test run: {{SLUG}}

| | |
|---|---|
| Date | {October 12, 2026} |
| Commit tested | `{{COMMIT}}` |
| Plan | {Functional Suitability} |
| Case | Result | Notes (what was observed; evidence file name) | Issue |

| Plan | {Interaction Capability} |
| Case | Result | Notes (what was observed; evidence file name) | Issue |
| J1 - 05 | PASS | Notes (what was observed; evidence file name) | NONE |
| J2 - 06 | PASS | Notes (what was observed; evidence file name) | NONE |
| J5 - 10 | FAIL | Notes (what was observed; evidence file name) |  -- |
| J7 - 05 | PASS | Notes (what was observed; evidence file name) | NONE |
| J8 - 05 | PASS | Notes (what was observed; evidence file name) | NONE |
| J9 - 08 | PASS | Notes (what was observed; evidence file name) | NONE |
| Plan | {Performance Efficiency} |
| Plan | {Reliability} |
| Plan | {Security} |
| Tester |{Lijan Daffodil Bagang}|
| Environment | OS and version, Nagios version, lab network range, database state (fresh / upgraded copy) |
| Raw evidence | Host and path of the harness `output_root` (not committed) |

## Result

**Overall: Pass / Fail / Partial.** One or two sentences: what was covered and
what blocks sign-off.

Totals: Pass 0, Fail 0, Blocked 0, Skipped 0.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| | Pass / Fail / Blocked / Skipped | | |

## Deviations from the plan

Cases changed, reordered or skipped, and why.

## Follow-up

- Defects found: link each issue. Do not describe defects only here.
- Cases to repeat in the next run:

## Sanitization checklist

- [ ] No passwords, tokens, keys, SNMP communities or private key paths
- [ ] No addresses outside the documented lab range
- [ ] Evidence is referenced by name and location, not pasted



Note:
TEST
[PASS]
Interaction Capability
- J1-05
- J2 - 06
- J7 - 05
- J8 - 05
- J9 - 08

Functional Suitability
-
Performance Efficiency
- PT - 03
- 
Reliability
- J2 - 02
- J2 - 05
- J2 - 10

Security
- J1 - 03
- J9 - 05
- J9 - 10
- J9 - 12
- X2 - 01
- 

---

[FAIL]
Interaction Capability
- J5 -10 error: sudo a password is required
- J9 - 06 the edited user does not sign out after saving the editing changes
-

Functional Suitability
-
Performance Efficiency
-
Reliability
-
Security
- J9 - 07

---

[PENDING]
Interaction Capability
- J7 - 04
- J8 - 07

Functional Suitability
-
Performance Efficiency
-
Reliability
- J3 - 08
- 
Security
-

[NOTES]
- add functions to the 3 dot option in the overview, if there is no use, remove
