# Issue #181: Create User Manual and Technical Manual for PinPoint

Branch: `issue-181-manuals-draft`
Status: ready-for-review

## Finish condition

Scope for this session (user request, 2026-11-15): produce a **draft** of both
manuals, each in its own folder under `docs/`. The issue's full checklist is
kept below; items outside the draft are marked out of scope with the reason.

- [x] `docs/User_Manual/User_Manual.md` drafted with sections 2.1 to 2.7 (issue B)
- [x] `docs/Technical_Manual/Technical_Manual.md` drafted with sections 3.1 to 3.12 (issue C)
- [x] Both have title page, version, table of contents, numbered sections, glossary, appendices (issue D)
- [x] Existing `docs/manuals/` guides are linked, not duplicated
- [x] Verified facts, assumptions, recommendations and TBC items are distinguished (issue A, E)
- [x] Screenshot placeholders where no real screenshot exists (issue D)
- [x] Credentials locations only, never values (issue H)
- [x] `AGENTS.md`, `spec files/README.md`, root `README.md`, `docs/manuals/README.md` link the manuals
- [x] `scripts/verify.sh docs` passes

Requirement coverage:

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Deliverable paths `docs/manuals/*.md` | Changed by user request: own folders under `docs/` | `ls docs/User_Manual docs/Technical_Manual` |
| A. Accuracy | Verified/assumption/TBC labelling | Review against specs and `Implementation_Status.md` |
| B. User Manual 2.1-2.7 | User Manual draft | Headings present |
| C. Technical Manual 3.1-3.12 | Technical Manual draft | Headings present |
| D. Formatting | Title page, TOC, glossary, appendices | Read files |
| E. Quality | Draft review | Owner review (pending) |
| F. verify docs, CI green, no AI attribution in PR | verify.sh docs | `scripts/verify.sh docs` |
| G. DOCX/PDF export | Out of scope for the draft | Follow-up after content review |
| G. ERD/diagrams from capstone paper | Out of scope: depends on open #283; Mermaid diagrams drawn from code instead | - |
| H. Installer verification | Out of scope: marked TBC, needs installer maintainers | - |
| H. Lab evidence screenshots | Out of scope: placeholders only | - |
| Two PRs (one per manual) | Changed: one draft PR for both drafts, per user request | - |

## Plan

1. [x] Read required specs and topic guides; note facts per manual section.
2. [x] Write `docs/User_Manual/User_Manual.md`.
3. [x] Write `docs/Technical_Manual/Technical_Manual.md`.
4. [x] Link from `AGENTS.md`, `spec files/README.md`, `README.md`, `docs/manuals/README.md`.
5. [ ] `scripts/verify.sh docs`, then open a draft PR.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Plan | - | - |
| 2 | User Manual draft | - | written |
| 3 | Technical Manual draft, index links | `scripts/verify.sh docs` | green |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs
- Result (first failing lines, or "green"): green
- Hypothesis: -
- Next action (one specific step, not "continue"): owner review of the drafts; then DOCX/PDF export, installer review (TBC items), lab screenshots

## Decisions and notes

- User asked for a draft, each manual in its own `docs/` folder, instead of
  `docs/manuals/`. DOCX/PDF export, installer review, lab screenshots and the
  capstone-paper ERD (#283, still open) are left for follow-up.
