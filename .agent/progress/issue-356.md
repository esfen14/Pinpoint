# Issue #356: Device Inventory cannot dismiss a duplicate identity review for devices that are separate machines

Branch: `issue-356-dismiss-identity-review`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] The review kinds that can be dismissed are decided and stated in `spec files/Device_Inventory_Requirements.md`.
- [ ] A user with `system.hosts.edit` can dismiss such a review from the page; both records are unchanged, and the list and count refresh without a reload. A user without that permission does not get the action.
- [ ] A failed request shows an error and leaves the review listed.
- [ ] A dismissed review does not come back on a later scan of the same situation, with a regression test.
- [ ] `docs/manuals/Device_Identity_Review.md` and `spec files/Implementation_Status.md` no longer say the page cannot dismiss a review.
- [ ] `scripts/verify.sh all` passes.
- [ ] (added by owner decision) The action is labelled "Keep both records" and asks for confirmation: both records listed, nothing changes on either device, the review will not return, no undo.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Explicit action in the comparison drawer, keeps both records | 2 | `client/src/test/DeviceIdentityReview.test.tsx` |
| Decide which kinds get the action | 1 | spec section 14; frontend test per kind |
| A dismissed review must not come back for any kind that offers it | 4 | `server/tests/unit/test_device_identity.py` |
| Wording and confirmation, no undo | 7 | frontend test |
| Opening, closing, cancelling still never resolve; spec states the new action | 1, 7 | frontend test; spec section 14 |
| Not in issue: discovery matching changes, undo merge | out of scope | diff review |

## Plan

1. [x] Server test then fix: a resolved duplicate identity review is not raised again (cross-network holder case, hardware-MAC holder case, secondary-address case, clone pair that moved). `server/tests/unit/test_device_identity.py`, `server/app/network_discovery/device_identity.py` (`add_review_item`)
2. [ ] Frontend tests then action and confirmation in the drawer, permission, error, refresh. `client/src/test/DeviceIdentityReview.test.tsx`, `IdentityReviewDrawer.tsx`, `DeviceIdentityReviews.tsx`, `lib/deviceIdentityApi.ts`
3. [ ] Refresh the page's list when dismissed from the host drawer. `StatusDetailDrawer.tsx`, `pages/DeviceInventoryPage.tsx`, their tests
4. [ ] Docs: `spec files/Device_Inventory_Requirements.md` section 14, `Frontend_Modules_and_Routes.md`, `Backend_Modules_and_Routes.md`, `Data_Model_and_Integrations.md`, `Implementation_Status.md`, `docs/manuals/Device_Identity_Review.md`
5. [ ] Injection and secret-exposure review of the `network_discovery` change; `scripts/verify.sh all`

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan | - | - |
| 1 | Server tests, then `find_dismissed_duplicate()` | pytest identity + routes | red 2 failed (cross-network, MAC holder), then 166 passed |

## State for the next session

- Last check run (exact command): `cd server && .venv/bin/python -m pytest tests/unit/test_device_identity.py tests/unit/test_device_identity_routes.py -q`
- Result (first failing lines, or "green"): green
- Hypothesis: n/a
- Next action (one specific step, not "continue"): write the failing frontend tests (plan step 2).

## Decisions and notes

- Owner, 2026-11-26: only DUPLICATE_IDENTITY gets the action; label "Keep both records" with confirmation.
- No AI attribution in commits or PR text (owner rule).
- `app/network_discovery/` is a sensitive module (Engineering_Standards).
- Branch `issue-181-manuals-draft` moves the manual to `docs/User_Manual/guides/`; expect a merge conflict.
- Owner, 2026-11-26: approved the `add_review_item()` change in `app/network_discovery/`.
- Owner, 2026-11-26: a one-record duplicate identity review gets the same action worded "Keep record unchanged".
- Recurrence confirmed by test for the two "kept the known device" cases; the secondary-address case does not recur.
