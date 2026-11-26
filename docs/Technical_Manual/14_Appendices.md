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
| Operator guides | [`docs/User_Manual/guides/`](../User_Manual/guides/README.md) |
| Maintainer guides | [`docs/Technical_Manual/guides/`](guides) |

### Appendix B. Items to be confirmed (questions for the owners)

Struck-through items are answered.

| # | Item | Section | Answer or open question |
|---|---|---|---|
| 1 | ~~Installer order and upgrades~~ | 8 | Answered from the installer README and scripts (2026-11-19), and the first-boot order was observed on an ISO install (2026-11-25). Confirmation by the installer maintainer (Lorraine) is pending |
| 2 | ~~HTTPS~~ | 5.5, 9.4 | Answered: the installer configures no TLS; Nginx listens on 80 only. Decision for the site: add TLS |
| 3 | ~~Host firewall~~ | 5.7 | Answered: not configured; the health check only tests `ufw` if active |
| 4 | ~~Server addressing, DNS, gateway~~ | 5.2, 5.6 | Answered: chosen in the Ubuntu installer's network step |
| 5 | ~~Production Nginx config~~ | 2.1 | Answered: `/etc/nginx/sites-available/pinpoint`, written by `deploy-pinpoint-web.sh` |
| 6 | ~~Sizing~~ | 3.1, 10.4 | Answered by stating the tested limit: resource use measured with at most 14 container hosts on 4 CPUs and about 4 GB. Larger sizing is not known; the rows-per-host measurement is deferred (#82) |
| 7 | ~~Supported monitored OSes~~ | 4.1 | Answered from source: NCPA deployment accepts Debian or Ubuntu based hosts only. Lab targets ran Ubuntu 22.04 and 24.04 |
| 8 | ~~Bootstrap credentials location~~ | 8.4 | Answered: `/root/pinpoint-install-credentials.txt`, removed after first confirmation |
| 9 | ~~NCPA key and token location~~ | 8.4 | Answered: `/opt/pinpoint/.ssh/pinpoint_ncpa_deploy`; token in `system.db` |
| 10 | ~~Backup time of day~~ | 6.6 | Answered from source: there is no time-of-day setting. A backup runs at the first automation check (every 5 minutes) after the newest backup is a day old. A fixed time would be a new feature |

### Appendix C. Still to be confirmed

- Confirmation of the installer facts by its maintainer, Lorraine.
- Review of the installer repository by the CICT IT team.
- A performance test at a production host count.
