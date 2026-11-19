# Issue #181: Create User Manual and Technical Manual for PinPoint

Branch: `issue-181-manuals-draft`
Status: in-progress

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

## Remaining work (tracking list)

Issue items still open after the draft (PR #333, draft). Tick here and in
issue #181 together.

### Owner decisions needed
- [x] Export tool: Pandoc (decided 2026-11-19). **Owner still to run `sudo apt install pandoc`**
- [x] Mermaid: render with `npx @mermaid-js/mermaid-cli` at export time (decided 2026-11-19)
- [x] Commit trailers: drop `Co-Authored-By` from now on (decided 2026-11-19; commits `a5fac04e` and `5dbd91b3` keep theirs unless rewritten)
- [x] One PR (#333) for both manuals (decided 2026-11-19); amend the issue's checklist to say so
- [ ] Confirm the folder change (`docs/User_Manual/`, `docs/Technical_Manual/` instead of `docs/manuals/`); then amend the issue's Deliverables paths

### Printable export (issue section G)
- [ ] `scripts/export_manuals.sh`: Markdown -> DOCX (Pandoc, `--toc`, `reference.docx`) -> PDF (`soffice --headless`)
- [ ] `reference.docx` template: fonts, margins, spacing, page numbers, title page
- [ ] Rewrite relative links as printed repo-path notes (Pandoc Lua filter), or include linked guides as appendices
- [ ] Wide tables fit the page (landscape sections or smaller font)
- [ ] Document the export command and template in `docs/manuals/README.md`
- [ ] Produce DOCX and PDF of each manual

### Diagrams (issue section G, depends on #283)
- [ ] Embed the ERD and architecture diagrams at print resolution: they are Mermaid in `docs/reference/` (from #283 work); render in the export step
- [x] Compared with the models and `System_Overview_and_Architecture.md`: the ERD is generated from the schema and the differences from the paper are listed in Technical Manual section 6.3
- [x] Image-path check: `scripts/verify.sh docs` already fails on a missing image path (it caught one during the screenshots work)

### Installer verification (issue section H; ask @lorraine-pangilinan)
- [x] Technical Manual §8: installer steps in order, upgrade command, health check (read from the public installer repo 2026-11-19)
- [x] §5: no host firewall, no HTTPS, address chosen in the Ubuntu installer, Nginx site written by `deploy-pinpoint-web.sh`
- [x] §8.4: bootstrap login in `/root/pinpoint-install-credentials.txt`; NCPA key `/opt/pinpoint/.ssh/pinpoint_ncpa_deploy`, token in `system.db`
- [x] Nagios systemd unit name is `nagios`
- [ ] Installer maintainer to confirm these (read from the repository, not run on production)

### Lab evidence (issue section H, Evidence)
- [x] Screenshots captured 2026-11-19 on the QA appliance (`demo/demo qa create`, branch `issue-181-manuals-draft`, 14 demo containers); the User Manual had four placeholders (UM-01 to UM-04), plus 22 guide figures. Regenerate with `docs/images/manual/README.md`
- [ ] Hardware sizing and bandwidth figures from a named appliance (Technical Manual §3.1, §5.8)
- [ ] Follow each User Manual procedure on a demo build and clear its TBCs (worklist: `docs/plans/TEMP_TBC_Worklist.md`, group A)

### Open TBC questions
- [ ] User Manual Appendix C (8 items: browsers, HTTPS, Remember me, Manager/Staff permissions, self-service password change, sidebar order, support contact, screenshot appliance)
- [ ] Technical Manual Appendix B (11 items)

### Review-only items (need a reviewer, not more writing)
- [ ] A: nothing invented; every TBC marked; every claim checked against code or `Implementation_Status.md`
- [ ] E: comprehensive, beginner-friendly, technically accurate, easy to follow, maintainable, security-conscious, system-specific, usable by every audience

### Before the PR leaves draft
- [ ] `scripts/verify.sh all`
- [ ] Delete this progress file (`git rm .agent/progress/issue-181.md`); CI rejects a ready PR that still has it

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 1 | Plan | - | - |
| 2 | User Manual draft | - | written |
| 3 | Technical Manual draft, index links | `scripts/verify.sh docs` | green |
| 4 | Draft PR #333 opened; CI green; issue checkboxes ticked; remaining-work list added | `gh pr checks 333` | pass |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs
- Result (first failing lines, or "green"): green
- Hypothesis: -
- Next action (one specific step, not "continue"): get the owner decisions in "Remaining work", then write `scripts/export_manuals.sh`

## Decisions and notes

- User asked for a draft, each manual in its own `docs/` folder, instead of
  `docs/manuals/`. DOCX/PDF export, installer review, lab screenshots and the
  capstone-paper ERD (#283, still open) are left for follow-up.
