# lab/

Harness code for the test labs. `lab/` mixes files for four different uses; this
table says which file serves which lab, and which script runs it. Check the
owner before editing or removing a file.

## Which file serves which lab

| Files | Owner script | Lab it needs | Guide |
|---|---|---|---|
| `compose.yaml`, `appliance/`, `targets/`, `mail/` | `scripts/lab` only | Local lab: Docker appliance, five targets (`web01`, `web02`, `app01`, `snmp01`, `legacy01`) and the mail sink `mail01` | [Local lab manual](../docs/manuals/Local_Lab.md) |
| `identity_review_fixture.py` | Run by hand inside the local lab appliance (opt-in: `PINPOINT_IDENTITY_LAB=1`, `PINPOINT_SCHEDULER=0`) | Local lab | [Local lab manual](../docs/manuals/Local_Lab.md) |
| `dhcp/` | `scripts/dhcp-lab`, `scripts/dhcp-accept`; unit tests `server/tests/unit/test_dhcp_lab_control.py`, `test_dhcp_acceptance.py` | Isolated DHCP lab (Docker, `CAP_NET_ADMIN`, `10.79.0.0/28`) | [Isolated DHCP lab](../docs/manuals/Local_Lab.md#isolated-dhcp-lab) |
| `smoke.py` | `scripts/vmlab smoke` and `scripts/lab smoke` (shared) | Either lab; it hardcodes the five local target names in `TARGETS` and takes the rest through flags | [VM lab plan](../docs/archive/plans/VM_Lab_Plan.md) |
| `setup_restricted.py`, `phase0_event_handler_probe.sh` | `scripts/vmlab` | VM appliance lab | [VM lab plan](../docs/archive/plans/VM_Lab_Plan.md) |
| `alerts_run.py` | `scripts/vmlab alerts` | VM appliance lab with the demo's Docker targets only. It shells out to `demo/demo`, so it cannot run against the local lab | [Demo index](../demo/README.md) |
| `vmlab.env.example` | Template for `scripts/vmlab` settings | VM appliance lab | |
| `unix_web_proxy.mjs` | `scripts/playwright-lab`, `scripts/qa_transport.py`, `scripts/qa_queue.py` | QA browser runs against a VM appliance (not a Docker lab) | [QA run queues](../docs/qa/QA_Run_Queues.md) |

The fifteen-device demo has its own `demo/` directory with its own `targets/` and
`appliance/`; they are not the same as `lab/targets/` and `lab/appliance/`. See the
[demo index](../demo/README.md).

## Role of the local lab

The owner decided in issue #306 to keep the local lab (`compose.yaml`,
`appliance/`, `targets/`, `mail/`) as the headless lane, because it needs only Docker.

- It is not in CI: a lab job would slow every pull request. Run `scripts/lab smoke` by hand.
- It tracks the installer. `appliance/` copies the installer's steps by hand; it was
  audited in issue #316, and `scripts/lab check-drift` (issue #317) reports when the
  versions pinned in `appliance/Dockerfile` differ from the installer. Run it when
  the installer changes.
- `targets/` stays separate from `demo/targets/`, and the lab is not retired.
- The smoke test's plugin and alert gap is closed (issue #315), and issue #316 added
  email checks against the mail sink in `mail/`. Still open: `scripts/lab ui` is
  unverified, and NCPA deployment and remote restart need a VM-lab appliance
  (issue #322).

Details are in the [Local lab manual](../docs/manuals/Local_Lab.md#role-of-this-lab).

## Why the shared files stay in `lab/`

Issue #305 considered moving the shared helpers (`smoke.py`, `unix_web_proxy.mjs`
and the `scripts/vmlab` helpers) out of `lab/`. They stay: the QA queue files under
`docs/qa/queues/` record a SHA-256 of `lab/unix_web_proxy.mjs`, and
`scripts/qa_queue.py` checks it, so a move invalidates reviewed queues. The scripts,
tests (`scripts/test_playwright_safety.py`, `scripts/test_vmlab_setup_admin.py`) and
docs also name these paths. If a move is wanted later, change the queue hashes and
those references in one reviewed change and run `scripts/verify.sh all`.
