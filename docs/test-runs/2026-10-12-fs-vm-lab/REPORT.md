# Test run: fs-vm-lab

| | |
|---|---|
| Date | 2026-10-12 |
| Commit tested | `bb7e967` (appliance deployment); isolated MOCK checks from the dedicated QA branch at the same starting main commit |
| Plan | docs/qa/QA_Test_Plan.md |
| Tester | QA agent (tracking [#100](https://github.com/esfen14/Pinpoint/issues/100)) |
| Environment | Fresh Ubuntu 22.04.5 VirtualBox appliance; Nagios Core 4.5.11; restricted lab network `10.77.0.0/28`; fresh application databases |
| Raw evidence | Local VM-lab state and command transcripts; not committed |

## Result

**Overall: Partial.** The FS MOCK cases J4-08, J5-08 and J7-09 passed; J1-02's
installer/service wiring was observed as specified; the restricted VM smoke passed
against all five targets. The run stopped after five QA rounds before additional
FS cases could be claimed.

Totals: Pass 4, Fail 0, Blocked 0, Skipped 0.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| J1-02 | Pass | Appliance listeners: Nginx on 80, Apache only on 127.0.0.1:8081, Gunicorn only on 127.0.0.1:8000. `nagios`, `nginx`, `apache2`, and `pinpoint-gunicorn` were active; Gunicorn ran as `pinpoint`; localhost returned HTTP 200 from the web application. | — |
| J2-01 | Pass | Restricted `scripts/vmlab smoke` completed discovery with Success in 156 seconds and reported the generated host config applied. Each documented target address `.2` through `.6` was monitored and Up. | — |
| J4-08 | Pass | `server/.venv/bin/python -m pytest -c server/pytest.ini server/tests/unit/test_plugin_validation.py`: 28 passed. | — |
| J5-08 | Pass | `server/.venv/bin/python -m pytest -c server/pytest.ini server/tests/unit/test_smtp_settings.py`: 38 passed. | — |
| J7-09 | Pass | Settings, host-config writer, status and plugin-services tests: 160 passed. This covers validation, apply/rollback and Last_Check deduplication as the written MOCK case requires. | — |

## Deviations from the plan

- The initial smoke launch overlapped an inherited scan after administrator setup and
  could not start another scan. The running scan was stopped through the authorized
  API, allowed to reach terminal `Interrupted`, and discovery settings were read back
  and restricted to `10.77.0.0/28` before the successful smoke run. This was test
  environment preparation, not a product-case failure.
- The full verification gate passed: 35 frontend test files / 495 tests, production
  build, and lint with zero errors (tracked warnings only). The command reported
  `verify: all OK`.
- No browser-only FS case was claimed in this round. The five-round workflow limit
  was reached by baseline recovery plus the three isolated FS cases and J1-02/J2-01.

## Follow-up

- Defects found: none.
- Cases to repeat in the next run: J4-01 onward after preserving the fresh baseline;
  execute only after a new QA round claims them.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
