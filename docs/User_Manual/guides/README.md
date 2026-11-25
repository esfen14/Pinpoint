# Pinpoint guides

How-to guides for operators and users. Each guide gives the purpose, prerequisites, numbered steps, the expected result and precautions. A guide marked **TBC** inside has items not yet checked step by step on a demo build.

The [User Manual](../User_Manual.md) and [Technical Manual](../../Technical_Manual/Technical_Manual.md) (drafts, issue #181) link to these guides rather than copy them.

## Guide for each page

Every route in the web interface (`client/src/App.tsx`) is listed here.

| Page (route) | Guide | Notes |
|---|---|---|
| Sign in (`/login`) | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) | |
| Dashboard (`/dashboard`) | [Dashboard and Network Health](Dashboard_and_Network_Health.md) | |
| Network Health (`/network-health`) | [Dashboard and Network Health](Dashboard_and_Network_Health.md) | |
| Network Status (`/system-status`) | [Dashboard and Network Health](Dashboard_and_Network_Health.md) | |
| Device Inventory (`/device-inventory`) | [Device Inventory](Device_Inventory.md) | Merging duplicates: [Device identity review](Device_Identity_Review.md) |
| History (`/history`) | [Alerts and notification history](Alerts_and_Notification_History.md) | |
| Topology (`/topology`) | [Network topology](Topology.md) | |
| Plugin Manager (`/plugins`) | [Plugin Manager](Plugin_Manager.md) | Your own checks: [Custom checks](Custom_Checks_Manual.md), [Application checks](Application_Checks.md) |
| NCPA Deployment (`/ncpa-deployment`) | [NCPA deployment](NCPA_Deployment.md) | |
| Maintenance (`/maintenance`) | [Maintenance windows](Maintenance_Windows.md) | |
| Remediation (`/remediation`) | [Automatic recovery](Automatic_Recovery.md), [Remote service restart](Remote_Service_Restart.md) | |
| Reports (`/reports`) | [Service reports](Service_Reports.md) | |
| System Logs (`/system-logs`) | [System logs](System_Logs.md) | Nagios log: [Storage and Nagios logs](Storage_and_Nagios_Logs.md) |
| Manage Accounts (`/accounts`) | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) | |
| Manage Roles (`/manage-roles`) | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) | |
| Settings (`/settings`) | [Settings](Settings.md) | Tabs: [Network discovery](Network_Discovery.md), [Email settings](Email_Settings.md), [Notification policy](Notification_Policy.md) |

## Tasks

| Task | Guide |
|---|---|
| Find and inspect a host | [Device Inventory](Device_Inventory.md) |
| Resolve a duplicate device identity | [Device identity review](Device_Identity_Review.md) |
| Acknowledge an alert | [Dashboard and Network Health](Dashboard_and_Network_Health.md) |
| Scan the network | [Network discovery](Network_Discovery.md) |
| Reset a forgotten password | [Sign in, accounts and roles](Login_Accounts_and_Roles.md) |
| Back up and restore | [Backup and restore](../../Technical_Manual/guides/Backup_and_Restore.md) |
| Build a local test lab | [Local lab](../../Technical_Manual/guides/Local_Lab.md) |

## Manuals and hand-off documents

| Document | Purpose |
|---|---|
| [User Manual](../User_Manual.md) | For people who use the web interface |
| [Technical Manual](../../Technical_Manual/Technical_Manual.md) | For administrators and maintainers: architecture, installation, operations |
| [Hand-off page](../../Hand_Off.md) | License, installer location, credential locations, contacts, open questions |
| [Database diagram (ERD)](../../reference/ERD.md) | Generated from the models; always current |
| [Architecture and example deployment diagrams](../../reference/Architecture_Diagrams.md) | Software architecture and a generic deployment |

## Printable copies (DOCX and PDF)

```bash
scripts/export_manuals.sh            # both manuals; or: user | technical
```

Writes `build/manuals/User_Manual.docx` and `.pdf`, and the same for the Technical Manual (`build/` is git-ignored). Needs `pandoc`, LibreOffice (`soffice`), `node`/`npx` and `python3`; mermaid-cli is fetched on first use and reuses a Playwright Chromium if one is installed (set `MERMAID_CHROME` to choose another).

What the export does to the Markdown (see `scripts/manual_export/`):

- Joins the Technical Manual's chapter files, in the order of its contents list, into one document.
- Replaces the manual's own contents list with a generated one that has page numbers, and puts the title block on a title page.
- Renders each Mermaid diagram to an image. Left-to-right diagrams are stacked top to bottom so they stay readable on a portrait page.
- Turns links to other repository files into a printed note, for example "Device Inventory (repository file `docs/User_Manual/guides/Device_Inventory.md`)"; web links and links inside the same manual stay.
- Uses the Word styles in `scripts/manual_export/reference.docx` (A4, 2 cm margins, Arial, page numbers, bordered tables, a new page for each chapter). Edit that file in Word to change the look; delete it and run the script to regenerate the default from `scripts/manual_export/make_reference.py`.
- The linked guides in the `guides/` folders are not copied into the printed manuals; they stay in the repository. Wide tables are shrunk to a smaller font, not rotated to landscape.

In Word, open the DOCX and choose **Update field** on the contents list the first time; the PDF already has it filled in.
