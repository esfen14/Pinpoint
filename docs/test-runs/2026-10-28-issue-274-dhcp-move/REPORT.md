# Test run: issue-274 DHCP move and interruption recovery

| | |
|---|---|
| Date | 2026-10-28, Asia/Manila |
| Presenter revision | `14bdc1b2`; existing Pinpoint-Final appliance |
| Environment | Two VirtualBox VMs and fourteen host-Docker targets on `vboxnet1` |
| Scope | DHCP move and one interruption, with ping-only connectivity checks |

## Result

**Partial pass.** The DHCP server and five clients were replaced with the
prepared image. Their original identity and data mounts were reused; their
previous containers were kept stopped as backups. All five acquired their
original reservations, and Windows pinged the appliance and all fourteen Linux
targets successfully after deployment.

The fixed VirtualBox inventory showed only the expected two running VMs on
`vboxnet1`. Local inspection found the expected fourteen macvlan attachments
across active process network namespaces in two passes, and one Docker macvlan
network using the parent. This does not prove absence of every possible
namespace held without an active process.

| Check | Result | Observation |
|---|---|---|
| Move | Pass | `dynweb01` moved from `10.77.1.20` to `10.77.1.25`; Windows ping to `.25` succeeded. |
| Other clients | Pass | Windows ping to each of `.21`, `.22`, `.23` and `.24` succeeded during the move. |
| Restore by move | Pass | The presenter moved `dynweb01` back to `.20`; Windows ping received 2/2 replies. |
| Interrupted move | Pass | A second move was interrupted after its journal recorded the allocator change. The process exited from the interrupt and the recovery intent cleared. |
| Recovered baseline | Pass | All five original reservations and addresses were observed; the six upgraded container IDs were unchanged; Windows ping to `.20` received 2/2 replies. |

The move and recovery checks did not verify Pinpoint discovery, monitoring
history association, DHCP-to-static transitions, IP reuse, all possible
interruptions, or an outage recovery. The client ID reported by node inspection
is catalog-derived; SSH host key continuity was not independently measured.
After the test, both VMs and all fourteen current targets were running; a host
sample showed about 11.1 GiB available. This single sample does not establish
the full rehearsal resource gate. No credentials, tokens, or private owner
markers are included.
