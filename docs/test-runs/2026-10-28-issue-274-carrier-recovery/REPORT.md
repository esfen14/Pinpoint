# Test run: issue-274 carrier and DHCP recovery

| | |
|---|---|
| Date | 2026-10-28, Asia/Manila |
| Presenter revision | `14bdc1b2`; existing containers and persistent presenter checkout use older code |
| Environment | Existing Pinpoint-Final and Windows VMs, host-Docker pilot on `vboxnet1` |
| Scope | Read-only service/address observations and ping from the Windows VM |

## Result

**Partial.** All fourteen Linux containers were running, but all five DHCP
clients had no address. Their interfaces were present and their lease processes
were running; DHCP client logs showed unanswered discovery. Both demo VMs were
off, and `vboxnet1` reported no carrier. Starting Pinpoint-Final brought the
host-only link up, and all five clients automatically reacquired their original
addresses `.20` through `.24`. Starting Windows then allowed one successful
ping to each of the fourteen Linux targets and two successful pings to the
appliance at `10.77.1.1`. No move or rollback was tested, and the prepared
image was not deployed.

With both VMs running, host available memory fell to about 1.5 GiB, below the
plan's 3 GiB reserve; an unrelated `llama` process was using about 11 GiB.
Windows was shut down normally after the ping test. Pinpoint-Final stayed on,
and host available memory rose to about 4.5 GiB. The simultaneous lab does not
pass the resource gate in this host state.

## Routing mistake

Before checking the laptop route, the executor attempted two pings each to
`10.77.1.1` and `10.77.1.3` from the host. They received no replies. A later
route lookup showed that these packets followed the laptop's Wi-Fi default
route rather than the isolated demo adapter. The host pings should not have
been attempted without checking the route first. Subsequent connectivity tests
used only Windows on the isolated segment.

No credentials, tokens, or private configuration are included. This is not a
full issue acceptance rehearsal.
