# TC-HIS-04 — History API date range rules

## Run identity

| Field | Recorded value |
|---|---|
| Case / requirement | TC-HIS-04 / REQ-HIS-03 |
| Result | **Pass** for the observed API expectations |
| Executor | Codex, AI-assisted API requests using Python urllib; not human manual testing |
| Authorization | User explicitly requested testing TC-HIS-04 in this conversation |
| Execution time | 2026-10-18 17:26:31–17:26:33 UTC; 2026-10-19 01:26:31–01:26:33 Asia/Manila; start is the evidence-directory creation time |
| Plan | [Current case catalog](../../qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md#tc-his-04--date-range-rules-api) |
| Application commit tested | `65a5862c375dd7dfe1dd98433ca017dc4efe0cec`, previously deployed and file-verified during this manual lab setup; not fingerprinted again during these API requests |
| Report checkout | `43f0df103752d485f4cab786ee29ce6a5e049add` with existing user edits to the catalog |
| Catalog SHA-256 | `25d31388b44a3fdd1a4c0f6e011d3043fdfdf10bdb13c3de7c2f0f7f54600cbf` at report import; no catalog hash was captured at execution time |
| Queue / set / session / batch | Individually requested one-case API assessment; no qa_pilot queue, reviewed execution card, supervisor session or automated batch was used |
| Environment | Existing upgraded Pinpoint QA appliance, local forwarded HTTP endpoint, existing Super Admin account, existing Nagios alert history |
| Installer provenance | Base installer `697869e` identified during lab preparation; restricted resource helper installed separately from installer PR 7 commit `b166953d2e7e5b4bae12bf723712224cc97fae94`; full installer manifest not reverified for this check |
| Baseline | Cooperative QA host claim held; existing account authenticated; genuine older alert history available; concurrent human UI activity was not attested absent |
| Raw evidence | Host file `/home/paeng/pinpoint-test-results/TC-HIS-04-20261018T172631Z/observations.json` (not committed) |
| Evidence SHA-256 | `6f29a90600d090669b01d7d0737e0226785fd0b12d8637cb4057f05985ac4275` |

## Result and scope

Unique TC totals: **Pass 1, Fail 0, Partially Pass 0, Blocked 0, Inconclusive 0, Not run 0**. Unique E2E totals: **0**. One attempt; no diagnostic repeat. No historical evidence was reused as a new execution.

| Case | Result | Coverage | Issue |
|---|---|---|---|
| TC-HIS-04 | Pass | Valid pair accepted; incomplete, reversed and malformed pairs rejected; no-date range compared with explicit 24-hour preset and genuine older event | None found |

## Expected-item observations

All requests targeted `/api/system/history/alerts` after authentication.

| Expected item / step | Request / observation | Result |
|---|---|---|
| E1 / step 1 | `start_date=2026-10-01&end_date=2026-10-02`: HTTP 200, success true, an empty items list (permitted by the case) | Pass |
| E2 / step 2 | Only `start_date=2026-10-01`: HTTP 400, success false, no data field | Pass |
| E2 / step 3 | `start_date=2026-10-02&end_date=2026-10-01`: HTTP 400, success false, no data field | Pass |
| E2 / step 4 | `start_date=abc&end_date=def`: HTTP 400, success false, no data field | Pass |
| E3 / default range | No dates and no preset returned 33 events; explicit `preset=24h` returned the same 33 event IDs. Every default event fell within 24 hours, using five seconds of clock tolerance | Pass |
| E3 / older-event control | A genuine archived event with timestamp `1792034109`, found using `preset=30d` sorted oldest first, was over 25 hours old and absent from the default response | Pass |

Invalid requests returned the message: “Invalid time range. Use a preset (1h, 6h, 24h, 7d, 30d) or provide start_date and end_date as YYYY-MM-DD.”

Default and explicit 24-hour responses were collected with pagination, at 100 items per page, rather than checking only the first page. Sanitized HTTP statuses, predicates, counts and the older-event identity are recorded in the private observations file; raw response bodies were not retained.

## Restoration

The script called logout in its `finally` block. It did not retain the logout response, so server-side session invalidation was not independently asserted. Authentication can generate normal activity/audit records. No device, service, fixture, configuration, password, application source or historical test verdict was changed by this assessment. Existing manually prepared lab faults and fixtures were left in place.

## Limits and provenance

- No browser UI was exercised; this catalog case is an API check.
- No event exactly on the 24-hour boundary was created. The evidence supports default/preset equivalence, observed timestamps and exclusion of a known older event.
- Deployment identity is based on the earlier source/build verification in this session, not a fresh execution-time fingerprint.
- This run did not follow the repository's reviewed-card and qa_pilot execution procedure. Its API observations are recorded transparently as an ad hoc user-requested assessment; it is not evidence of supervisor acceptance, queue completion, or launcher readiness.
- Existing manual catalog results remain untouched. This report does not silently promote an AI execution into a human manual result or claim release approval.

## Sanitization

No credentials, tokens, private keys, SNMP communities, raw environment files or full device outputs are included. Raw evidence remains outside the checkout.
