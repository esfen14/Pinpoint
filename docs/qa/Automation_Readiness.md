# Current-case adapter preparation

[Automation coverage](Automation_Coverage.md) accounts for all 231 TC cases and
eight E2E scenarios. It is generated from `automation-coverage.json` and shows
source implementation, expected items still missing and unassigned executors.
It does not change the human catalog or certify any runtime PASS.

Five permission adapters are source-complete: TC-SS-04, TC-HIS-01, TC-RPT-07,
TC-LOG-05 and TC-PLG-07. Only TC-SS-04 is currently untested in the human catalog;
the other four remain excluded from default pending queues. An intentional
`recheck` needs its own reviewed assignment. The remaining 234 cases/scenarios
are explicitly unmapped, not automatically classified as suitable for automation.

## What is implemented

- `scripts/qa_coverage.py` validates the complete register, catalog/case hashes,
  source-file hashes, review metadata, adapter identity and expected-item markers.
  Implemented means every expected item has source-reviewed assertion coverage;
  markers do not prove that assertions are correct or that a browser ran.
- Queue snapshots include the case's coverage record and fingerprint the register,
  selection configuration and helper. Preparing/checking a supplied execution card
  rejects unmapped/partial coverage and a changed mapping, adapter, title, project,
  config or exact argv. Changed sources require renewed review and new queue scope.
- `client/playwright.qa.config.ts` selects only `qa-permissions.lab.spec.ts` in
  `qa-permissions`, with explicit current IDs, one worker, no retries or setup
  dependencies, fixed loopback origin and disabled trace/video/screenshot capture.
  A failed test stops further tests; bounded action/navigation/case/global limits apply.
- Each adapter signs in through the UI using an already initialized disposable
  Staff account, checks its role, zero permissions and completed password/setup
  state, then checks the exact hidden sidebar link and redirect. API cases open
  the specified API address in the browser and assert 403. No intercepted response
  or shell operation replaces a case step. Sanitized E1 evidence is attached only
  after all its assertions succeed. Logout and unauthenticated `/me` checks record
  cleanup; Playwright disposes the independent context. Login/logout audit entries
  are expected side effects and must not be erased.
- `client/qa/selection.mjs` requires explicit supported unique IDs and a new, empty,
  same-owner private directory (0700 recommended), rejecting symlinks and broader
  permissions. JSON/artifacts stay there. It does not inspect credentials or a lab.
- The offline journal requires complete expected-item observations, every approved
  action slot recorded, timeout compliance and verified cleanup before PASS.
  Recording an action is an attestation, not dispatch or proof of execution.

## Preparation commands

These commands read local sources and produce metadata; none launches Playwright,
contacts the appliance, provisions an account or runs a product case:

```bash
python3 -I scripts/qa_coverage.py check
python3 -I scripts/qa_coverage.py show --id TC-SS-04
python3 -I scripts/qa_coverage.py card-template --id TC-SS-04
python3 -I scripts/qa_coverage.py render --write
```

The template includes exact source identity and command selection. It deliberately
has BLOCKED readiness, no reviewer/observed prerequisites, no evidence path and no
timeouts, with `human_required: true`. It cannot open a case. Never fill those fields
with guessed observations or simply switch the blocking flag to make it execute.

To review or change coverage, inspect the full written case and relevant behavioral
specification, every assertion and fixture/cleanup step. Record reviewer/date,
procedure coverage, each E1/E2 observation method and all relevant source hashes.
A partial adapter remains partial. If the catalog or a dependency changes, review
the impact before refreshing hashes; regeneration alone is not a coverage review.

## Remaining live requirements

The existing `scripts/playwright-lab` does **not** forward `PINPOINT_QA_CASES` or
`PINPOINT_QA_RUN_DIR` into its container or mount the new private artifact path.
The new config therefore fails closed through the current launcher. Do not work
around this by launching a host browser with credentials or relaxing isolation.
A future reviewed launcher must bind those values to the immutable queue/card,
provide private per-run mounts, verify deployed version and exclusive ownership,
then launch only the approved exact selection through the no-network boundary.
An environment variable or config file is not runtime authorization or an OS sandbox.

No live card is complete yet. Actual account readiness, target revision, lab claim,
preflight, output lifetime, interruption/recovery and set start must be reviewed and
proved. Browser hooks may fail because a fixture is unavailable; that is not proof
of a product permission defect. E1 alone cannot pass a case if cleanup failed.
Other modules need their own assertion/fixture/recovery mappings; these permission
checks do not establish discovery, NCPA, report content, performance or E2E coverage.

## Verification

`scripts/verify.sh docs` checks the registry/derived view and isolated Python
contracts. `scripts/verify.sh frontend` type-checks the new config/adapter and runs
`node --test qa/selection.node.mjs` before existing frontend checks. Those Node
tests use Playwright `--list` with no browser or credentials: they prove exact
one-case/five-case collection, no setup dependencies/retries and rejected invalid
selection/private paths. They are harness checks, not live acceptance evidence.
