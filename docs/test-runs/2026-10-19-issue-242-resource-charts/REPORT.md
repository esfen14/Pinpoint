# Test run: issue-242-resource-charts

| | |
|---|---|
| Date / time zone | 2026-10-19, Asia/Manila (UTC+8) |
| Candidate source revision | `ca3c4ea96e4cd0e0a37f0f80ab259b14656ee8c4` |
| Plan | [#242](https://github.com/esfen14/Pinpoint/issues/242), including user-authorized [#256](https://github.com/esfen14/Pinpoint/issues/256) label handling |
| Executor / mode | Codex; scripted official agent/Nagios/API checks and AI-assisted actual browser UI |
| Catalog / queue | Issue-specific feature acceptance; no catalog case execution or historical verdict replacement |
| Appliance baseline | Existing ARM64 Docker lab, mounted source revision `44471f7cc5ee94348cff18015993dd023d53365d` |
| Deployed candidate | Only `network_health.py` and `statistics.py` copied from candidate `ca3c4ea9` into the existing appliance, then Gunicorn restarted. This is an explicitly composite deployment, not a claim that every appliance file is that revision. Vite serves the unchanged candidate frontend from this checkout against that real API |
| Deployed file SHA-256 | network_health.py `a68b454e0c41eb54d74b24e4081386a720820adeed4253ab5bff9a24183a4a9a`; statistics.py `0b0450990cca1c45c3ac46d07a429630a5115e9b79fcfba89d7be6d46a7e5dcb` (both matched checkout files) |
| Agent / checks | Official NCPA 3.5.0 DEB extracted into temporary x86-64 Ubuntu 22.04 container (emulated on ARM64); official v3.5.0 check_ncpa.py through the existing protected-token adapter; manually defined fixture Nagios host/services with generated ncpa-* descriptions and pinpoint_nd_ncpa command identity |
| Network / isolation | User reserved existing internal Docker lab `10.78.0.0/24`; agent `10.78.0.20`, no published agent port and disconnected from default bridge; no discovery scan or SSH deployment |
| Stored sample period | 16:18:13–16:32:13 Manila (08:18:13–08:32:13 UTC) |
| Raw evidence | Git-ignored `test-results/issue-242/stored-samples.json` contains sanitized stored counts/ranges; public downloaded package/client are in the same ignored directory. Browser AX/screenshot observations are in the task tool record; no raw screenshot is committed |

## Result

**Overall: Pass for both required live resource-chart journeys.** A working real
agent produced CPU, memory and disk data; real Nagios checks and normal Pinpoint
polling stored 15 samples per resource. Both Dashboard and Network Health displayed
populated resource data using the candidate. Scope includes #256 short-label
handling following the user's explicit approval. Forecast selection remains a
separate assessed consumer in [#259](https://github.com/esfen14/Pinpoint/issues/259).

Totals: two issue-specific browser journeys passed; zero catalog TC/E2E cases
executed or credited. Earlier blocked preflight remains recorded separately.

## Observations

| Check / journey | Result | Actual observation |
|---|---|---|
| Real agent / Nagios | Pass | Official CPU, virtual-memory and logical-disk checks returned OK; Dashboard Service Overview showed NCPA 3/3 OK. No fake sample injection |
| Stored CPU history | Pass | `ncpa-cpu-5693-tcp`, metric `'percent'`, 15 samples, range 0–17.88% |
| Stored memory history | Pass | `ncpa-memory-5693-tcp`, metric `'percent'`, 15 samples, range 29.6–33.9% |
| Stored disk history | Pass | `ncpa-disk_root-5693-tcp`, metric `'used_percent'`, 15 samples, 0.8% |
| Real trends API | Pass | Authenticated HTTP 200 for hours=1, buckets=6; observed non-null CPU [2.21, 6.5889], memory [31.2, 30.3667], disk [0.8, 0.8] before later polls. Values evolve normally |
| Dashboard Average Resource Utilization | Pass | Actual browser sign-in, Dashboard section visible, green CPU bar and tooltip `cpu: 6.7682`; absent the previous no-CPU-data empty state |
| Network Health Average Resource | Pass | Actual page card showed CPU 7.0375%, memory 30.75%, disk 0.8%; graph opened via its button. Last hour selection showed three visible populated series with CPU 11.5 last / 7.2 avg, memory 32.3 last / 30.8 avg and disk 0.8 last / avg |
| Isolated regressions | Pass | Final Network Health/statistics target: 131 tests passed. Includes full paths, short/quoted/per-core labels, service fallback, command metric paths, non-NCPA exclusion, old/future window exclusion, empty data and swap/disk-I/O/ambiguous exclusions |
| Candidate Linux CI | Pass | All three jobs passed on `ca3c4ea9` (run 39221818664); final documentation/cleanup commit still receives its own CI |

## Attempts and limits

The first preflight exposed short labels and was blocked; the user then authorized
including #256 in #242. That historical preflight is not rewritten as a PASS.
One native browser click failed in the tool; opening the observed button with the
semantic locator succeeded. A direct-navigation/account-menu tool attempt also
needed retry; the completed browser journeys above were visibly verified.
The browser connector's first connection took unusually long; no chart verdict
was inferred during that delay.

This is functional Docker acceptance, not installer/systemd or NCPA SSH deployment
acceptance, the user's own appliance, independent hardware or scale testing.
The agent was emulated and fixture checks manually wired in Nagios; no #234
resource/deployment helper fix is claimed. Existing local macOS verification
limitations remain: the all gate stops on canonical /tmp checks, and the separate
backend run had four GNU sed-dependent failures (4,335 passed / 26 skipped) before
the label expansion. Linux CI is the full supported gate.

## Restoration

- Browser used the supported Account menu → Log out → Sign Out flow and returned
  to Login. API diagnostic sessions also logged out; normal audit records remain.
- Restored the original two backend source files and Nagios configuration with
  candidate hash guards, restarted Gunicorn and reloaded Nagios. Validation:
  zero warnings / zero errors; fixture host absent from active status.
- Original deployed network_health.py hash returned to
  `78382323db309d6cb89c3bd0e53cfe192f2be7972ec4512dc5acca3aa5df8bbf`;
  original hosts.cfg hash remained
  `70236d60c291e47d8fe371d24349b929d3337bf0f01f2067afd722a9645bae20`.
- Removed only fixture-owned history for the unique `issue242-agent` host after
  it left active Nagios status; no unrelated history, inventory or audit records
  were deleted. Protected temporary runtime files and only the verified owned
  fixture container were removed. All original six containers remain running.
- Baseline authenticated trends API again returned HTTP 200 with `ncpa: null`.
  No claim is made that the restored baseline now contains the fix; deployment is
  a later user/team action after review.
