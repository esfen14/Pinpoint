# Email settings

Open **Settings → Email** with the **settings.email** permission. One shared
SMTP account sends Pinpoint's alert email for the whole system.

For **Gmail**, keep the supplied host, port and STARTTLS security. Enter the full
Gmail address and a Google app password. The tab links to app-password setup;
Gmail uses the signed-in account as the From address.

For **Other SMTP relay**, obtain these settings from your mail administrator or
provider:

- **Host:** the SMTP submission hostname or IPv4 address, without a URL scheme,
  spaces or a port suffix. IPv6 literals are unavailable in the existing helper.
- **Port:** a whole number from 1 to 65535, usually 587 for STARTTLS.
- **Security:** STARTTLS. The relay must offer it and present a certificate trusted
  by the appliance. Selecting port 465 does not enable implicit TLS.
- **Username:** the relay login name, which can differ from the sender address.
- **Sender:** an email address this account is allowed to send from.
- **Password:** the relay password, app password or SMTP token required by the
  provider. Consult the provider's account and administrator restrictions.

Save the settings, then use **Send test email**. It sends to your signed-in
account's email address using the saved configuration. Confirm arrival in that
inbox or its spam folder. A successful send means the SMTP server accepted the
message; it does not prove inbox delivery.

The password is never returned to the browser. Leave it blank on later saves to
keep the saved credential. This also applies when switching providers; enter a
replacement whenever the new relay uses different credentials. Entered passwords
are cleared after a successful save. **Discard Changes** restores saved values.

A **Last notification failure** notice gives the latest failure time and a safe
reason. Its link jumps to the test-email controls; save edits before testing. The
notice refreshes every 30 seconds while the tab is open. It records a past Nagios
notification failure, so a successful test does not clear it. It disappears when
the current log tail has no matching failure, including after rotation. No notice
can also mean the log is unavailable; absence does not establish delivery health.

Ask the appliance operator to check `NAGIOS_LOG_FILE` and read access for the
Pinpoint service user if a known failure is absent. The application reads only a
bounded current log tail and does not expose raw notification text.

No installer update, database migration, or permission synchronization is needed
for this STARTTLS change on an appliance with the existing SMTP helper. Implicit
TLS, plaintext SMTP and OAuth are unavailable. Microsoft 365 support remains
outside this change. If another administrator saves first, reload before retrying
so you do not overwrite their settings.
