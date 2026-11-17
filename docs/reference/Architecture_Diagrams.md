# Architecture and example deployment diagrams

Two hand-written Mermaid diagrams, kept as text so they are easy to review and
change. The entity relationship diagram is separate and generated:
[`ERD.md`](ERD.md).

| Diagram | Shows | Source of truth |
|---|---|---|
| [Layered overview](#layered-overview) | The paper's three-layer view: web interface, PinPoint modules, monitored infrastructure | Capstone paper, Chapter 4, Figure 61 |
| [Software architecture](#software-architecture) | The parts inside the PinPoint server and how they talk | [`System_Overview_and_Architecture.md`](../../spec%20files/System_Overview_and_Architecture.md), Technical Manual sections 1.4 and 2.2 |
| [Example deployment](#example-deployment) | A generic, illustrative placement of the server on a network | Technical Manual section 5 |

The capstone paper's architecture figure (Chapter 4, Figure 61) is redrawn here
as the layered overview, and the software architecture adds the detail the
paper leaves out. Where they differ, the specification and the code win.

## Layered overview

Redrawn from the capstone paper (Chapter 4, Figure 61): a 3-layer architecture.

```mermaid
flowchart TB
  subgraph Presentation["Presentation layer: web interface"]
    ADMIN["Network administrator"]
  end

  subgraph Application["Application layer: PinPoint system modules"]
    DEPLOY["Deployment automation"]
    MONCFG["Monitoring configuration"]
    ALERTS["Alert system"]
  end

  subgraph Infrastructure["Infrastructure layer: monitored by Nagios Core"]
    SERVERS["Servers"]
    ROUTERS["Routers"]
    SWITCHES["Switches"]
    ENDDEV["End devices"]
  end

  ADMIN <--> MONCFG
  DEPLOY <--> MONCFG
  MONCFG <--> ALERTS
  MONCFG <--> Infrastructure
  SERVERS --> ROUTERS --> SWITCHES --> ENDDEV
```

How the paper's modules map to the code (details in the next diagram):

| Paper module | In the code |
|---|---|
| Deployment automation | Network discovery and NCPA deployment (`app/network_discovery/`, `app/ncpa_deployment/`) |
| Monitoring configuration | Nagios config generation (`create_host_cfg.py`), Plugin Manager (`app/api/plugin/`) and the settings that feed them |
| Alert system | Notification policy, recipients, escalations, acknowledgements and maintenance windows; Nagios sends the email |

## Software architecture

One Ubuntu Server host runs everything. There is no cloud component.

```mermaid
flowchart TB
  subgraph Client["User's computer"]
    UI["Browser: React and TypeScript single-page app"]
  end

  subgraph Host["PinPoint server (one Ubuntu Server host)"]
    NGX["Nginx (from the installer): serves the built client, proxies /api"]

    subgraph Flask["Flask application (Gunicorn, one worker)"]
      API_USER["/api/user: sign-in, accounts, roles, preferences"]
      API_SYSTEM["/api/system: monitoring views, history, reports, logs, settings, discovery, NCPA deployment"]
      API_PLUGIN["/api/plugin: Plugin Manager"]
      SCHED["APScheduler: Nagios polling, retention, automation"]
      CFGW["Config writer: generates Nagios host and service config"]
    end

    SYSDB[("system.db: users, settings, discovery, plugins, audit")]
    HISDB[("history.db: polled Nagios status snapshots")]

    subgraph NagiosBox["Nagios Core"]
      NCORE["Nagios Core: runs checks, sends notifications"]
      CGI["JSON CGIs: status, object, archive"]
      PLUGINS["Plugin directory"]
      SPOOL["Event-handler spool"]
    end
  end

  DEVICES["Monitored devices"]
  SMTP["SMTP relay"]

  UI -->|"same-origin /api, session cookie"| NGX
  NGX --> API_USER
  NGX --> API_SYSTEM
  NGX --> API_PLUGIN
  API_USER --> SYSDB
  API_SYSTEM --> SYSDB
  API_PLUGIN --> SYSDB
  SCHED --> HISDB
  SCHED -->|"poll"| CGI
  API_SYSTEM -->|"read status, send commands"| NCORE
  CFGW -->|"write config, validate, reload"| NCORE
  NCORE --> PLUGINS
  NCORE --> SPOOL
  SPOOL -->|"remediation events"| SCHED
  NCORE -->|"checks"| DEVICES
  API_SYSTEM -->|"nmap scan, SSH install"| DEVICES
  NCORE -->|"alert email via msmtp"| SMTP
```

How to read it:

- Browsers only ever talk to Nginx. Flask, the databases and Nagios's web
  interface are not exposed to users.
- **Nagios owns monitoring**: it runs checks and decides state. PinPoint polls
  Nagios and stores snapshots in `history.db`; it does not run checks itself.
- **PinPoint owns everything else**: accounts, settings, discovery, plugin
  administration, audit logs and the web interface, all in `system.db`.
- PinPoint writes Nagios configuration, validates it with Nagios, then reloads
  Nagios. It never edits Nagios state directly.

### Checked against the specification

Compared with the runtime diagram in
[`System_Overview_and_Architecture.md`](../../spec%20files/System_Overview_and_Architecture.md):

| Item | Specification | This diagram | Reason |
|---|---|---|---|
| Nginx and Gunicorn | Not drawn; the spec shows the Flask application only | Drawn | Delivered by the separate installer; they explain how the browser reaches Flask |
| `/api/user`, `/api/system`, `/api/plugin` | Listed | Same three groups | Same |
| `system.db`, `history.db` | Listed | Same | Same |
| Nagios JSON CGIs, config files, plugin directory | Listed | Same | Same |
| APScheduler | Listed | Same, plus the event-handler spool feeding remediation | Spool added from Technical Manual section 2.5 |
| Mail | Not drawn | SMTP relay via msmtp | Alert email leaves through Nagios, not Flask |
| Remote devices through nmap and SSH/NCPA | Listed | Same, split into "checks" (Nagios) and "scan, install" (Flask) | Shows which part talks to devices |

### Comparison with the capstone paper

Compared with Chapter 4, Figure 61:

| Item | Paper | This repository | Reason |
|---|---|---|---|
| Layers | Three: presentation, application, infrastructure | The layered overview keeps them; the software architecture shows what runs inside | The paper is a concept view |
| Nagios Core | A label on the infrastructure layer ("monitored by Nagios Core") | A component on the server that runs every check and decides state | Nagios sits between PinPoint and the devices; PinPoint does not run checks |
| Modules | Three boxes in a hub: deployment automation, monitoring configuration, alert system | Three API groups (`/api/user`, `/api/system`, `/api/plugin`) sharing two databases, a scheduler and a config writer | The code has no single hub; modules are independent and share the databases |
| Not in the paper | | Accounts and roles, reports and history, audit logs, Plugin Manager as its own area, remediation, backups, the scheduler, `system.db` and `history.db`, Nginx and Gunicorn | Added after the figure, or too detailed for it |
| Device chain | Servers to routers to switches to end devices | Not drawn as a chain: devices are checked by Nagios individually; parent links are optional and set by hand (Topology page) | The arrows in the paper show how the network is wired, not data flow |
| Administrator arrow | Straight to "monitoring configuration" | Browser to Nginx, then to the Flask API | Same intent, with the real path drawn |

## Example deployment

An **illustration only**. Real addresses, VLANs and firewall layout depend on
each site and are decided by the people who run the network. The addresses below
are reserved for documentation (RFC 5737) and are not in use anywhere. The
capstone paper has no network diagram; this one is new.

```mermaid
flowchart LR
  subgraph Users["User network (example 198.51.100.0/24)"]
    BROWSER["Administrator browsers"]
  end

  subgraph ServerNet["Server network (example 192.0.2.0/24)"]
    PINPOINT["PinPoint server (example 192.0.2.10)"]
  end

  subgraph Monitored["Monitored networks (example 203.0.113.0/24)"]
    DEVICES["Servers, workstations, network devices"]
  end

  subgraph Mail["Mail"]
    SMTP["SMTP relay"]
  end

  BROWSER -->|"web interface (HTTP or HTTPS)"| PINPOINT
  PINPOINT -->|"ICMP, SNMP, SSH, NCPA, service checks"| DEVICES
  PINPOINT -->|"SMTP with STARTTLS"| SMTP
```

Guidance that holds on any network (the full table with protocols and
default ports is Technical Manual section 5.5, and firewall guidance is
section 5.7):

- Put the PinPoint server where it can reach every network it monitors. Use a
  static address or a DHCP reservation so users and firewall rules keep working.
- Let only administrator networks reach the web interface.
- Let only the PinPoint server reach the agent and management services on
  monitored devices.
- Allow the server to reach the mail relay and nothing more outbound than it
  needs.
- Keep the example addresses as examples: do not record a real subnet, VLAN or
  firewall rule in this repository.
