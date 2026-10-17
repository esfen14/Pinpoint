# Notification policy in Settings

Administrators with **settings.system** can open **Settings → System → Notification policy** to choose when Nagios sends alert email. Other users cannot see the System tab or save the policy.

- **Quiet hours:** Add a weekday and start/end in 24-hour `HH:MM` format. These times use the **Nagios server's local time**, not your browser's display time zone. A window must start before it ends; split an overnight window into two weekdays. Windows on the same day cannot overlap. An empty list allows notifications at all hours.
- **Host and service states:** Select which state changes notify. Keep at least one choice in each group.
- **Renotify interval:** Set 0–1440 minutes. Zero disables repeated notifications; the default is 30 minutes.

Save applies the change to Nagios after configuration validation. If another administrator saved first, reload the policy before retrying. A failed Nagios apply leaves the previous policy in place and displays the error. Existing contacts still require an Active account with **Send this user email alerts** enabled, and delivery requires mail transport configured under **Settings → Email**.

The **Show notification bell in the header** switch on the General tab only controls the in-app bell. It does **not** switch off Nagios alert email. The default notification policy has no quiet hours, uses the historical host/service state options, and preserves the existing generated configuration.

## Parent outages and temporary child DOWN alerts

With manual parent relationships, a parent outage can briefly produce a **DOWN**
alert for a child before Nagios classifies it as **UNREACHABLE**. Pinpoint accepts
this behavior (Option A for [#173](https://github.com/esfen14/Pinpoint/issues/173));
it does not guarantee immediate suppression of child DOWN notifications.

For example, a router fails and its child stops responding. Nagios may still use
a recent cached UP result for the router and initially classify the child DOWN.
With **Maximum check attempts = 1**, the first failed child check can immediately
become a confirmed HARD problem and send a notification, subject to the existing
notification policy. Updating the classification does not undo an alert already sent.

As subsequent checks update reachability, a child that still fails its check is:

- **UNREACHABLE** when all configured parents actually included in Nagios are DOWN
  or UNREACHABLE.
- **DOWN** when at least one of those parents is UP.

A child that responds again becomes **UP**. UNREACHABLE describes the unavailable
network path; it is not the UNKNOWN plugin/service state. There is no fixed wait
before the classification changes. A paused or otherwise omitted parent does not
participate in Nagios reachability decisions.

When investigating several alerts, check the parents and the latest child state
before treating each child DOWN notification as a separate device failure. In
**Settings → System**, prefer the default **Maximum check attempts = 3** for
failure confirmation. The three-attempt routed trial avoided the transient child
DOWN notification, but that result is not a guarantee for every timing/cache
configuration. One attempt remains supported for operators who accept this quirk.

**Check interval** controls scheduled monitoring frequency; **Retry interval**
controls retries during failure confirmation. Discovery scanning and Pinpoint's
**Data polling interval** are separate. Parent relationships do not automatically
stop child checks. This decision changes no cache, check, retry or notification
settings, and does not change monitoring for devices without eligible parents.
