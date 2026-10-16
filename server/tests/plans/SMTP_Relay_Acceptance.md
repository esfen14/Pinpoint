# STARTTLS SMTP relay acceptance

Status: Active issue #115 acceptance procedure.
Specification: [Email settings and transport ownership](../../../spec%20files/Data_Model_and_Integrations.md),
[SMTP routes](../../../spec%20files/Backend_Modules_and_Routes.md), and
[Email settings UI](../../../spec%20files/Frontend_Modules_and_Routes.md).

Use one owned disposable appliance; do not change another tester's shared lab.
The #115 Docker fixture is named `issue-115-smtp-appliance`, labeled
`pinpoint.issue=115`, published only on loopback port 18115, and mounted to the
issue checkout read-only. Background polling/automation is disabled. Use the
existing cached appliance image; create fresh databases through migrations and
seed. Install msmtp and real sudo inside that container, replacing its sudo shim,
then install the unchanged installer SMTP helper and its exact-command sudo rule.
Trust a disposable local SMTP sink certificate in that container only. No scans
or external network devices are needed.

The sink listens on container loopback port 2525, requires STARTTLS and SMTP AUTH,
and stores message/TLS/authentication counts only. It must not retain message
bodies, recipient lists or credentials. Synthetic fixture credentials are distinct
from any real provider credentials. Keep raw setup and evidence outside Git.

| Case | Action | Expected result |
|---|---|---|
| SMTP-L01 | Save Other SMTP relay through the authenticated API as the unprivileged service user | Existing root helper applies exactly its original six fields; configuration is root:nagios 0640 |
| SMTP-L02 | Send a test email, save again with blank password, send again | Both arrive at the sink with verified STARTTLS and authentication; credential is not returned |
| SMTP-L03 | Save invalid host, port and TLS values | Field-specific 400 responses; current working configuration remains usable |
| SMTP-L04 | Add scoped host/service fixtures using the production formatted-email script; validate with Nagios before reload | Nagios accepts fixtures; checks target only local always-OK commands |
| SMTP-L05 | Force one custom host and one custom service notification through the external command pipe | Both messages reach the sink through real msmtp; failure indicator remains null |
| SMTP-L06 | Empty only the disposable transport configuration, force a notification, poll settings | New failure time and safe reason appear within one 30-second UI cycle; service user can read the real worker log |
| SMTP-L07 | Run the opt-in browser test against the seeded synthetic fixture | Provider switch/help, field validation, real save/test, blank-password preservation, failure notice/link and polling after log rotation work; unsaved edits survive |
| SMTP-L08 | Run `scripts/verify.sh all` | Isolated regression, docs, build and lint pass |

For SMTP-L07, serve the built client through the fixture's Nginx alongside `/api`.
Use the seeded development administrator, the local synthetic relay configuration
and the existing failure notice from SMTP-L06. The browser test checks the label,
URL and saved local-relay configuration before writing. It rotates only this
owned container's log. Trace/video/screenshots remain disabled.

```bash
PINPOINT_SMTP_LAB_URL=http://127.0.0.1:18115 \
  npx --prefix client playwright test --config client/playwright.config.ts \
  --project issue-115-live --reporter=line
```

A real-provider inbox trial is separate and needs the owner's explicit recipient
and configured sending credentials. Enter real credentials through Settings →
Email; never put them in chat, source, command arguments, reports or raw captures.
Disable stock fixture notifications before configuring a real provider, keep
background jobs off, and send only the requested labeled messages. Authentication
success, server acceptance and owner-confirmed inbox arrival are separate results.
A provider quota rejection is not delivery proof. Restore the synthetic fixture
before rerunning SMTP-L07, then remove the owned container after testing is done.
Implicit TLS, plaintext SMTP, OAuth and installer upgrade trials are outside the
requester's STARTTLS-only scope. Record results using the
[test-run template](../../../docs/test-runs/TEMPLATE.md); retain failed/blocked
attempts and report a retest separately.
