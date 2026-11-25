## 4. Software requirements

### 4.1 Operating system

| Role | OS | Basis |
|---|---|---|
| PinPoint appliance | Ubuntu Server 22.04.5 LTS | Installer contract |
| Monitored Linux hosts (NCPA deployment) | Debian or Ubuntu based; the deployment refuses others ("Unsupported distro") and installs from `repo.nagios.com` for the host's release codename | Lab targets ran Ubuntu 22.04 and 24.04; other releases untested |
| Monitored Windows hosts | Windows 10 observed with NCPA 3.5.0 (manual install) | #274 report |
| Development | Any OS with Python 3.14 and Node 22; dev container provided | `.devcontainer/` |

### 4.2 Languages, frameworks and libraries

| Layer | Component | Version (source) |
|---|---|---|
| Backend language | Python | 3.14 (`README.md`) |
| Web framework | Flask | 3.1.3 (`server/requirements.txt`) |
| ORM | SQLAlchemy / Flask-SQLAlchemy | 2.0.50 / 3.1.1 |
| Migrations | Alembic / Flask-Migrate | 1.18.4 / 4.1.0 |
| Sessions | Flask-Login | 0.6.3 |
| Scheduling | APScheduler | 3.11.3 |
| SSH | Paramiko | 5.0.0 |
| Discovery | python3-nmap | 1.9.1 (needs the `nmap` binary) |
| Encryption | cryptography (Fernet) | 50.0.0 |
| Frontend | React / React DOM | ^19.2.6 (`client/package.json`) |
| Language | TypeScript | ~6.0.2 |
| Build | Vite | ^8.0.12 |
| Routing | react-router-dom | ^7.17.0 |
| UI | Tailwind CSS, lucide-react, Recharts, @xyflow/react | ^4.3.0, ^1.17.0, ^3.8.1, ^12.11.0 |
| Tests | pytest; Vitest and Testing Library | `requirements-test.txt`; ^3.2.7 |

Lockfiles and requirements files are the source of truth for exact versions.

### 4.3 DBMS

SQLite (bundled with Python). No separate database server.

### 4.4 Web and application servers

| Component | Version / setting | Owner |
|---|---|---|
| Nginx | Distribution package; listens on 80 | Installer |
| Gunicorn | 1 worker, 4 threads, user `pinpoint`, service `pinpoint-gunicorn.service`, loopback `127.0.0.1:8000` **[A]** (lab config) | Installer |
| Nagios Core | 4.5.11; web UI moved to `127.0.0.1:8081` | Installer |
| Nagios Plugins | 2.4.12 | Installer |
| `check_ncpa.py` | 1.2.4 | Installer |
| msmtp (as `/usr/sbin/sendmail`) | Distribution package | Installer |
| nmap, snmp utilities (`snmpwalk`) | Distribution packages | Installer **[A]** |

### 4.5 Development tools

Git, GitHub CLI, Node 22 and npm, Python 3.14 with venv, Docker (local lab),
VirtualBox (VM lab), Playwright (QA smokes). See
[`Agent_Workflow_and_CI.md`](../../spec%20files/Agent_Workflow_and_CI.md).

### 4.6 Compatibility notes

- `interval_length=60` must hold in `nagios.cfg`.
- `check_ncpa.py` needs a `python` command or a python3 shebang on the
  appliance (fixed in the installer).
- Browser support. The client build targets the toolchain minimums: Chrome and
  Edge 111, Safari 16.4 (Vite 8), and Firefox 128 (Tailwind CSS 4; Vite alone
  allows 114). Older versions were not tested. On 2026-11-25 sign-in and six pages
  (Dashboard, Network Health, Device Inventory, Topology, Remediation, Settings)
  loaded with no page errors in Playwright's Chromium 156, Firefox 157 and WebKit
  27.2 at 1366 px. This was a load check, not a test of every control.
- Screen size (emulated, not real devices): the six pages fit a tablet-width
  viewport (712 px) without page-level sideways scrolling. On an emulated Pixel 7
  they did not fit. Phone-sized screens are not supported. That check ran before
  the header's **Toggle sidebar** button was made to hide the sidebar
  ([#342](https://github.com/esfen14/Pinpoint/issues/342)); screen sizes have not
  been measured again since.
