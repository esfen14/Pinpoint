# Test run: issue-274 observed manifest, reset and product inventory

| | |
|---|---|
| Date | 2026-10-28, Asia/Manila |
| Environment | Pinpoint-Final appliance, Windows VM and fourteen host-Docker targets on `vboxnet1` |
| Scope | `presenter manifest`, `presenter reset`, and a read-only read of Pinpoint's Device Inventory |

## Result

**Pass.** Plugins for the demo ports are enabled and monitoring; PostgreSQL has no dedicated plugin in the appliance.

- `demo/demo presenter manifest` read all fourteen Linux targets and reported MAC, IP, live listeners and the catalog's expected plugin for each. It exited 0 (consistent). The Windows VM is recorded from its pinned MAC and Pinpoint only; the presenter cannot observe its address or listener.
- Pinpoint's Device Inventory listed 16 hosts, all UP and Monitored: the 15 catalog addresses and the appliance's own `localhost`.
- `presenter reset` was run from a perturbed lab (a DHCP client moved to `.25`, another set to static `.15`, `api02` stopped, an extra `web03` port open, `ftp01` FTP stopped). It returned every target to its catalog address with all daemons running and no extra ports in 84 seconds, and a second run completed with the same result.

## Devices

Companion listeners are extra sockets that the real daemons open (DNS over TCP, SNMP SMUX, the DHCP client on UDP 68); they are recorded, not treated as faults. The Pinpoint columns are read from the Pinpoint UI after the plugins were enabled; the expected-plugin column is the catalog's expectation.

| Device | IP | MAC | Observed | Expected listeners (plugin) | Companion | Pinpoint host | Monitored in Pinpoint | Other ports in Pinpoint |
|---|---|---|---|---|---|---|---|---|
| dhcp01 | `10.77.1.2` | `02:77:01:00:00:01` | yes | tcp/22 ssh (check_ssh), udp/67 dhcp (no plugin) | - | dev-6de884 | tcp/22 ssh via check_ssh | - |
| win01 | `10.77.1.3` | `02:77:01:00:00:02` | Pinpoint only | tcp/5693 ncpa (check_ncpa.py) | - | dev-581e83 | tcp/5693 ncpa via check_ncpa | - |
| web03 | `10.77.1.4` | `02:77:01:00:00:03` | yes | tcp/80 http (check_http), tcp/443 https (check_http) | - | dev-9d2afd | tcp/80 http via check_http, tcp/443 https via check_http | tcp/8088 http (Missing), tcp/8443 https (Missing) |
| api02 | `10.77.1.5` | `02:77:01:00:00:04` | yes | tcp/8081 http (check_http) | - | dev-ae70fd | tcp/8081 http via check_http | - |
| ftp01 | `10.77.1.6` | `02:77:01:00:00:05` | yes | tcp/21 ftp (check_ftp) | - | dev-2e463a | tcp/21 ftp via check_ftp | - |
| mail01 | `10.77.1.7` | `02:77:01:00:00:06` | yes | tcp/25 smtp (check_smtp), tcp/143 imap (check_tcp) | - | dev-df02af | tcp/25 smtp via check_smtp, tcp/143 imap via check_tcp | - |
| dns01 | `10.77.1.8` | `02:77:01:00:00:07` | yes | udp/53 dns (check_dns) | tcp/53 | dev-3d579e | tcp/53 domain via check_dns, udp/53 domain via check_dns | - |
| db01 | `10.77.1.9` | `02:77:01:00:00:08` | yes | tcp/5432 pgsql (check_pgsql) | - | dev-835a8a | tcp/5432 nagios-nsca via check_tcp | - |
| snmp02 | `10.77.1.10` | `02:77:01:00:00:09` | yes | udp/161 snmp (check_snmp) | tcp/199 | dev-ec6b5e | tcp/199 smux via check_tcp, udp/161 snmp via check_snmp | - |
| ssh-alt02 | `10.77.1.11` | `02:77:01:00:00:0a` | yes | tcp/2223 ssh (check_ssh) | - | dev-8c66c0 | tcp/2223 ssh via check_ssh | - |
| dynweb01 | `10.77.1.20` | `02:77:01:00:00:0b` | yes | tcp/22 ssh (check_ssh), tcp/80 http (check_http) | udp/68 | dev-8fbfd1 | tcp/22 ssh via check_ssh, tcp/80 http via check_http | - |
| dynapp01 | `10.77.1.21` | `02:77:01:00:00:0c` | yes | tcp/22 ssh (check_ssh), tcp/8080 http (check_http) | udp/68 | dev-9bfaff | tcp/22 ssh via check_ssh, tcp/8080 http via check_http | - |
| dynmail01 | `10.77.1.22` | `02:77:01:00:00:0d` | yes | tcp/22 ssh (check_ssh), tcp/25 smtp (check_smtp) | udp/68 | dev-cb8670 | tcp/22 ssh via check_ssh, tcp/25 smtp via check_smtp | - |
| dynsnmp01 | `10.77.1.23` | `02:77:01:00:00:0e` | yes | tcp/22 ssh (check_ssh), udp/161 snmp (check_snmp) | tcp/199, udp/68 | dev-07a2ac | tcp/22 ssh via check_ssh, tcp/199 smux via check_tcp, udp/161 snmp via check_snmp | - |
| dynweb02 | `10.77.1.24` | `02:77:01:00:00:0f` | yes | tcp/22 ssh (check_ssh), tcp/9090 http (check_http) | udp/68 | dev-0d91f7 | tcp/22 ssh via check_ssh, tcp/9090 http via check_http | - |

## Plugins

Initially only `check_ssh`, `check_http` and `check_ncpa` were enabled, so the FTP, DNS, SMTP, IMAP, PostgreSQL and SNMP ports were discovered-only (Suggested). At the owner's request `check_dns`, `check_ftp`, `check_smtp`, `check_snmp` and `check_tcp` were enabled through Plugin Manager's own preview and confirm (previews: DNS 2 services, FTP 1, SMTP 2, SNMP 12, TCP 4). About two minutes later every discovered demo port above was Monitored.

- `check_pgsql` does not exist among the appliance's 65 baseline plugins, so the catalog's expected plugin for PostgreSQL cannot be met. Pinpoint guesses `5432` as `nagios-nsca` from the port number and monitors it with `check_tcp`. This is a gap between the catalog's expectation and the appliance, not a lab fault.
- The SNMP devices also have `tcp/199` (SMUX), now monitored by `check_tcp`.
- `web03` still lists `8088` and `8443` as Missing from the earlier port test; they stay until archived.
- After the reset, `dynweb01` (`dev-8fbfd1`) returned to `.20` about 6.5 minutes after a discovery was started.

## Not covered

No Windows-side listener probe. The plugin enables changed Pinpoint's configuration (five plugins) and added monitored services; nothing else was changed. Raw captures, credentials and the scrape scripts are not committed.
