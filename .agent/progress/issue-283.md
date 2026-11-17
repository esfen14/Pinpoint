# Issue #283: System Refinement Add hand-off scaffolding: LICENSE, ERD, architecture diagram, docs index and contacts list

Branch: `issue-283-handoff-scaffolding`
Status: in-progress
<!-- Status is one of: in-progress | blocked | ready-for-review -->

Base branch: `issue-181-manuals-draft` (owner decision: this work merges there, not `main`; open the PR with `--base issue-181-manuals-draft`).

## Finish condition

- [ ] `LICENSE` is GPL-3.0, marked provisional on the hand-off page.
- [ ] A generator reads the SQLAlchemy models and writes `docs/reference/ERD.md`: overview (all tables, relationships, no columns) plus one full-column diagram per domain, each with a purpose line.
- [ ] A backend unit test fails when `docs/reference/ERD.md` is stale or a table has no domain.
- [ ] Technical Manual section 6.3 links to `docs/reference/ERD.md`; the capstone-paper TBC is replaced by a differences list (paper: Chapter 3, Figure 4).
- [ ] Hand-written Mermaid architecture diagram, cited to the paper (Chapter 4, Figure 61), checked against `System_Overview_and_Architecture.md`, differences listed.
- [ ] Mermaid example deployment diagram: documentation addresses only, generic zones, no site topology or port assignments.
- [ ] `docs/manuals/README.md` checked and updated as the manual index.
- [ ] Hand-off page: installer repo, secret locations (paths only), contacts as GitHub handles only (maintainers and installer maintainer), To Be Confirmed list (ownership and final license, `python3-nmap` GPL-3.0 constraint, installer bundling of Nagios, plugins, Nmap).
- [ ] All of the above linked from root `README.md`, `docs/README.md` and `spec files/README.md`.
- [ ] Root README "Before you open a pull request" section (`scripts/verify.sh all`, three blocking CI jobs `docs`, `backend`, `frontend`, link to `Agent_Workflow_and_CI.md`).
- [ ] `CONTRIBUTING.md`: one-line command plus link; no failure table copy.
- [ ] `scripts/verify.sh all` green.

Requirement coverage (every requirement the issue states, and the check that proves it):

| Issue requirement | Finish-condition item | Proof (test or command) |
|---|---|---|
| Add LICENSE (provisional GPL-3.0) | LICENSE | `head -3 LICENSE`; hand-off page note |
| ERD, checked against the three model files, differences listed | Generator, ERD.md, differences list | `pytest tests/unit/test_erd_doc.py` |
| ERD stays current (decision) | Stale-file test | same test |
| Architecture diagram checked against the spec | Architecture diagram | doc review against `System_Overview_and_Architecture.md`; `check_doc_links` |
| Example network diagram, no site details (decision) | Example deployment | grep for RFC 5737 addresses only; no `192.168.` literal |
| `docs/manuals/README.md` index | Manuals index | `check_doc_links` |
| Hand-off page with installer, secret locations, contacts, TBC | Hand-off page | file review; grep for no secret values |
| Links from three READMEs | Links item | `check_doc_links` |
| Contributor path to green CI, CONTRIBUTING.md | README section, CONTRIBUTING | `check_doc_links` |
| Done when: IT reader finds everything from root README | Links item | read root README |

## Plan

1. [ ] ERD generator and test, test first: `server/scripts/generate_erd.py`, `server/tests/unit/test_erd_doc.py`, `docs/reference/ERD.md`. Domain map in the generator; the test fails on an unassigned table.
2. [ ] ERD differences vs the paper (Chapter 3, Figure 4) from the model files; Technical Manual 6.3 links to ERD.md: `docs/reference/ERD.md`, `docs/Technical_Manual/Technical_Manual.md`.
3. [ ] Architecture and example deployment diagrams: `docs/reference/Architecture_Diagrams.md`; read `System_Overview_and_Architecture.md`, Technical Manual 1.4, 2.4, 2.6, 2.7 and port table.
4. [ ] LICENSE (GPL-3.0 text from `/usr/share/common-licenses/GPL-3`): `LICENSE`.
5. [ ] Hand-off page: `docs/Hand_Off.md`; secret locations from `server/app/secrets_store.py`, `server/config.py`, `.env` handling.
6. [ ] `CONTRIBUTING.md`, root README "Before you open a pull request" section, links from `README.md`, `docs/README.md`, `spec files/README.md`; check `docs/manuals/README.md`.
7. [ ] Spec upkeep: `spec files/README.md` index, `Implementation_Status.md` if needed; `scripts/verify.sh docs`.
8. [ ] `scripts/verify.sh all`, delete progress file, open PR with `--base issue-181-manuals-draft`.

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | Plan written | none | n/a |

## State for the next session

- Last check run (exact command): none yet
- Result (first failing lines, or "green"): n/a
- Hypothesis: `db.metadatas` (Flask-SQLAlchemy 3.1) gives tables per bind without a database
- Next action: write `server/tests/unit/test_erd_doc.py` and watch it fail (no generator, no ERD.md)

## Decisions and notes

- License: provisional GPL-3.0 because the backend imports GPL-3.0 `python3-nmap` (`nmap3`). Final license depends on code ownership (state university, CHED, RA 8293, RA 10055, university IP policy); the capstone adviser answers. Recorded as To Be Confirmed.
- Diagrams are Mermaid text, not images. The paper is cited only: ERD Chapter 3 Figure 4, architecture Chapter 4 Figure 61. The paper has no network diagram, so that one is an example deployment (RFC 5737 addresses, generic zones, protocol labels pointing to the Technical Manual port table).
- Contacts are GitHub handles only (maintainers, installer maintainer `lorraine-pangilinan`); no personal emails. Which collaborators count as maintainers is to confirm with the owner.
- Secrets: paths only, never values. Installer-managed secrets marked TBC.
- Out of this issue: replacing `python3-nmap` (new issue only if the university refuses GPL-3.0); subnet default change is #334.
