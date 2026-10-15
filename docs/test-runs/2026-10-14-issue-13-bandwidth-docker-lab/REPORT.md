# Test run: issue-13-bandwidth-docker-lab

| | |
|---|---|
| Date | 2026-10-14 |
| Commit tested | Branch `fix-interface` at `9252b105` **plus the uncommitted working tree** of this change (nothing was committed when the run was made). Not reproducible from a commit until the change is committed. |
| Plan | The lab test of issue 13 (interface bandwidth): known traffic compared with the charted rate |
| Tester | Claude Code |
| Environment | Docker local lab (`scripts/lab up`): the appliance with real Nagios Core 4.5.11 and plugins 2.4.12, and the real `snmpd` target `snmp01` (10.78.0.5). The lab database was upgraded with `flask db upgrade` (revisions `143c48cd6663` and `b7d3f1a9c264` applied), and the working tree was copied in with `scripts/lab sync`. |
| Raw evidence | The lab appliance's `history.db` (`SERVICE_STATUS`, `SERVICE_PERF_DATA` for `snmp-if11_*`), not committed. |

## Result

**Overall: Partial.** The interface list, monitoring, Nagios validation and the rate were observed running on the lab. After fixing one defect found by this run, the charted rate matched the generated traffic within 5%. The traffic was made with `ping`, not `iperf3`, and the browser UI was not exercised.

Totals: Pass 6, Fail 0, Blocked 0, Skipped 2.

## Cases

| Case | Result | Notes | Issue |
|---|---|---|---|
| L1 Migration on the lab database | Pass | `flask db upgrade` ran `a4c8e1f6d392 -> 143c48cd6663 -> b7d3f1a9c264` without error | |
| L2 Enable `check_snmp`; SNMP port becomes monitored | Pass | Plugin Manager enable applied a config (6 services); `udp/161` went from Suggested to Monitored | |
| L3 Interface discovery over SNMP | Pass | `POST /hosts/4/interfaces/refresh` read 11 interfaces from the real `snmpd` (names, `eth0` speed 10 Gbit/s, status) | |
| L4 Monitor an interface; Nagios validates | Pass | `PUT /hosts/4/interfaces/11` `{"monitored": true}` returned `config_ok: true`, `config_applied: true`; the generated config was validated with the Nagios binary and applied. Services `snmp-if11_in_octets-161-udp` and `snmp-if11_out_octets-161-udp` ran and stored counters | |
| L5 Window validation on the live route | Pass | `hours=2` gave 400 "hours must be one of: [1, 6, 24, 168]." | |
| L6 Rate against known traffic | Pass, after a fix (below) | See the table below | |
| L7 `iperf3` as the traffic generator | Skipped | `iperf3` is not installed in the lab targets and the lab network has no internet. `ping` with a fixed interval was used instead, so the expected rate is computed from the packet count | |
| L8 Browser UI (card, drawer section) | Skipped | Only the API was exercised; the UI is covered by vitest with mocked APIs | |

### L6 detail

Generator: from the appliance, `ping -i 0.01 -s 1400 -w 240 -q 10.78.0.5`. It sent 18,799 packets in 240 s (78.3 packets/s, not the 100 asked for). Each echo is 1400 + 8 + 20 + 14 (ICMP, IP, Ethernet) = 1442 bytes, so the expected rate is 18,799 / 240 x 1442 x 8 = **903.6 kbit/s** in each direction (a few kbit/s of Nagios SNMP polling is also on the interface).

| Reading | Rate | Against 903.6 kbit/s |
|---|---|---|
| Before the fix: full-load intervals, divided by the 60 s the row was stored | 743 kbit/s | -17.8% |
| After the fix: counter delta over 150 s of full load (17,426,224 B, Nagios `Last_Check` 17:18:19 to 17:20:49) | 929 kbit/s | +2.9% |
| After the fix: the endpoint's two full-load intervals (in and out equal) | 921 and 946 kbit/s | +2.0% and +4.6% |
| After the fix: first and last intervals | 498 and 527 kbit/s | partial intervals: the traffic started and ended inside them |

Tolerance used: within 5% over full-load intervals. The partial intervals are expected to read lower.

### Defect found and fixed during the run

Pinpoint stores a row each time it polls Nagios (every 60 s here), but Nagios reads the counter on its own schedule (every 50 s, the lab's `interval_length=10` x check interval 5). The first version of `GET /network-health/bandwidth` divided by the stored time (`Timestamp`), so it read 17.8% low. The fix takes each sample's time from `Last_Check` (when the counter was read), falling back to `Timestamp`. A unit test (`TestSampleTime` in `server/tests/unit/test_network_health_bandwidth.py`) covers it. This only showed up against real Nagios; the earlier tests seeded both times as equal.

## Not covered

- `iperf3`, and a link faster than a few Mbit/s: the 32-bit counter wrap and a counter reset were covered by unit tests only, not on the lab.
- The browser UI.
- A VM-lab (installer-built appliance) run.
