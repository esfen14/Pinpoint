# System logs

This guide covers the **System Logs** page: the audit logs of what people and the system did in Pinpoint, and the Nagios log tab.

> **Verification status.** Written on 2026-11-14 from the route specification and `SystemLogsPage.tsx`. It has not yet been followed step by step on a demo build; items marked **TBC** need that check, and screenshots are not included yet.

## Purpose

Use System Logs to answer "who changed this, and when?" and to export that record. It is not the alert history; for alerts and notifications see [Alerts and notification history](Alerts_and_Notification_History.md).

## Prerequisites

- The **system.logs** permission (the page is hidden without it).
- Audit logging on under **Settings → Security → Audit Logging**; otherwise new events are not recorded. **TBC:** which categories this setting covers.

## Read the logs

1. Open **System Logs** (`/system-logs`).
2. Choose a tab: **Activity Log**, **Configuration Change**, **Network Discovery**, **NCPA Deployment**, **Export Log** or **Nagios log**.
3. Type in **Search** to filter by text. Use the two date boxes (from and to) to limit the period. **Clear** removes all three filters.
4. The list shows **Activity**, **Timestamp** and **Tag ID**. Select a row to see its detail on the right.
5. In the detail panel, use the export control to download that entry. **TBC:** the file formats offered. Close the panel with the button beside it.

Expected result: newest events first, shown in the date format and time zone chosen under **Settings → General**.

## Nagios log tab

The **Nagios log** tab shows a bounded excerpt of the Nagios Core log, not the whole file. For its size limits, retention and the full file on the server, see [Storage and Nagios logs](Storage_and_Nagios_Logs.md).

## Troubleshooting

- **"No logs match your search or filter":** clear the filters, then widen the dates.
- **A red banner with an error:** the server could not load that tab; reload. The Nagios tab reports its own errors.
- **Older entries are missing:** logs are removed after the **System Log Retention** period under **Settings → System**.

## Precautions

- Logs can contain email addresses and host names. Treat exports as confidential.
- Do not edit or delete log files on the server to "tidy up"; the retention setting does that safely.
