## 14. Appendices

### Appendix A. Reference documents

| Topic | Document |
|---|---|
| Specification index | [`spec files/README.md`](../../spec%20files/README.md) |
| Architecture | [`System_Overview_and_Architecture.md`](../../spec%20files/System_Overview_and_Architecture.md) |
| Routes | [`Backend_Modules_and_Routes.md`](../../spec%20files/Backend_Modules_and_Routes.md), [`Frontend_Modules_and_Routes.md`](../../spec%20files/Frontend_Modules_and_Routes.md) |
| Data and integrations | [`Data_Model_and_Integrations.md`](../../spec%20files/Data_Model_and_Integrations.md) |
| Standards | [`Engineering_Standards.md`](../../spec%20files/Engineering_Standards.md) |
| Status and gaps | [`Implementation_Status.md`](../../spec%20files/Implementation_Status.md) |
| Plugins | [`Plugins_List.md`](../../spec%20files/Plugins_List.md) |
| Operator guides | [`docs/manuals/`](../User_Manual/guides/README.md) |

### Appendix B. Items to be confirmed (questions for the owners)

| # | Item | Section | Question |
|---|---|---|---|
| 1 | ~~Installer order and upgrades~~ | 8 | Answered from the installer README and scripts (2026-11-19); the maintainer should confirm |
| 2 | ~~HTTPS~~ | 5.5, 9.4 | Answered: the installer configures no TLS; Nginx listens on 80 only. Decision for the site: add TLS |
| 3 | ~~Host firewall~~ | 5.7 | Answered: not configured; the health check only tests `ufw` if active |
| 4 | ~~Server addressing, DNS, gateway~~ | 5.2, 5.6 | Answered: chosen in the Ubuntu installer's network step |
| 5 | ~~Production Nginx config~~ | 2.1 | Answered: `/etc/nginx/sites-available/pinpoint`, written by `deploy-pinpoint-web.sh` |
| 6 | Sizing | 3.1 | Expected host count; measured CPU, memory, disk and bandwidth on a named appliance |
| 7 | Supported monitored OSes | 4.1 | Which Linux distributions does NCPA deployment support? |
| 8 | ~~Bootstrap credentials location~~ | 8.4 | Answered: `/root/pinpoint-install-credentials.txt`, removed after first confirmation |
| 9 | ~~NCPA key and token location~~ | 8.4 | Answered: `/opt/pinpoint/.ssh/pinpoint_ncpa_deploy`; token in `system.db` |
| 10 | Backup time of day | 6.6 | Backups run once a day when due; is a fixed time wanted? |

### Appendix C. Not covered by this draft

- DOCX and PDF export for the capstone appendix (issue #181 section G).
- Confirmation of the installer answers by its maintainer (they were read from the repository, not run on a production appliance).
- Measurements from a named lab appliance.
