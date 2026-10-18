# Test run: module-13-maintenance

| | |
|---|---|
| Date | 2026-10-18 |
| Commit tested | Lab runs `43f0df1`; the checkout used for this report is `65a5862c`. The only difference between them is one frontend test file (`client/src/test/RemediationPage.test.tsx`), so the deployed product code matches the checkout. |
| Plan | `docs/qa/Pinpoint - Black-Box Test Cases by Module with Traceability Matrix.md`, Module 13 TC-MNT-02 to TC-MNT-10 |
| Tester / executor mode | Mixed. AI-assisted (Claude) drove the browser UI with a Playwright script on installed Chrome and used SSH for setup, fault injection and Nagios evidence. A human (the lab owner) checked the alert mailbox for TC-MNT-10 and approved the plan, the lab changes and the dummy device. |
| Catalog revision and SHA-256 | Checkout `65a5862c`; catalog SHA-256 `ec2b1c3f3b98f73da9b0f5d6656d1565b1405af97a58b2fcc8fe7481fbe5af71` |
| Queue / set / session / batch | No prepared queue (ad hoc run approved by the lab owner in chat). Session 1, one module per branch: `qa-run-module-13-maintenance`. |
| Deployed application / installer revision | Application `43f0df1` (git HEAD on the appliance). Installer revision not checked. |
| Baseline / preflight / restoration | Services nagios, apache2 and pinpoint-gunicorn active. Windows 1 (cancelled) and 2 ("kernel updates", not created by this run) existed before the run. Restoration below. |
| Start / end / time zone | 2026-10-18 14:35 to 15:20 UTC. Appliance in UTC; browser display time zone UTC+08:00. |
| Environment | Ubuntu 22.04.5 lab appliance reached over Tailscale; Nagios Core; scan network configured as the lab's own range, which this run never scanned. Test devices were dummies on `10.77.0.0/28`. |
| Raw evidence | Run scratch folder on the tester machine and the appliance's Nagios log and `status.dat`. Not committed. |

## Result

**Overall: Pass.** All nine selected cases (TC-MNT-02 to TC-MNT-10) behaved as the catalog expects. No product defect was found. TC-MNT-01 was out of scope.

Totals (unique TC): Pass 9, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Totals (unique E2E): Pass 0, Fail 0, Partial 0, Blocked 0, Inconclusive 0, Not run 0.
Historical credit: 0 accepted, 0 partial.
Attempts and setup operations are not extra unique cases.

## Cases

| Case | Result | Notes (what was observed; evidence file name) | Issue |
|---|---|---|---|
| TC-MNT-02 | Pass | "Maintenance window created." and the window listed as Scheduled with its next occurrence. Activity Log: "Created maintenance window 3: kernel updates". | |
| TC-MNT-03 | Pass | 30 days accepted (HTTP 201). 30 days + 1 minute refused by the form with "A window can last at most 30 days." and 0 requests sent. | |
| TC-MNT-04 | Pass | End before start, end in the past, daily 25 h and weekly 8 days were each refused with a message, 0 requests, form open with entries kept. Boundaries daily 24 h and weekly 7 d were accepted. | |
| TC-MNT-05 | Pass | Stop-repeating 366 days after Starts accepted. Editing to 367 days refused: "Repeats can be scheduled at most 366 days ahead." | |
| TC-MNT-06 | Pass | Empty refused ("Add a reason for the maintenance."); 1 and 200 characters accepted. The Reason field has `maxlength=200`, so a 201st character cannot be typed and the form saved 200 characters without a message. A direct API call with 201 characters returned 400 "comment must be at most 200 characters." Judged as meeting the requirement; see Deviations. | |
| TC-MNT-07 | Pass | Prompt "Cancel this window?"; **Keep it** changed nothing (0 requests); **Yes, cancel it** set Cancelled with "Maintenance window cancelled." Running downtime (window 11) and pending downtime (window 12) were removed in Nagios (`DEL_DOWNTIME_BY_HOST_NAME`, downtime depth 0); other windows' downtime stayed. | |
| TC-MNT-08 | Pass | With Nagios stopped, the window was still cancelled and the page showed "Saved in PinPoint, but Nagios was not updated (The Nagios command pipe was not found.) Notifications may continue." Nagios's leftover downtime was removed by hand afterwards. | |
| TC-MNT-09 | Pass | Devices list offered All monitored devices and monitored devices only; the paused, retired and missing dummy devices (and the lab's real missing devices) were not offered. A Staff user typing `/maintenance` was redirected to `/settings` and had no Maintenance in the sidebar. | |
| TC-MNT-10 | Pass | Window active 15:02 UTC. Overview showed the service as "CRITICAL · Downtime". Service reached Hard Critical at about 15:09 UTC with scheduled downtime depth 1; the Nagios log has no failure notification for it, while an ordinary alert on another host in the same period logged one. The lab owner checked the alert mailbox and found no email about the web service going Critical. | |

## Expected-item observations and restoration

| Case / attempt | Expected item | Observed value | Verdict | Private evidence reference | Restoration verified |
|---|---|---|---|---|---|
| TC-MNT-02 | E1 toast and Scheduled row | Toast and row seen | Pass | scratch `mnt02.png` | Window cancelled |
| TC-MNT-02 | E2 Activity Log entry | "Created maintenance window 3: kernel updates" | Pass | scratch `mnt02log.png` | |
| TC-MNT-03 | E1 30 days accepted | 201 | Pass | run output | Window cancelled |
| TC-MNT-03 | E2 30 d + 1 min refused before sending | Message shown, 0 requests | Pass | scratch `mnt03b.png` | |
| TC-MNT-04 | E1 each invalid case refused, form kept | 4 of 4 refused, entries kept | Pass | run output | Boundary windows cancelled |
| TC-MNT-04 | E2 daily up to 1 day, weekly up to 7 days | Both accepted | Pass | run output | |
| TC-MNT-05 | E1 366 accepted, 367 refused | As stated | Pass | run output | Window cancelled |
| TC-MNT-06 | E1 0 and 201 refused, 1 and 200 accepted | 0 refused; 1 and 200 accepted; 201 not enterable (field limit) and 400 from the API | Pass | scratch `mnt06.png` | Windows cancelled |
| TC-MNT-07 | E1 Keep it changes nothing | 0 requests, status unchanged | Pass | scratch `mnt07.png` | |
| TC-MNT-07 | E2 Cancelled, message, downtime ends | As stated, running and pending | Pass | Nagios log lines | |
| TC-MNT-08 | E1 window cancelled and notice | As stated | Pass | run output | Nagios started; stale downtime removed |
| TC-MNT-09 | E1 devices not choosable | None of the 3 offered | Pass | run output | Dummies removed, Staff user kept until closing |
| TC-MNT-09 | E2 Staff redirected, no sidebar entry | `/settings`, no Maintenance | Pass | scratch `mnt09staff.png` | |
| TC-MNT-10 | E1 downtime indicator | "CRITICAL · Downtime" | Pass | scratch `overview_mnt10.png` | Window 11 cancelled, service restarted |
| TC-MNT-10 | E2 service Critical | Hard Critical in downtime | Pass | Nagios log | |
| TC-MNT-10 | E3 no notification email | None in Nagios log or mailbox | Pass | Nagios log; owner mailbox check | |

Timing: TC-MNT-10 used real elapsed time (window created 14:47 UTC to start 15:02, Hard Critical 15:09). No clock was changed. TC-MNT-03 to 05 are form-validation boundaries and needed no elapsed time.

## Deviations from the plan

- Windows were created on a dummy device, not a real one, per the owner's rule that real devices must not be affected.
- The lab has no web VM: the dummy `qa-dummy-web` listens on `10.77.0.5` port 110 and is monitored with `check_tcp`. Port 80 was unavailable because Apache listens on all addresses. The dummy replaces the "web VM" of TC-MNT-10.
- Enabling the `check_tcp` plugin was needed to monitor the dummy service. The preview showed it matched only that one service.
- Extra boundary windows were created (daily 24 h, weekly 7 d) in TC-MNT-04.
- TC-MNT-06 step 4: the form cannot accept a 201st character, so the form never refuses it with a message. Recorded as Pass because a 201-character reason cannot be saved by either the form or the API. The owner may want a visible message instead.
- TC-MNT-07: a separate pending window was created to observe pending downtime, because the first window's downtime was already running.
- TC-MNT-09 used dummy paused, retired and missing devices instead of real ones.
- A dummy "missing" device briefly sent one real DOWN email before it was removed (setup side effect, not a product finding).
- Window 2, "kernel updates" (created 13:53 UTC by someone else), was not touched.
- Test mailbox: the Gmail connector available to the tester is not the alert recipient, so the lab owner checked the mailbox.

## Follow-up

- Defects found: none.
- Open for the lab owner: remove `qa-dummy-web`, the `10.77.0.5` loopback alias, the Staff user `qa-staff` and the `check_tcp` enablement after Module 14 finishes (the dummy is reused there).
- Cases to repeat in the next run: none.

## Sanitization checklist

- [x] No passwords, tokens, keys, SNMP communities or private key paths
- [x] No addresses outside the documented lab range
- [x] Evidence is referenced by name and location, not pasted
