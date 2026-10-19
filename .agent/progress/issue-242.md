# Issue #242: NCPA resource history missing from both charts

Branch: `issue-242-ncpa-resource-history`
Status: blocked

## Finish condition

- [x] Historical NCPA selection uses the existing plugin classifier, not a check_ncpa substring.
- [x] Regressions assert actual CPU/disk/memory values for generated services.
- [x] Cover service-name fallback, command-based identification, non-NCPA exclusion and requested time window; preserve empty state.
- [ ] Verify Dashboard Average Resource Utilization and Network Health Average Resource with a working agent and stored history on a lab appliance; record deployed revision and both results.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Consistent historical plugin identification | 1, 3 | parametrized API regression with generated, legacy and command-identified service names |
| Actual CPU, memory, disk chart samples | 2 | API regression asserts non-null numeric values and units |
| Time window/non-NCPA exclusion/empty data | 3 | focused regression cases |
| Both affected pages with working agent/history | 4 | live issue-specific report with candidate revision, source samples and browser observations |
| #234 deployment/helper defect distinct | Out of scope | do not change deployment/helper code |

## Plan

1. [x] Add failing regressions in server/tests/unit/test_network_health.py, fix selector in server/app/api/system/network_health.py and run focused/backend checks.
2. [ ] Update Display_Requirements.md and Backend_Modules_and_Routes.md/Implementation_Status.md; verify docs/full gates.
3. [ ] Establish exclusive lab availability, deploy candidate, verify working NCPA history and both charts; record docs/test-runs/ report; publish PR and check CI.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Classify bounded historical rows with _plugin_key; add numeric resource regressions | FLASK_DEBUG=1 .venv/bin/python -m pytest tests/unit/test_network_health.py -q | green: 57 passed; 16 regressions failed before fix |
| 2 | Updated specs; real agent preflight exposed short labels; filed #256 and cleaned fixtures | real NCPA 3.5.0 CPU/memory/disk checks; verify.sh all | checks OK with percent/used_percent labels; live charts blocked by #256; all gate stops on known macOS lock-path failure |
| 0 | Read issue, affected specs and source; inspected running Docker lab without changing it | docker ps | existing six-container lab; ownership must be confirmed |

## State for the next session

- Last check run (exact command): docker exec pinpoint-lab-appliance-1 sha256sum /opt/pinpoint/Network-Diagnosis-System/server/app/api/system/network_health.py
- Result: baseline hash remains 78382323db309d6cb89c3bd0e53cfe192f2be7972ec4512dc5acca3aa5df8bbf; candidate not deployed. Owned agent fixture removed and six original containers preserved.
- Hypothesis: selector fix is correct for canonical full-path resource history, but real short labels require additional mapping; see #256.
- Next action: Ask whether to expand #242 to include #256 label handling, or leave selector PR separate with live acceptance blocked. Full backend verification is still running locally.

## Decisions and notes

- Issue explicitly authorizes live verification. Asked user whether existing Docker lab can be reserved exclusively; no live mutation before ownership confirmation.
- No new dependency or migration; no deployment/resource helper changes.
- Mac host full-gate /tmp and GNU sed limitations were observed on prior issues; retain truthful verification results and Linux CI.

- User confirmed exclusive reservation of the existing Docker lab for issue #242.
- Fallback regression uses supported ncpa/NCPA aliases; check_ncpa in a description alone is not a supported name fallback in the canonical classifier. Command check_ncpa is covered separately.

- Scope blocker: official real agent returns percent for CPU/memory and used_percent for disk. Existing ingestion/predicates do not map them to full paths. Filed #256 after duplicate search; no chart PASS can be claimed.
