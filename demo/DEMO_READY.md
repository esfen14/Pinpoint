# Installed demo lab

Pinpoint is served at **http://127.0.0.1:18080** by the VirtualBox VM
`pinpoint-qa-appliance`. The five target VMs use the isolated internal network
`pinpoint-demo`, `10.77.0.0/28`; the appliance is `10.77.0.1`.

The administrator email and password are stored privately in
`~/.local/share/pinpoint-vmlab/admin-email` and `admin-password`. Read these
locally to sign in; do not include them in slides or recordings. The targets use
the public disposable demo login documented in [README.md](README.md).

## Start the presentation

From the repository root:

```bash
scripts/vmlab up
python3 demo/demo_lab.py up --gui
python3 demo/demo_lab.py wall
```

Open http://127.0.0.1:18080 and sign in. The target console windows and the wall
show live service state. Discovery is restricted to the lab subnet, with TCP
ports 22, 80, 443, 2222, 5693 and 8080, and UDP 161. Monitoring checks run every
minute; the presentation session timeout is two hours.

Before starting, check for existing headless target processes as well as the
VirtualBox VM list. This setup encountered two VirtualBox sessions with
different running-VM views. Starting the same targets twice caused duplicate
IPs and filesystem errors; the targets were recovered from their clean
snapshots. Use one VirtualBox session and one instance of each VM.

## Suggested walkthrough

1. Show Dashboard, Network Health, Device Inventory and System Status.
2. Rescan the lab and show HTTP on `app01:8080` and SSH on `legacy01:2222`.
3. Open Plugin Manager and inspect the HTTP, SSH, SNMP and NCPA plugins.
4. Show CPU, memory and disk monitoring on `web01` after NCPA deployment.
5. Stop the web service, wait for the alert, acknowledge it, and restore it:

   ```bash
   python3 demo/demo_lab.py break web01 http
   python3 demo/demo_lab.py wall --once
   # After showing the alert in Pinpoint:
   python3 demo/demo_lab.py fix web01 http
   python3 demo/demo_lab.py wall --once
   ```

   Nginx serves both HTTP and HTTPS, so both go down together. Allow a few
   minutes for Nagios retries and Pinpoint polling.

6. Show History, Reports and System Logs after recovery.
7. Use the NCPA wizard on `legacy01` to demonstrate deployment over SSH port
   2222. Use `python3 demo/demo_lab.py creds` for the target login.
8. Show Accounts, Roles and Settings. Email delivery requires separate Gmail
   SMTP configuration and has not been configured by this setup.

## Manually stop and restore a service inside a device VM

For a simple demonstration, use **web02 (10.77.0.3)**: it has one HTTP service
on port 80. Run the following commands **inside web02**, not on the laptop or
the Pinpoint appliance. Open its VirtualBox console and sign in with username
`demo` and password `pinpoint-demo`. Alternatively, from the repository root
on the laptop, open its management shell:

```bash
python3 demo/demo_lab.py shell web02
```

Confirm nginx is running, then stop it:

```bash
sudo systemctl status nginx --no-pager
sudo systemctl stop nginx
systemctl is-active nginx
```

The last command should print `inactive` and return a nonzero exit status.
This is expected when the service is stopped. The VM remains running and SSH
continues to work.

From another terminal on the **laptop**, show the service board:

```bash
python3 demo/demo_lab.py wall --once
```

Web02's HTTP row should read `DOWN`. For a direct network check, run this
**inside the Pinpoint appliance**:

```bash
curl --connect-timeout 3 --max-time 5 -I http://10.77.0.3/
```

The HTTP request should fail while nginx is stopped. In Pinpoint, use Device
Inventory to identify the device at `10.77.0.3`, then show its HTTP service in
System Status and the active alert on Dashboard. Monitoring checks run every
minute; allow a few minutes for retries and polling. Acknowledge the alert
with a demo comment if you want to show acknowledgement. Leave the service
stopped until the audience has seen the failure.

Bring the service back with these commands **inside web02**:

```bash
sudo systemctl start nginx
systemctl is-active nginx
sudo systemctl status nginx --no-pager
```

The active-state command should now print `active`. Repeat the laptop's
`wall --once` command: web02's HTTP row should read `UP`. Repeat the curl
command inside the appliance: it should return `HTTP/1.1 200 OK`. After the
next monitoring checks, Pinpoint should show the service as OK and clear
the active failure. Show History to explain the failure and recovery.

### Commands for the other device services

Each command below runs **inside the VM named in its row**. Use the VM
console or `python3 demo/demo_lab.py shell VM` from the laptop. The management
shell remains available when the monitored SSH service is stopped.

| Device | Monitored service | Stop | Start | Check local state |
|---|---|---|---|---|
| web01 | HTTP 80 and HTTPS 443 together | `sudo systemctl stop nginx` | `sudo systemctl start nginx` | `systemctl is-active nginx` |
| web02 | HTTP 80 | `sudo systemctl stop nginx` | `sudo systemctl start nginx` | `systemctl is-active nginx` |
| app01 | HTTP 8080 | `sudo systemctl stop nginx` | `sudo systemctl start nginx` | `systemctl is-active nginx` |
| snmp01 | SNMP 161/UDP | `sudo systemctl stop snmpd` | `sudo systemctl start snmpd` | `systemctl is-active snmpd` |
| Any target | Monitored SSH (2222 on legacy01; 22 on the others) | `sudo systemctl stop ssh` | `sudo systemctl start ssh` | `systemctl is-active ssh` |

For web01, stopping nginx intentionally affects both HTTP and HTTPS. For an
SSH failure demonstration, use the console or management shell so you can
start SSH again. Do not stop `demo-mgmt-sshd`; it is the separate management
connection used by the lab controls.

## Restore the appliance baseline

The `demo-ready` snapshot includes the installed application, administrator,
demo settings and discovered devices. The lower `os-nagios-ready` snapshot is
the installer baseline and contains no application.

```bash
scripts/vmlab down
VBoxManage snapshot pinpoint-qa-appliance restore demo-ready
scripts/vmlab up
```

An appliance snapshot does not restore target VMs. Keep their agent state
consistent with the appliance. Restore services using `fix VM all`; avoid
resetting target snapshots after deploying NCPA unless you intend to deploy
the agents again.

Stop the lab after the presentation:

```bash
python3 demo/demo_lab.py down
scripts/vmlab down
```

Observed setup results are recorded in the
[demo-ready report](../docs/test-runs/2026-10-12-demo-ready/REPORT.md).
