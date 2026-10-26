# Issue #273: System Refinement Add One-Time Single-Device Network Discovery Scan

Branch: `issue-273-single-device-scan`
Status: blocked

## Finish condition

- [ ] An authorized administrator can submit one valid IPv4 address and scan only that address through the existing discovery and Nagios configuration pipeline.
- [ ] Saved networks and later scheduled/full scans remain unchanged after successful, failed, and stopped focused scans.
- [ ] Devices and ports outside the requested target retain their state.
- [ ] Invalid, CIDR range, loopback, multicast, unspecified, reserved, and IPv6 targets are rejected before scanning; unauthorized requests are denied.
- [ ] Concurrency, status, stop, and progress work in both modes.
- [ ] An unreachable target gives clear feedback and leaves inventory and Nagios configuration intact.
- [ ] Existing full-network and scheduled discovery continue to work.
- [ ] Automated tests and backend/frontend verification pass.
- [ ] Backend, frontend, data, and implementation-status specifications and user help are updated.
- [ ] PR references #273, records verification and security review, and receives required CI checks and review approvals.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Optional one-time IPv4 target, existing permission, validation and normalization before worker | 1, 4 | Route and target-validation tests; backend gate |
| Target reaches host and port discovery without settings writes | 1, 2 | Mocked discovery and settings tests; backend gate |
| One scan at a time; status, progress, stop, audit, reconciliation, plugin attachment and Nagios rollback | 1, 3, 5 | Route, worker, lifecycle and config tests; backend gate |
| Unscanned devices and ports stay intact | 3 | Multi-device focused-scan regression; backend gate |
| Unreachable target has clear result and no empty/unrelated config change | 6 | Empty-target worker regression; backend gate |
| Admin Scan device input, help, permission gate and feedback; full rescan remains | 1, 5, 7 | Frontend interaction tests; frontend gate |
| Full/scheduled scans and settings remain unchanged even after fail/stop | 2, 7 | Backend regression tests and frontend tests |
| API contract, four named specifications, user help, security review | 9, 10 | Docs gate; explicit review notes; PR diff |
| Relevant automated tests, backend/frontend results and CI/review | 8, 10 | `scripts/verify.sh backend`, `frontend`, `docs`, `all`; PR checks/review |
| No migration unless persistent state is added; no hostname or bulk entry | 1, 2 | Diff review |

## Plan

1. [ ] Add failing validation, permission and concurrency tests in `server/tests/unit/test_network_discovery.py`; implement optional target parsing/thread handoff in `server/app/api/system/network_discovery.py`.
2. [ ] Add failing scan-scope, empty-result and full/scheduled regression tests in `server/tests/unit/test_network_discovery.py`, `test_device_config.py` and identity tests as applicable; implement target flow in `server/app/network_discovery/network_discovery.py`, `create_host_cfg.py`, `device_identity.py` and any necessary port lifecycle code.
3. [ ] Add failing UI interaction tests in `client/src/test/DiscoverySettings.test.tsx` and hook tests as applicable; implement `Scan device` in `client/src/components/settings/DiscoverySettings.tsx`, `client/src/hooks/useNetworkRescan.ts` and shared API/types as needed.
4. [ ] Update `spec files/Backend_Modules_and_Routes.md`, `Frontend_Modules_and_Routes.md`, `Data_Model_and_Integrations.md`, `Implementation_Status.md` and user-facing help for the resulting contract; verify docs.
5. [ ] Re-read issue and prove each finish item; run backend, frontend, docs and all gates; remove this progress file, push and open PR with verification and injection/secret review.

## Round log

One row per loop round, newest last.

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Read issue, workflow, specs and source; wrote plan; no product code changed | `gh issue view 273 --json number,title,body,comments,state,labels,assignees` | Requirements covered; sensitive-module review checkpoint required |

## State for the next session

Everything a fresh session needs to continue without redoing work.

- Last check run (exact command): `gh issue view 273 --json number,title,body,comments,state,labels,assignees`
- Result (first failing lines, or "green"): green; issue open and no comments; no implementation checks run
- Hypothesis: an explicit target must be validated before nmap; the current reconciler scopes unseen lifecycle by network, which needs careful target-specific handling because a `/32` differs from an existing saved subnet.
- Next action (one specific step, not "continue"): Obtain the required person review for sensitive discovery-module changes, then add failing route validation/permission/concurrency tests.

## Decisions and notes

- `Engineering_Standards.md` marks `app/network_discovery/` sensitive and requires an explicit injection and secret-exposure review; `.agent/workflows/work-issue.md` says to stop for a person before changing it. The user needs to review/authorize this checkpoint.
- Security review proposal: accept one strict IPv4 host (canonical dotted-decimal address or `/32` if contract chooses), reject ranges, unsafe/non-global classes and unexpected JSON; hand only the normalized numeric address to nmap; do not interpolate a shell or log request data that can carry secrets; keep existing Nagios validation, resource transaction and rollback. Inspect nmap3 invocation and scanned-result address matching during implementation.
- Current source shows the stop route already uses `system.discover`, while `Backend_Modules_and_Routes.md` and `Implementation_Status.md` still describe a `network.discovery` mismatch. Update those inventories with the issue's owning spec change; this is a stale inventory entry, not a requested permission redesign.
- No hostname resolution or bulk targets. No migration is planned.
