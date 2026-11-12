# `scripts/` — developer, QA and lab tooling

Command-line tools for developers, testers and agents. **None of this is
installed on a production appliance or run by the application.** Run everything
from the repository root.

## Everyday

| Script | Does |
|---|---|
| `verify.sh <docs\|backend\|frontend\|all>` | The single verification entry point; CI runs the same commands. See [Agent Workflow and CI](../spec%20files/Agent_Workflow_and_CI.md) |
| `agent-worktree.sh <name>` | A separate git worktree and environment for an AI agent |
| `agent_checkpoint.sh <issue> "<msg>"`, `check_agent_progress.py` | Commit/push and validate an agent's `.agent/progress/` file |
| `new_test_run.sh <slug>` | Start a report in `docs/test-runs/` from the template |
| `file_plan_issues.sh` | File the planned issues in `docs/issues/` on GitHub (dry run by default) |

## Drift checks (run by `verify.sh docs`)

| Script | Fails when |
|---|---|
| `check_env_drift.py` | The environment variables the server reads and the root README table disagree |
| `check_route_drift.py`, `check_client_api_drift.py`, `check_frontend_route_drift.py` | Flask routes, client API calls, browser routes and the specifications disagree |
| `check_doc_links.py` | A relative Markdown link is broken |
| `check_traceability.py`, `render_qa_case_tables.py --check` | The QA case catalog, requirement mappings or derived status are inconsistent |
| `lab_drift.py` (via `lab check-drift`) | The lab appliance pins differ from the PinPoint Installer; needs an installer checkout, not part of CI |

## Labs

| Script | Does | Needs |
|---|---|---|
| `lab` | Local Docker lab: appliance plus five targets (`up`, `down`, `smoke`, `sync`, `break`, `fix`...) | Docker. [Local lab manual](../docs/manuals/Local_Lab.md) |
| `dhcp-lab`, `dhcp-accept` | Isolated DHCP lab and its acceptance run | Docker, `CAP_NET_ADMIN`; never in CI |
| `vmlab`, `vmlab_preflight.py` | VM appliance lab (VirtualBox) with the demo targets | VirtualBox; [VM lab plan](../docs/archive/plans/VM_Lab_Plan.md) |
| `playwright-lab` | Browser smokes in a no-network container with a socket bridge | Docker and a running appliance |

## QA automation (`qa_*.py`)

The `qa_*.py` modules prepare, constrain and record supervised QA runs against
the black-box case catalog. They are guarded: many are libraries with no live
entry point, and the ones with a command line (for example `qa_queue.py`,
`qa_coverage.py`, `qa_evidence.py`, `qa_execute.py` and `qa_pilot.py`) are
offline or refuse to start a lab without reviewed cards and an explicit start. Read [QA run queues](../docs/qa/QA_Run_Queues.md) and
[Automation readiness](../docs/qa/Automation_Readiness.md) before running one.

## Tests

`test_*.py` are offline unit tests for the scripts above (synthetic fixtures, no
Docker, VM, browser or network). `verify.sh docs` runs them.
