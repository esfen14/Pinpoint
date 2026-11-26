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
- [x] Export tool: Pandoc (decided 2026-11-19). Pandoc is installed
- [x] Mermaid: render with `npx @mermaid-js/mermaid-cli` at export time (decided 2026-11-19)
- [x] Commit trailers: drop `Co-Authored-By` from now on (decided 2026-11-19; commits `a5fac04e` and `5dbd91b3` keep theirs unless rewritten)
- [x] One PR (#333) for both manuals (decided 2026-11-19); amend the issue's checklist to say so
- [x] Folder layout confirmed (2026-11-25): `docs/User_Manual/` and `docs/Technical_Manual/`, each with chapter files and `guides/`; issue #181 paths amended

### Printable export (issue section G)
- [x] `scripts/export_manuals.sh`: Markdown -> DOCX (Pandoc) -> PDF (LibreOffice macro that refreshes the contents list); LibreOffice is run under `env -i` because it crashes with `std::bad_alloc` under this session's environment
- [x] `docs/manuals/export/reference.docx` template: A4, 2 cm margins, Arial, page-number footer, page break per chapter; built by `scripts/manual_export/make_reference.py`
- [x] Relative links rewritten as printed repo-path notes (`scripts/manual_export/prepare.py`); linked guides are not appended
- [x] Wide tables: smaller font and borders (not rotated to landscape)
- [x] Export command documented in `docs/manuals/README.md`
- [x] DOCX and PDF produced for both manuals (User 25 pages, Technical 32 pages) in `build/manuals/`; not committed (git-ignored)
- [ ] Owner to open the DOCX in Word and check the contents list and look (decided 2026-11-25: the PDFs are not committed)

### Diagrams (issue section G, depends on #283)
- [x] Mermaid diagrams render in the export step at 2x scale; the ERD and architecture diagrams in `docs/reference/` are separate files and are not part of the printed manuals (the Technical Manual links to them)
- [x] Compared with the models and `System_Overview_and_Architecture.md`: the ERD is generated from the schema and the differences from the paper are listed in Technical Manual section 6.3
- [x] Image-path check: `scripts/verify.sh docs` already fails on a missing image path (it caught one during the screenshots work)

### Installer verification (issue section H; ask @lorraine-pangilinan)
- [x] Technical Manual §8: installer steps in order, upgrade command, health check (read from the public installer repo 2026-11-19)
- [x] §5: no host firewall, no HTTPS, address chosen in the Ubuntu installer, Nginx site written by `deploy-pinpoint-web.sh`
- [x] §8.4: bootstrap login in `/root/pinpoint-install-credentials.txt`; NCPA key `/opt/pinpoint/.ssh/pinpoint_ncpa_deploy`, token in `system.db`
- [x] Nagios systemd unit name is `nagios`
- [ ] Installer maintainer (Lorraine) to confirm these; the CICT IT team is the installer reviewer. Partly checked on an ISO install 2026-11-25

### Lab evidence (issue section H, Evidence)
- [x] Screenshots captured 2026-11-19 on the QA appliance (`demo/demo qa create`, branch `issue-181-manuals-draft`, 14 demo containers); the User Manual had four placeholders (UM-01 to UM-04), plus 22 guide figures. Regenerate with `docs/images/manual/README.md`
- [x] Hardware sizing and bandwidth figures: tested limit and lab measurements stated (Technical Manual 3.1, 5.8, 10.4)
- [ ] Follow each User Manual procedure on a demo build and clear its TBCs (the TBC worklist was finished and removed on 2026-11-25; not every procedure has been walked through). Walkthrough on the local lab started 2026-11-26; followed: Sign in/accounts/roles, Network discovery, Dashboard and Network Health (each guide's verification note says what was not). Next: Device Inventory. Filed #352 from it

### Open TBC questions
- [x] User Manual open questions answered (now Appendix B in `09_Appendices.md`)
- [x] Technical Manual Appendix B answered; what remains is in its Appendix C

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
| 5 | Walkthrough: sign-in, discovery and Dashboard guides corrected | `scripts/verify.sh docs` | green |

## State for the next session

- Last check run (exact command): scripts/verify.sh docs
- Result (first failing lines, or "green"): green
- Hypothesis: -
- Next action (one specific step, not "continue"): walk through `docs/User_Manual/guides/Device_Inventory.md` on the local lab

## Decisions and notes

- 2026-11-25: the guides are the only place user procedures are written; the
  printed User Manual includes them (`scripts/manual_export/prepare.py`).

- User asked for a draft, each manual in its own `docs/` folder, instead of
  `docs/manuals/`. DOCX/PDF export, installer review, lab screenshots and the
  capstone-paper ERD (#283, still open) are left for follow-up.
