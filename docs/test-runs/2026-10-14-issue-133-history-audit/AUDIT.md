# Issue #133 — History page requirements audit (source/isolated-test review)

Compared `spec files/Alerts_Notifications_History_Requirements.md` against `client/src/pages/HistoryPage.tsx`, `server/app/api/system/history.py`, access wiring, and `client/src/test/HistoryPage.test.tsx`. This is **not** a live appliance run. Results describe the implementation, not observed lab behavior. Backend-dependent findings are tracked separately; they are not fixed in #133.

| Requirement | Evidence | Result |
|---|---|---|
| §1 permission: hide nav, deny direct URL, distinct from ack, default role grant | `pageAccess.ts`, `Sidebar`, `PageAccessGuard`; `HistoryPage.test.tsx` guard; backend `@require_permission("system.history")`; role seed | Met in code; default-role grant not verified live |
| §2 two tabs, shared filter bar, table, expandable detail | `HistoryPage.tsx` tabs, filter bar, tables, expanded rows | Met |
| §3.1 every state-change event, not current snapshot | `history.py` `request_alerts_range` uses archivejson; list test | Met in code |
| §3.1 timestamp, type, host, service columns | Alerts table; `Timestamp` relative with absolute hover | Met |
| §3.1 previous/new state, soft/hard, previous duration, truncated output | Alerts table; API `fill_previous_states`, `duration_seconds`, output slice | Partly met: incomplete prior-state/duration at window boundaries [#144](https://github.com/esfen14/Pinpoint/issues/144) |
| §3.1 acknowledgement badge for this event's active episode | `Acked` badge and `history.py` `build_ack_map` keyed only by target | Partly met: earlier episode falsely marks later event [#141](https://github.com/esfen14/Pinpoint/issues/141) |
| §3.2 full output; ack user/time/comment | Alert expansion; detail endpoint returns full output and latest ack by target | Partly met: wrong ack possible across episodes [#141](https://github.com/esfen14/Pinpoint/issues/141) |
| §3.2 recovery duration from first detection | Alert expansion displays `recovery_duration`; API copies archive duration | Partly met: no reliable first-detection duration [#144](https://github.com/esfen14/Pinpoint/issues/144) |
| §3.2 associated notifications | Alert detail lists `linked_notifications` from ±5 min; tab navigation added | Partly met: proximity only, no exact event identity [#143](https://github.com/esfen14/Pinpoint/issues/143) |
| §3.3 time presets 1h/6h/24h/7d/30d | `PRESETS`, `buildQuery`, backend `resolve_time_range` | Met |
| §3.3 custom date/time range | Page has date-only inputs; backend `get_range_custom` accepts YYYY-MM-DD | Partly met: time-of-day unavailable [#142](https://github.com/esfen14/Pinpoint/issues/142) |
| §3.3 type, host, service, new state, ack, state type; simultaneous filters | `buildQuery` sends all active filters; tests combined type/host/ack | Partly met: ack association is wrong across episodes [#141](https://github.com/esfen14/Pinpoint/issues/141) |
| §3.4 default timestamp descending; any-column sort; timestamp-desc tie break | Page now has controls for backend-supported time, host, state, duration; API supports four keys | Partly met: other columns and tie break absent [#142](https://github.com/esfen14/Pinpoint/issues/142) |
| §3.5 25/50/100, total count, pagination | Rows-per-page select, showing range, shared Pagination; test changes per_page | Met |
| §4.1 Nagios notification event and columns time/type/host/service/state/contacts/method/truncated message | `history.py` archive query and `HistoryPage.tsx` notification table | Met in code |
| §4.2 full message, contacts, related alert link | Notification expansion shows full message, contacts and tab button | Partly met: button filters target but cannot navigate exact row [#143](https://github.com/esfen14/Pinpoint/issues/143) |
| §4.3 time presets, custom date/time, type, host, service, state, contact | Notification controls and query; date-only custom inputs | Partly met: date/time precision [#142](https://github.com/esfen14/Pinpoint/issues/142) |
| §4.4 same sorting/pagination/default descending | Shared pagination and supported sort controls, default API timestamp-desc | Partly met: not every column or secondary tie break [#142](https://github.com/esfen14/Pinpoint/issues/142) |
| §5.1 no-match clear shortcut; no-data explanation | Empty row conditions in `HistoryPage.tsx`; test empty state | Met (notifications use a notification-specific empty message) |
| §5.2 manual Refresh, last loaded, no auto-refresh | Refresh and `loadedAt`; only effect on query changes | Met |
| §5.3 relative and absolute timestamps, viewer local zone | `Timestamp` relative/hover, `useDisplayTime` absolute and detail | Met; follows user display-zone preference (Browser is local) |
| §5.4 alert ↔ notification links | New alert detail button and existing notification detail button | Partly met: target filtering only; exact event support [#143](https://github.com/esfen14/Pinpoint/issues/143) |
| §6 exclusions: exports, edits, live feed, status, contacts, downtime | No such controls on History page | Met |
| Pinpoint scan source extension beyond Nagios-only §4 | Source badge/filter and detail route; `HistoryPage.test.tsx` Nagios/Pinpoint | Met (additional supported source) |

No live/manual verification was performed. Do not treat this table as an acceptance run on an appliance.
