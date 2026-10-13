# Notification policy in Settings

Administrators with **settings.system** can open **Settings → System → Notification policy** to choose when Nagios sends alert email. Other users cannot see the System tab or save the policy.

- **Quiet hours:** Add a weekday and start/end in 24-hour `HH:MM` format. These times use the **Nagios server's local time**, not your browser's display time zone. A window must start before it ends; split an overnight window into two weekdays. Windows on the same day cannot overlap. An empty list allows notifications at all hours.
- **Host and service states:** Select which state changes notify. Keep at least one choice in each group.
- **Renotify interval:** Set 0–1440 minutes. Zero disables repeated notifications; the default is 30 minutes.

Save applies the change to Nagios after configuration validation. If another administrator saved first, reload the policy before retrying. A failed Nagios apply leaves the previous policy in place and displays the error. Existing contacts still require an Active account with **Send this user email alerts** enabled, and delivery requires mail transport configured under **Settings → Email**.

The **Show notification bell in the header** switch on the General tab only controls the in-app bell. It does **not** switch off Nagios alert email. The default notification policy has no quiet hours, uses the historical host/service state options, and preserves the existing generated configuration.
