# Pinpoint defense cue card

Keep this beside the browser. Full wording and recovery notes: [Pinpoint-Demo-Script.md](Pinpoint-Demo-Script.md).

## 30-second opening

“Pinpoint gives the administrator one interface for network discovery, Nagios monitoring, alerts, NCPA metrics, and response. I’ll discover our isolated lab of fifteen devices, attach checks through plugins, create a real fault, and show recovery.”

## Flow to remember

**Settings: `10.77.1.0/27` → Dashboard: Rescan Network (15 devices) → Inventory/Network Status → enable `check_ncpa` → Windows NCPA (`win01`) → Ports/service checks → fault/recovery → Remediation → Maintenance → address change (DHCP) → Accounts/Settings.**

Keep credentials off the projector. The prepared appliance has already passed its first login; for the password-change screen use a new account marked **Require password change at first sign-in**.

## Two-terminal commands (laptop)

From the repository root (or the `~/Documents/Pinpoint-Demo/` shortcut, which is a link to the same script):

```bash
demo/Pinpoint-Demo-faults.sh wall                    # live status; Ctrl+C exits
demo/Pinpoint-Demo-faults.sh services web03          # one target's services and address
demo/Pinpoint-Demo-faults.sh down web03 http         # one service fails
demo/Pinpoint-Demo-faults.sh up web03 http           # restore that service
demo/Pinpoint-Demo-faults.sh down dynapp01 host      # optional whole-container failure
demo/Pinpoint-Demo-faults.sh up dynapp01 host        # start it again
demo/Pinpoint-Demo-faults.sh dhcp-move dynweb01 10.77.1.25   # same device, new address
demo/Pinpoint-Demo-faults.sh dhcp-move dynweb01 10.77.1.20   # move it back
```

Only the named presets are accepted; run `Pinpoint-Demo-faults.sh help` for the list. Stopping a service leaves the container and its other services up. The wall changes at once; Nagios and Pinpoint need their next checks, retries and polling before they show the alert.

## Quick device map

| Device | IP | Demo services | Best use |
|---|---|---|---|
| `dhcp01` | `10.77.1.2` | SSH, DHCP | Lease source; leave running |
| `win01` | `10.77.1.3` | NCPA 5693 | Windows metrics (no fault controls) |
| `web03` | `.4` | HTTP 80, HTTPS 443 | Clean single-service fault and recovery |
| `api02` | `.5` | HTTP 8081 | Nonstandard port, maintenance fault |
| `ftp01` `mail01` `dns01` `db01` | `.6` `.7` `.8` `.9` | FTP; SMTP+IMAP; DNS (UDP); PostgreSQL | Protocol variety |
| `snmp02` | `.10` | SNMP 161/UDP | SNMP monitoring |
| `ssh-alt02` | `.11` | SSH 2223 | Nonstandard SSH |
| `dynweb01` `dynapp01` `dynmail01` `dynsnmp01` `dynweb02` | `.20` `.21` `.22` `.23` `.24` | DHCP clients with web/SMTP/SNMP | Address change on the same device |

## Missing and archive: what to say

A port that disappears first fails its check (CRITICAL). It becomes **Missing** only after five scans no longer see it, and stays monitored. It is **archived** after the configured period (default 30 days), when its Nagios service is removed. Nothing is deleted immediately, so do not promise the row vanishes after a fault.

## Fault follow-ups

- **Remediation:** use an enabled **Record only** action for the exact `web03` HTTP service, then cause a hard failure. The Run log proves the event was handled. Record only never restarts anything; restore with `up web03 http`.
- **Maintenance:** schedule a one-off active window for `api02` before `down api02 http`. Show downtime and suppressed notifications; cancel, then restore. Global **Maintenance Mode** in Settings is a different control.
- **Address change:** after `dhcp-move`, run a scan. The same device shows the new IP; Pinpoint does not yet show an address history (#277).
- **If the alert is delayed:** show the red wall row now, then wait for Nagios hard state and Pinpoint polling.
- **End clean:** restore every fault you used (`up ...`, move `dynweb01` back to `.20`), cancel the demo window, disable/delete the demo remediation action, and check `status`.
