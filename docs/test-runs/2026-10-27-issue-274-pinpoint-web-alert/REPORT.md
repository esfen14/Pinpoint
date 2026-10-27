# Test run: issue-274-pinpoint-web-alert

| | |
|---|---|
| Date | 2026-10-27, Asia/Manila |
| Presenter / plan revision | `47698bc5`; running appliance revision not established |
| Plan | [Defense demo lab](../../plans/Defense_Demo_Lab_Plan.md) |
| Executor | Owner observes Pinpoint UI; AI-assisted fixed presenter operations |
| Environment | Owner's Pinpoint-Final VM and laptop Docker pilot on `10.77.1.0/27` |
| Raw evidence | Owner-reported status and local presenter observations; no raw log retained |

## Result

**Partial.** The owner reported web03 HTTP visible and OK and Windows NCPA
checks all OK. First attempt stopped the shared web service; the owner checked
the Nagios host ping, which remained up as expected, and the scheduled restore
returned the service to RUNNING. On the second attempt the owner reported the HTTP service went CRITICAL.
Presenter restoration succeeded and the owner then reported the same HTTP check returned to OK. The owner subsequently reported all fifteen demo addresses visible, a total of sixteen devices including Nagios, and Windows metrics. Alert notification display, exact timings and full-lab acceptance were not observed. This is not QA case or E2E credit.

| Check | Result | Observation |
|---|---|---|
| Web baseline | Pass | HTTP check for web03 was visible and OK. |
| Windows NCPA checks | Pass | Owner reported checks OK and Windows memory 47.5944%, CPU 0.0853%, disk 45.6%. |
| Demo inventory | Pass | Owner reported all fifteen demo addresses visible and sixteen devices including Nagios; individual inventory rows not independently inspected. |
| Induce web failure | Pass | Presenter reported `web03 http stopped`; it controls the shared HTTP/HTTPS daemon. |
| First-attempt host ping | Pass | A manual `host_check/ping` did not report the host down; the device was not stopped. This does not test HTTP failure. |
| First-attempt restoration | Pass | Scheduled timer succeeded; presenter status showed web RUNNING. |
| Second-attempt Pinpoint HTTP failure | Pass | The HTTP service check went CRITICAL while the web daemon was stopped. The alert UI itself was not reported. |
| Second-attempt local restoration | Pass | Presenter returned `web03 http running`; the backup restore timer was stopped. |
| Pinpoint HTTP recovery | Pass | The owner reported the same HTTP service check returned to OK after restoration. |

No passwords, tokens, keys, communities, or addresses outside the demo range are
included. The test is tracked under [#274](https://github.com/esfen14/Pinpoint/issues/274).
