# Hand-off

For the IT team taking over Pinpoint. This page says where things are and what is
still undecided. It holds **locations only, never secret values**, and no real
network details (subnets, hostnames, firewall rules).

## Where to find things

| You want | Go to |
|---|---|
| The license | [`LICENSE`](../LICENSE) (GPL-3.0, **provisional**; see [License](#license)) |
| What Pinpoint is and how to run it | [Root `README.md`](../README.md) |
| How to use it (operators and users) | [User Manual](User_Manual/User_Manual.md) |
| How to install, run and maintain it | [Technical Manual](Technical_Manual/Technical_Manual.md) |
| Task guides for every page | [Manuals index](manuals/README.md) |
| Database diagram (generated, always current) | [`reference/ERD.md`](reference/ERD.md) |
| Software architecture and an example deployment | [`reference/Architecture_Diagrams.md`](reference/Architecture_Diagrams.md) |
| What the system must do | [`spec files/`](../spec%20files/README.md) |
| What is unfinished or excluded | [`Implementation_Status.md`](../spec%20files/Implementation_Status.md) |
| How to contribute a change | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |

## Repositories

| Repository | Holds | Notes |
|---|---|---|
| This repository (`esfen14/Pinpoint`) | The Flask backend, React frontend, specifications, manuals and tests | |
| [`lorraine-pangilinan/PinPoint-Installer`](https://github.com/lorraine-pangilinan/PinPoint-Installer) | The installer that sets up an Ubuntu Server appliance: Nagios Core, plugins, Nginx, Gunicorn, msmtp, sudoers rules, helper scripts and the service files | Not reviewed for the manuals; installer-owned behaviour is marked **TBC** in the Technical Manual |

## Contacts

GitHub handles only. Ask through a GitHub issue in the relevant repository.

| Role | GitHub handle |
|---|---|
| Installer maintainer | [`lorraine-pangilinan`](https://github.com/lorraine-pangilinan) |
| Plugin Manager author | [`lorraine-pangilinan`](https://github.com/lorraine-pangilinan) |
| Maintainers (this repository) | [`esfen14`](https://github.com/esfen14), [`eliarzx`](https://github.com/eliarzx), [`RinkoCheesekek`](https://github.com/RinkoCheesekek), [`jaaasantiago`](https://github.com/jaaasantiago), [`lorraine-pangilinan`](https://github.com/lorraine-pangilinan) |
| University IT contact after hand-off | **TBC:** to be named by the university |

## Where credentials and secrets live

Locations only. No value is written in this repository.

| Credential | Where it is stored |
|---|---|
| `SECRET_KEY`, `PINPOINT_SECRETS_KEY`, Nagios web user and password | `/etc/pinpoint/pinpoint.env` on the appliance (production); Git-ignored `server/.env` (development) |
| Bootstrap administrator placeholder email and password | Created by the installer. **TBC:** where the installer reports them |
| SMTP password | Encrypted in the `SMTP_SETTINGS` table, and in `/etc/msmtprc` (written by a root helper) |
| Custom-check passwords, SNMPv3 passphrases | Encrypted in `system.db`; written to the Nagios resource file when configuration is generated |
| NCPA deployment SSH key and NCPA token | **TBC:** on-disk location |
| Settings table and environment variables | [Root `README.md`, "Production settings"](../README.md#production-settings) |

Keep `SECRET_KEY` (or `PINPOINT_SECRETS_KEY`) stable across upgrades: if it
changes, stored passwords can no longer be read and must be entered again.

## License

[`LICENSE`](../LICENSE) is the GNU General Public License v3.0. It is
**provisional**:

- The backend imports `python3-nmap` (`nmap3`), which is GPL-3.0. Software that
  combines with it and is distributed must be offered under GPL-compatible
  terms. Nagios Core, Nagios Plugins and Nmap are run as separate programs and
  do not force a license on Pinpoint's code.
- Who owns the code, and so who may choose the final license, is not yet
  settled. The capstone adviser and the university's research office or
  Innovation and Technology Support Office (ITSO) are to answer it, with
  reference to the university's intellectual property policy.

## To Be Confirmed

Open questions for the university IT team and the project owners. Nothing here
is assumed.

| # | Question | Owner |
|---|---|---|
| 1 | Who owns the code (students, university, or both), and which license may be used. The `LICENSE` stays provisional until this is answered | Capstone adviser, university research office or ITSO |
| 2 | If GPL-3.0 is not acceptable: replace the two `nmap3` imports (`network_discovery.py`, `ncpa_relocation.py`) with direct `nmap` calls and XML parsing, then choose another license | Project owners, after item 1 |
| 3 | Licensing of what the installer bundles or downloads (Nagios Core GPL-2.0, Nagios Plugins GPL-3.0, Nmap under its own license, NCPA). Redistribution terms were not reviewed | Installer maintainer |
| 4 | A license scan of the frontend and remaining Python dependencies; only `python3-nmap` and the Nagios components were reviewed | Project owners |
| 5 | HTTPS, host firewall, static address, DNS and gateway: what the installer configures | Installer maintainer |
| 6 | Where the installer reports the bootstrap login, and where the NCPA key and token are stored | Installer maintainer |
| 7 | The final maintainer list and a named university IT contact | Project owners, university IT |

The Technical Manual's [Appendix B](Technical_Manual/Technical_Manual.md) lists
the remaining technical questions.
