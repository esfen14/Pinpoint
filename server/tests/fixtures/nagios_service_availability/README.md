# Installed Core 4.5.11 contract probe (#198)

Captured read-only from the exclusively reserved installer-built VM on 2026-10-17.
These are native responses, with only user/host/service identifiers replaced.
Each fixture preserves its original durations, envelope and selectors. Fixture
names `24h` and `90d` describe request windows, not successful coverage.

The CGI was executed locally as the existing web-server user (`www-data`) with
`REMOTE_USER=nagiosadmin`; no password was read or persisted. This establishes
CGI behavior only, not HTTP authentication, timeout, frontend or deployed API
behavior. There were eight configured services on one host.

The fixed 24h/90d windows ended at 1792245456; queries ran at 1792245479/80.
Both returned zero in every duration. The missing-history fixture is the same
kind of zero result for 2001-01-01 UTC. It is not an empty configured-object list;
`empty.json` demonstrates the distinct valid-empty response.

The live-now preliminary probe returned nonzero durations, but they are not in
these fixtures: that capture was diagnostic output and was not persisted before
its fixed-window rerun. Its discrepancy is recorded in the contract-probe report.
Do not treat the preliminary numbers as proven measured historical coverage.

No runtime adapter has been written. The issue requires resolving contradicted
design assumptions before implementation. See
[the probe report](../../../../docs/test-runs/2026-10-17-issue-198-contract-probe/REPORT.md).
