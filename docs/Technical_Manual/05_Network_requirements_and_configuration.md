## 5. Network requirements and configuration

> Sections 5.2 to 5.7 depend on the site. Values below are what the
> application needs; site-specific addressing and firewall configuration are
> **TBC** (the installer was checked on 2026-11-19; see the notes in each subsection).

### 5.1 Topology

PinPoint sits on, or routes to, every monitored subnet. Discovery uses nmap
directly, so the server must reach target addresses without NAT in between
**[A]**.

### 5.2 IP addressing and subnetting

| Item | Value |
|---|---|
| Monitored subnets | `PINPOINT_NETWORKS` (default `192.168.130.0/24`) or Settings → Network Discovery; a range larger than /16 is refused; localhost is never scanned |
| PinPoint server address | Chosen by the administrator in the Ubuntu installer's network step (DHCP or static); the installer does not set it afterwards. **[R]** Use a static address or a DHCP reservation |
| Monitored devices | DHCP or static; PinPoint tracks address changes through device identity evidence (NCPA certificate, SSH host key, MAC, machine ID, DNS name) |

### 5.3 Router and switch configuration

- Allow the PinPoint server's ICMP and TCP probes to every monitored subnet.
- Enable SNMP (read-only community, or v3 user) for devices whose interfaces
  you want charted, restricted to the PinPoint address **[R]**.

### 5.4 VLANs

Not required. With VLANs, route or trunk the PinPoint server to each VLAN.
The site's addressing, VLANs and firewall placement are not yet known. Do not
add them to this repository, which is public; keep them in a private site
document.

### 5.5 Protocols and ports

| Direction | Protocol/port | Purpose | Basis |
|---|---|---|---|
| Users → PinPoint | TCP 80 (HTTP) | Web UI and `/api` via Nginx | Lab Nginx, installer contract |
| Users → PinPoint | TCP 443 (HTTPS) | Not configured by the installer (Nginx listens on 80 only) | |
| Loopback | TCP 8000 | Nginx → Gunicorn **[A]** | Lab Nginx |
| Loopback | TCP 8081 | Nagios web / JSON CGIs | Installer contract |
| PinPoint → devices | ICMP echo | `check-host-alive` and discovery | |
| PinPoint → devices | TCP/UDP, configured ports | nmap discovery and service checks | `config.py`, Settings |
| PinPoint → devices | UDP 161 | SNMP checks and interface discovery | |
| PinPoint → devices | TCP 22 | NCPA deployment, remote restart, SSH checks | `SSH_PORT` |
| PinPoint → devices | TCP 5693 (default) | NCPA agent API | `NCPA_PORT`; per-device port recorded |
| PinPoint → SMTP relay | TCP 587 STARTTLS | Alert and test email | Settings → Email |
| Administrator → PinPoint | TCP 22 | Server administration **[A]** | |

### 5.6 DNS, DHCP and gateway

PinPoint needs a default gateway to reach routed subnets and the SMTP relay,
and DNS to resolve the SMTP host. Device DNS names are optional identity
evidence. The installer does not configure them; the administrator sets them in the
Ubuntu installer's network step.

### 5.7 Firewall rules and network security

**[R]** Host firewall on the appliance (for example `ufw`):

| Rule | Reason |
|---|---|
| Allow inbound 80/443 from administrator subnets only | Limit UI exposure |
| Allow inbound 22 from administrator workstations only | Server administration |
| Deny all other inbound | 8000 and 8081 are loopback only |
| Allow outbound to monitored subnets and the SMTP relay | Monitoring and email |

On monitored hosts allow 5693/tcp (NCPA) and 22/tcp (deployment) only from the
PinPoint address. The installer does not configure a host firewall; its health check
only verifies that, if `ufw` is active, it allows port 80.

### 5.8 Bandwidth and connectivity

Monitoring traffic is small (periodic checks every 1–15 minutes); discovery
scans are bursty. Measured on the QA lab appliance (4 CPU, 3.9 GB, 2026-11-25),
one discovery scan of a `/27` with 14 container hosts moved about 8.5 MB in and
8.6 MB out on the monitored interface over 226 s, roughly 0.6 Mbit/s on average.

### 5.9 Remote access

There is no remote-access feature. **[R]** Reach the UI over a VPN rather
than exposing it to the internet.

### 5.10 Network monitoring and troubleshooting

| Symptom | Check |
|---|---|
| Scan finds nothing | `PINPOINT_NETWORKS` / saved networks; routing from the appliance; `nmap` runs |
| SNMP charts empty | Community/v3 credentials; UDP 161 reachable; interface selected in Device Inventory |
| NCPA metrics critical | 5693 reachable; agent running; `check_ncpa` enabled; token/certificate |
| No email | Settings → Email failure indicator; `/etc/msmtprc` via helper; outbound 587 |
