## 3. Hardware requirements

### 3.1 Servers and workstations

| Item | Minimum | Recommended | Basis |
|---|---|---|---|
| PinPoint server CPU | 2 cores **[A]** | 4 cores | VM lab uses 4 vCPUs (`scripts/vmlab`) |
| Memory | 4 GB | 4 GB or more **[A]** | VM lab uses 4096 MB; Docker lab needs about 4 GB free |
| Disk | 40 GB | 40 GB plus room for history and 7 backups **[A]** | VM lab disk 40960 MB |
| Network interface | 1 × Ethernet on the monitored LAN | Wired, static address **[R]** | |
| Administrator workstation | Any computer with a current browser | | |

**Tested limit.** Resource use has been measured with at most **14 monitored
hosts** (containers in a lab), on virtual machines with 4 CPUs and about 4 GB of
memory. A later timing run saw 15 monitored devices; no recorded run had more.
Sizing for a larger network is not known. The 2-core minimum has not been tested.
When monitoring more hosts, watch CPU, memory and free disk space. The measured
figures and their limits are in [section 10.4](10_Testing_and_validation.md#104-performance-testing).

### 3.2 Routers and switches

PinPoint needs no specific router or switch. To use bandwidth charts the
devices must answer SNMP v1/v2c (interface discovery uses `snmpwalk -v2c`;
v3 is supported for checks but not for interface discovery).

### 3.3 Wireless access points

Not required. APs that answer ICMP or SNMP can be monitored like any host.

### 3.4 Storage

`system.db`, `history.db`, `DATABASE_BACKUP_DIR` (default
`server/database-backups`, newest 7 kept) and the Nagios archive directory
live on the server. The Dashboard warns below 10% free disk. **[R]** Copy
backups off the server (section 11.6).

### 3.5 Peripherals

None. A UPS for the server is **[R]**.
