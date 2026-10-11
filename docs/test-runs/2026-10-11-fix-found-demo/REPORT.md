# Fix-found demonstration — corrected synthetic evidence

Correction on 2026-10-11: the earlier report overstated queue skips and completion.
No candidate with `needs-decision` was present, so that skip was not demonstrated.
The original run did not record a tested commit or execute a failing regression.

| Check | Result | Evidence |
|---|---|---|
| Synthetic issue and PR exist | Pass | Issue [#90](https://github.com/esfen14/Pinpoint/issues/90), PR [#91](https://github.com/esfen14/Pinpoint/pull/91); re-read through GitHub on 2026-10-11 |
| Planted workflow input | Pass | The later scratch-only J2-labelled assertion failed identically twice; see `../2026-10-11-qa-loop-planted-run/REPORT.md`. It is not a product defect and was not filed. |
| Required queue skips | Pass (scratch demonstration) | The written queue fixture skips a `qa-found` + `needs-decision` candidate. Issue #90 is skipped after PR #91 exists. The executable workflow contract checks both rules. |
| Scratch retest handoff | Pass | PR #91 was opened without an agent merge, then merged by a human and issue #90 closed. A scratch demonstration row moves to `retest`; the real J2-08 row does not move because PR #91 contains no product fix. |

PR #91 is now merged (`2026-10-11T04:49:41Z`), contrary to the original report's
open-PR claim. It was unmerged when the agent opened it, satisfying the human merge
gate; the later merge supplies the scratch handoff event. This demonstration never
certifies J2-08 or any product fix. Preserve J2-08's independent evidence.
