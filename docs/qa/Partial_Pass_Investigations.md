# Partial-pass investigations

A human-recorded partial pass requires investigation and a durable issue or
existing-issue disposition. It is neither a whole-case PASS nor proof that every
expectation failed. Preserve the original catalog result and executor attribution.
This register records evidence review, not a new runtime test run.

| Current case | Original observation | Disposition | Next action |
|---|---|---|---|
| TC-ACK-05 | Human reports no prompt before removing acknowledgement | [#208: reported defect](https://github.com/esfen14/Pinpoint/issues/208) | Verify confirmation and cancellation across all acknowledgement surfaces in an explicitly started, reviewed live queue; attach evidence and follow normal finding/retest rules |
| TC-REM-04 | Human recorded `PARTIALLY PASS -` without a reason | [#209: evidence clarification](https://github.com/esfen14/Pinpoint/issues/209) | Recover the failed expectation/observation, account role, target version and evidence; otherwise prepare the missing checks for authorized execution |

Source: [current human catalog](Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md),
the detailed results for these exact IDs. The original run date, deployed revision
and attached runtime evidence are unknown; do not invent them.

For TC-ACK-05, [Display Requirements §4.6](../../spec%20files/Display_Requirements.md)
requires confirmation. Source inspection at revision
`9e8d7f1baaf85f56aa3e78c59da6b523a964886b` found direct removal requests in
DashboardPage, DeviceInventoryPage, SystemStatusPage and StatusDetailDrawer. This
corroborates the human report but does not constitute fresh runtime reproduction.

For TC-REM-04, source inspection at the same revision found UI permission guards
and backend `remediation.manage` checks. The historical
[issue #182 report](../test-runs/2026-10-17-issue-182-playwright/REPORT.md) contains view-only
checks (RR-12c), which cannot explain the blank human partial verdict or establish
a current whole-case PASS. No permission bypass is asserted.

## Required disposition procedure

1. Read each expected item, the human note, relevant specifications and attached
   reports. Record unknown dates, versions and observations explicitly.
2. Search open and closed issues. Link a matching issue; otherwise file an
   attributed reported defect when the observation identifies a requirement gap.
   An unexplained partial needs an evidence-clarification/`needs-decision` issue,
   not an invented defect. Include current case ID and evidence links.
3. Record issue URL, investigation findings and next action here or in a linked
   successor register. Do not silently exclude partials from all follow-up.
4. If live checks are needed, prepare a separate reviewed `recheck` queue with
   complete cards and explicit start. Apply the normal repeat, safety and evidence
   rules before using `qa-found`; code inspection alone does not meet those rules.
5. Keep the original human partial unchanged. Record subsequent runtime results
   in a separate attached test-run report. Close a defect only with appropriate
   fix/retest evidence; close an evidence question with its documented disposition.

`qa_queue.py prepare --purpose investigate` selects only catalog partial verdicts
by module or explicit ID. Conflicted verdicts remain `needs-decision`. Accepted
historical credit cannot erase a partial from this investigation purpose. The
preview identifies the review-only scope, and `qa_execute.py` rejects opening a
product case from it. The tool does not file issues or claim investigation is done.

Partial **historical evidence coverage** is different: an old report covering only
some expectations leaves missing coverage; it is not by itself a product defect.
See [historical evidence review](Historical_Evidence_Review.md).
