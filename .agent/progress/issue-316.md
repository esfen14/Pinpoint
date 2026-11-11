# Issue #316: Audit lab/appliance against the current installer

Branch: `issue-316-appliance-installer-drift`
Status: in-progress

## Finish condition

- [ ] Every difference between `lab/appliance/Dockerfile` (and its entrypoint, supervisord, nginx, shims) and the current PinPoint-Installer `setup/` scripts is listed (versions, packages, config, paths).
- [ ] Real drift is fixed; deliberate lab-only differences are recorded in the Dockerfile or `docs/manuals/Local_Lab.md`.
- [ ] The DHCP lab (`lab/dhcp/control.py`, #187) still builds from `lab/appliance/Dockerfile`.

Requirement coverage:

| Issue requirement | Finish-condition item | Proof |
|---|---|---|
| Compare and list every difference | 1 | Drift table in Local_Lab.md; installer ref 9bc7150 (main, 2026-11-10) |
| Fix real drift | 2 | `server/tests/unit/test_lab_appliance_drift.py`; image build |
| Record deliberate differences | 2 | Local_Lab.md "Deliberate lab differences" + Dockerfile comments |
| DHCP lab still builds | 3 | `docker build -f lab/appliance/Dockerfile .` and `lab/dhcp/appliance.Dockerfile` |

## Drift found (installer ref 9bc7150)

Real drift, to fix:
1. Nagios/plugins source from GitHub, no SHA-256; installer uses assets.nagios.com / nagios-plugins.org URLs with pinned SHA-256.
2. Plugins built without `--with-mysql=/usr` (no check_mysql; needs libmariadb-dev); check_ncpa.py 1.2.4 not installed (python3 shebang fix too); no python3 in image.
3. `cgi.cfg` sed grants pinpoint-api every `authorized_for_*` line incl. command rights; installer grants only system_information, configuration_information, all_hosts, all_services.
4. htpasswd.users is root:root 644; installer root:www-data 640.
5. plugin-services.cfg missing (installer: pinpoint:nagios 664, cfg_file in nagios.cfg).
6. Event handler spool `/usr/local/nagios/var/spool/pinpoint-events` (nagios:pinpoint 2770) and root-owned `/usr/local/sbin/pinpoint-event-handler` missing.
7. No msmtp-mta/bsd-mailx (`/bin/mail`) and no `/etc/msmtprc` (root:nagios 640).
8. nmap: installer root:pinpoint 0750 + caps `cap_net_raw,cap_net_admin,cap_net_bind_service=eip`; lab no 0750, no net_bind_service. pinpoint user not in group `pinpoint`-only system user (lab uses -m and shell).
9. Gunicorn lacks `--timeout 300 --no-control-socket --error-logfile -`.
10. Nginx lacks `client_max_body_size 50M`, 300s proxy timeouts, X-Real-IP / X-Forwarded-Proto.
11. uv Python dir `/opt/uv-python` vs installer `/opt/pinpoint/python`; no `uv pip check`.

Deliberate lab-only (to record): no systemd (supervisord), `install-daemoninit` skipped, sudo/systemctl/nmap-sudo shims (NMAP_PRIVILEGED=1 vs `--privileged`), interval_length=10 and no first-check stagger, lab credentials and nagiosadmin account, no PHP/mariadb-server, no client build (UI via `scripts/lab ui`), no installer firstboot/autoinstall/journald/logrotate/update/resource-helper/ncpa-deploy/service-restart/apply-smtp helpers and sudoers rules, hosts.cfg cfg_file appended not placed under localhost.cfg, runtime rsync of the app tree, apache extra a2enmod are default-on.

## Plan

1. [ ] Test first: `server/tests/unit/test_lab_appliance_drift.py` asserting the fixes above on lab files.
2. [ ] Dockerfile: items 1-8, 11 (`lab/appliance/Dockerfile`)
3. [ ] entrypoint (handler install), supervisord (gunicorn flags), nginx conf (items 6, 9, 10)
4. [ ] `docs/manuals/Local_Lab.md`: drift/deliberate-differences table, installer ref
5. [ ] Build image and DHCP lab base build; `scripts/verify.sh docs` then `all`
6. [ ] Finish (section 5): delete progress file, PR

## Round log

| Round | Change made | Check run | Result |
|---|---|---|---|
| 0 | audit, plan | - | - |

## State for the next session

- Last check run (exact command): none
- Result: n/a
- Hypothesis: n/a
- Next action: write the failing drift test (plan step 1)

## Decisions and notes

- Installer checkout used: `/home/paeng/Documents/Capstone-FIles/Capstone-Project/PinPoint-Installer` at main 9bc7150 (the other checkout is 18 commits behind).
