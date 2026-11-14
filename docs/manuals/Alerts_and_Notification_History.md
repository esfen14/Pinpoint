# Alerts and notification history

The **History** page is the record of what happened: every state change of a host or service, and every notification Nagios sent. Use it to answer "when did this go down, for how long, and who was told?" The Dashboard and Network Health answer "what is wrong right now".

> **Verification status.** Written on 2026-11-14 from `Alerts_Notifications_History_Requirements.md`, `HistoryPage.tsx` and the route specification. It has not yet been followed on a demo build; items marked **TBC** need that check, and screenshots are not included.

## Purpose

- **Alerts History:** a chronological log of state changes (for example OK to CRITICAL, then back to OK).
- **Notifications History:** the contact events Nagios sent for those changes.

## Prerequisites

- The **system.history** permission ("View Alert & Notification History"). Without it the page is hidden and a direct address is refused. It is separate from the permission to acknowledge alerts.
- Nagios must be running and reachable: history comes from Nagios's archive, not from Pinpoint's own database, so a stopped Nagios shows an error or an empty page.

## Find an event

1. Choose **History** in the sidebar. The **Alerts History** tab opens, newest first.
2. Choose a time range with the presets (last 1 hour, 6 hours, 24 hours, 7 days or 30 days), or enter a custom start and end date. **TBC:** whether the page offers a time of day for custom ranges; the server accepts date-times but the page may offer dates only.
3. Narrow the list with the filters: **Type** (all, host, service), **Host**, **Service**, **New state** (OK/UP, WARNING, CRITICAL/DOWN, UNKNOWN/UNREACHABLE), **Acknowledged** (all, acknowledged only, unacknowledged only) and **State type** (hard or soft). All filters apply together.
4. Sort by choosing a column heading. The default is timestamp, newest first.
5. Choose 25, 50 or 100 rows per page. The count of matching events is shown above the table.

Expected result: one row per state change with timestamp, type, host, service (blank for a host), previous state, new state, soft or hard, how long it was in the previous state, a short plugin output, and an **Acknowledged** badge.

## Read one alert in detail

Select a row to expand it. The detail shows:

- the full plugin output;
- if the problem was acknowledged while it was active: who, when and the comment;
- for a recovery: the total time from the first problem to the recovery;
- notifications Nagios sent for that alert, with a link to the **Notifications History** tab.

Notes:
- A problem and its recovery form one **episode**. An acknowledgement belongs to the episode it was made in; a later problem on the same device starts unacknowledged.
- Soft states are checks that have not yet reached the maximum number of attempts (**Settings → System → Maximum check attempts**); only hard states send notifications.
- For events near the start of the chosen range, the previous state and duration may be incomplete when Nagios has no earlier record **TBC**.

## Notifications History

1. Choose the **Notifications History** tab.
2. Use the same time presets and the filters **Type**, **Host**, **Service**, **State** (at the time of the notification) and **Contact**.
3. Select a row to see the full message, every contact notified, and a link to the matching alert.

Expected result: one row per notification with timestamp, type, host, service, state, contact, method and a short message.

Pinpoint's own events (a finished network scan) also appear here, shaped like notifications.

## Jump between an alert and its notification

Use the link in the expanded row. The page switches tab, finds the exact event even if it is outside the current time range, and expands it. A link appears only when a match exists: a notification matches the most recent earlier alert for the same host, service and state within five minutes.

## Refresh and time display

- The page does not refresh by itself. Choose **Refresh** to reload; the time of the last load is shown.
- Times show relative ("3 hours ago") with the exact time on hover or in the detail, in the time zone chosen under **Settings → General → Time Zone**.

## Precautions and troubleshooting

- **No events match the current filters:** choose the clear-filters shortcut, or widen the range.
- **No alert history yet:** history appears as hosts and services change state; a new installation starts empty.
- **A notification is missing:** quiet windows, maintenance windows, acknowledgements and the notification policy suppress notifications. See [Notification policy](Notification_Policy.md) and [Maintenance windows](Maintenance_Windows.md). If email did not arrive, see [Email settings](Email_Settings.md).
- Two Nagios records that are identical to the second cannot be told apart and may open the wrong row **TBC**.
- This page is read-only; acknowledging an alert is done from the Dashboard or Network Health (see [Dashboard and Network Health](Dashboard_and_Network_Health.md)). Reports and exports are in [Service reports](Service_Reports.md).
