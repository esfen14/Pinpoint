# Issue #290: Add READMEs for undocumented directories and an environment variable reference

Branch: `fix-SNMP-interface-checks` (user instruction: work on the current branch; do NOT commit, checkpoint or open a PR)
Status: ready-for-review

## Finish condition

- [ ] One short README per directory: `scripts/`, `dev/`, `server/migrations/`, `server/scripts/`, each `server/app/*` package (`api`, `nagios`, `network_discovery`, `ncpa_deployment`, `logging`), `client/qa`, `client/e2e` (`lab/` already has one). Each gives purpose, entry points, who runs it.
- [ ] Environment variable reference (name, purpose, default, required?) derived from `server/config.py`; `python3 -I scripts/check_env_drift.py` passes.
- [ ] Server README: database layout, CLI commands (`flask seed`, `sync-permissions`, `recover-bootstrap-admin`, restore) and a Python 3.14 justification.
- [ ] Root README: feature summary and a deployment/production pointer.
- [ ] Every top-level directory explains itself.

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Per-directory READMEs | item 1 | `ls` of each directory; `scripts/verify.sh docs` (links) |
| Env reference, name/purpose/default/required | item 2 | `scripts/check_env_drift.py` |
| Server README additions | item 3 | read the file; links checked by `verify.sh docs` |
| Root README additions | item 4 | read the file |
| Root/client/server READMEs lack troubleshooting, db layout, backup dirs, deployment pointer | items 3, 4 | read the files |

## Plan

1. [x] Fix env table in `README.md` (two malformed rows; verify each default against `server/config.py`)
2. [x] Root `README.md`: feature summary, directory table, deployment pointer, troubleshooting
3. [x] `server/README.md`: database layout, backups, CLI commands, Python 3.14, troubleshooting, fix stale text
4. [x] `client/README.md`: add `qa/`, `e2e/`, troubleshooting
5. [x] New READMEs: `scripts/`, `dev/`, `server/migrations/`, `server/scripts/`, `server/app/{api,nagios,network_discovery,ncpa_deployment,logging}/`, `client/qa/`, `client/e2e/`
6. [x] `scripts/verify.sh docs`; update `spec files/` only if a spec lists these directories

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | plan written | - | - |
| 2 | all READMEs written, env table fixed | check_doc_links, check_env_drift, manual link check of new READMEs | green |

## State for the next session

- Last check run (exact command): `python3 -I scripts/check_env_drift.py`
- Result: green (25 variables) before any edit
- Hypothesis: docs only; no code change needed
- Next action: user review; nothing committed

## Decisions and notes

- The branch holds uncommitted #278 work; do not stage or revert it.
- The rationale for Python 3.14 is not recorded anywhere in the repo. Write what is verifiable (CI, dev container, installer pin) and ask a person for the reason.
