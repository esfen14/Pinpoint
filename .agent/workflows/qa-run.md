# Workflow: qa-run

Run the finding loop on the QA test plan. The finding loop picks untested or retest cases, executes them against the appropriate target environment, records results, and logs defects. It **never fixes issues**.

## Constraints
- Max 5 rounds per session.
- Keep agent state in `.agent/progress/qa-run.md`. The format and usage mimics `.agent/progress/issue-<n>.md`.
- Never write code fixes during a `qa-run`.
- All failures must be repeated once before filing an issue. Sanitize all evidence.
- Mark newly found defects with label `qa-found`.
- Do not log known gaps documented in `docs/qa/QA_Journeys_and_Scope.md`.
- Use `scripts/vmlab` and `scripts/lab` for VM/Docker environments. Limit network scanning strictly to `10.77.0.0/28`. Use credentials from `.local/share/pinpoint-vmlab-*` but never print them.

## Retest Loop
To find closed fixes ready for retest, use this Github CLI query:
`gh issue list --state closed --label qa-found`
If the issue is closed but its matrix row says `fail-filed`, change the row back to `retest` so `qa-run` will pick it up on the next pass.

## Steps
1. Create or resume `.agent/progress/qa-run.md`.
2. Select next `untested` or `retest` row from `docs/qa/Requirements_Traceability.md`.
3. Follow steps specified for the case in `docs/qa/QA_Test_Plan.md`.
4. If failure occurs, repeat the case execution once to rule out transient flakiness.
5. Record result using `scripts/new_test_run.sh`.
6. If verified failure, file a `qa-found` issue using the Task template and link the case ID.
7. Update the traceability matrix status column accordingly (`pass`, `fail-filed`).
8. Stop condition: "QA done" when every in-scope row is `pass`, `fail-filed`, `needs-decision` or `won't-do`.
