# Issue #342: Web-Interface: Toggle sidebar button does nothing

Branch: `issue-342-sidebar-toggle`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

## Finish condition

Copied from the issue. Tick an item only when a check proves it.

- [ ] The button hides and shows the sidebar, and the content area follows.
- [ ] Decide whether phone screens are supported (decided: not supported).
- [ ] A frontend test covers the toggle.
- [ ] Manuals match the result (deferred to PR #333; see notes).

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Button hides/shows sidebar, content follows | 1 | `SidebarToggle.test.tsx`, browser check |
| Phone support decision | 2 | `spec files/Frontend_Modules_and_Routes.md` |
| Frontend test | 3 | `SidebarToggle.test.tsx` |
| Share state through context, not a window event (code comment in `Header.tsx`) | 1 | `git grep nds:toggle-sidebar` is empty |
| Pages fit phone width, if phones supported | not applicable | decided unsupported |
| User Manual and Technical Manual 4.6 | 4 | out of this PR; wording given in the PR body |

## Plan

1. [ ] Failing test: `client/src/test/SidebarToggle.test.tsx`
2. [ ] `contexts/SidebarContext.tsx`; wire `AdminLayout`, `Header`, `Sidebar`
3. [ ] Move the sidebar offset into `AdminLayout`; remove it from `pages/*.tsx` and `MaintenanceBanner.tsx`
4. [ ] Specs: `Frontend_Modules_and_Routes.md`, `Implementation_Status.md`
5. [ ] Browser check of hidden/shown layout, then `scripts/verify.sh all`

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| | | | |

## State for the next session

- Last check run (exact command): none
- Result (first failing lines, or "green"): n/a
- Hypothesis: nothing listens for the toggle event; 17 files hardcode the offset
- Next action (one specific step, not "continue"): write `SidebarToggle.test.tsx`

## Decisions and notes

- Phone screens: not supported (user decision, 2026-11-25).
- Manuals do not exist on `main`; they are in draft PR #333 (#181). User decided to defer:
  this PR gives the wording, and does not edit that branch.
- The issue has no comments; "the comment" is the one above the button in `Header.tsx`.
