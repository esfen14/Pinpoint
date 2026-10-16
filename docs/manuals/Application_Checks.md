# Application checks: web, mail and what stays port-level

PinPoint checks every monitored port with the plugin that fits its service. For most services that plugin talks to the service, not only to the port. This page says which web and mail checks you can adjust per device, and which services are checked only for "the port accepts a connection".

## Web and API checks (HTTP and HTTPS)

Open **Device Inventory**, choose a device, and in the **Ports** section choose **Check options** on a monitored HTTP or HTTPS port.

| Field | What it does |
|---|---|
| **Expected text** | The response must contain this text; otherwise the check is CRITICAL. |
| **Expected status codes** | HTTP status codes that count as healthy, separated by commas (`200` or `200,301`). Any other status is CRITICAL. |
| **Virtual host** | The host name sent to the web server, for a device that serves several sites. The check still connects to the device's address. |
| **Request method** | GET, HEAD, POST, PUT, DELETE, OPTIONS or PATCH. **Default** sends the standard request. |

Leave a field empty to keep the default check. The options belong to the device and the service: they apply to every HTTP (or every HTTPS) service monitored on that device. **Save** applies the Nagios configuration; **Reset to defaults** removes your options and returns the device to the standard check.

Rules the form enforces (the server enforces them too and names the field it refused):

- No quotes, backticks, `!`, `$`, `;` or backslashes, and no line breaks, in any field.
- Status codes are three-digit codes from 100 to 599, up to ten, separated by commas.
- A virtual host is a host name: letters, digits, `.` and `-`.

Not offered: authentication headers and passwords for web checks.

## Mail checks (POP3 and IMAP)

PinPoint checks the greeting the mail server sends when a client connects.

| Service | Default port | Greeting expected |
|---|---|---|
| POP3 (`pop3`) | 110 | `+OK` |
| POP3 over TLS (`pop3s`) | 995 | `+OK` |
| IMAP (`imap`) | 143 | `* OK` |
| IMAP over TLS (`imaps`) | 993 | `* OK` |

A server that answers with anything else is CRITICAL. If your server greets differently, open **Check options** on its port and set **Expected greeting**. Discovery names the services from nmap's result; a port that was already monitored as a plain TCP port before this check existed keeps that check until you use **Set service** on it and choose `pop3`, `imap`, `pop3s` or `imaps`.

The default Port to Service table in **Settings** now lists ports 110, 143, 993 and 995. A table you saved earlier is not changed; add the ports there if you want discovery to propose them for servers nmap cannot identify.

## Without permission to edit

Users with **system.hosts** but not **system.hosts.edit** can open **Check options** and read the saved options; the fields are disabled and there is no Save or Reset.

## Checked at port level only

PinPoint uses only the plugins that ship with it. A service without one is checked by the generic TCP check, which proves the port answers and nothing more:

- Database engines: **Microsoft SQL Server**, **Oracle** and **MongoDB** (MySQL and PostgreSQL have their own checks).
- Application servers: **JBoss**, **WebLogic** and **Citrix**.
- Any other service nmap names that PinPoint has no plugin for.

These services still appear in Device Inventory and still raise an alert when the port stops answering. They do not tell you that the service itself is healthy. Custom and community plugins are not supported.
