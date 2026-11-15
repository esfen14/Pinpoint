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
- [ ] Install Pandoc (`sudo apt install pandoc`) or choose the HTML -> LibreOffice fallback for export
- [ ] Render Mermaid with `npx @mermaid-js/mermaid-cli` (downloads Chromium) or commit pre-rendered PNGs
- [ ] Commit trailers: drop `Co-Authored-By` to match condition F, or keep (issue section H, Attribution)
- [ ] Merge as one PR or split into the two PRs the issue asks for (User Manual / Technical Manual)
- [ ] Confirm the folder change (`docs/User_Manual/`, `docs/Technical_Manual/` instead of `docs/manuals/`); then amend the issue's Deliverables paths

### Printable export (issue section G)
- [ ] `scripts/export_manuals.sh`: Markdown -> DOCX (Pandoc, `--toc`, `reference.docx`) -> PDF (`soffice --headless`)
- [ ] `reference.docx` template: fonts, margins, spacing, page numbers, title page
- [ ] Rewrite relative links as printed repo-path notes (Pandoc Lua filter), or include linked guides as appendices
- [ ] Wide tables fit the page (landscape sections or smaller font)
- [ ] Document the export command and template in `docs/manuals/README.md`
- [ ] Produce DOCX and PDF of each manual

### Diagrams (issue section G, depends on #283)
- [ ] Embed the capstone paper's ERD, architecture and network diagrams at print resolution once #283 lands
- [ ] Compare them with `system_models.py`, `history_models.py`, `plugin_models.py` and `System_Overview_and_Architecture.md`; list differences
- [ ] Image-path check: `check_doc_links.py` validates only `.md` links; extend it or keep a manual checklist once images exist (section H, Images)

### Installer verification (issue section H; ask @lorraine-pangilinan)
- [ ] Technical Manual §8: installer steps in order, upgrade behaviour, health check
- [ ] §5: ports, host firewall, static address, DNS/DHCP/gateway, production Nginx config, HTTPS
- [ ] §8.4: where the bootstrap admin placeholder login is reported; NCPA SSH key and token locations
- [ ] Nagios systemd unit name (§8.5)

### Lab evidence (issue section H, Evidence)
- [ ] Capture screenshots UM-01 to UM-08 (User Manual Appendix B) on a named appliance; record build, who and when
- [ ] Hardware sizing and bandwidth figures from a named appliance (Technical Manual §3.1, §5.8)
- [ ] Follow each User Manual procedure on a demo build and clear its TBCs

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
