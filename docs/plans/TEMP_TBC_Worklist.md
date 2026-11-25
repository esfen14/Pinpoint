# TEMPORARY: TBC worklist

Every **TBC** (To Be Confirmed) in the manuals, grouped by how it gets resolved.
Delete this file when the list is done. When an item is settled, replace the TBC in the
source file with the confirmed fact (or remove the sentence), then tick it here.
Lab: the QA appliance (see the screenshots work); line numbers are as of commit `5dbd91b3`.

Total: about 80 mentions in 13 files (User Manual 14, Technical Manual 25, Hand_Off 4,
guides 36). Several repeat the same question.

## A. Check on the running demo lab (you or an agent, about 1 to 2 hours)

User Manual and guides; each is a "click it and see".

### Sign-in and accounts
- [x] What **Remember me** changes in practice. (`Login_Accounts_and_Roles.md:33`, `User_Manual.md:152`) *(answered from source 2026-11-24)*
- [x] Exact permission set of **Manager** and **Staff** on a production install (`flask init-production` vs the dev `flask seed`). (`Login_Accounts_and_Roles.md:107`, `User_Manual.md:722-723`) *(answered from source 2026-11-24)*
- [x] Do permission changes apply to a signed-in person at their next request? (`Login_Accounts_and_Roles.md:113`) *(answered from source 2026-11-24)*
- [x] Is there a self-service password change outside the forced change window? (`User_Manual.md:766`) *(answered from source 2026-11-24)*

### Dashboard and navigation
- [x] How many days ahead **Running out soon** looks. (`Dashboard_and_Network_Health.md:39`) *(answered from source 2026-11-24)*
- [x] Card order and labels for each **Dashboard Layout** (default, compact, expanded). (`Dashboard_and_Network_Health.md:80`) *(answered from source 2026-11-24)*
- [x] Exact sidebar order on a demo build. (`User_Manual.md:250`; the screenshots show it, so this one is nearly done) *(answered from source 2026-11-24)*

### Device Inventory, discovery, topology
- [x] Per-device limit for monitored interfaces, shown on screen. (`Device_Inventory.md:83`) *(answered from source 2026-11-24)*
- [x] Default wait before a missing device is archived. (`Device_Inventory.md:109`) *(answered from source 2026-11-24)*
- [x] What is kept when a running scan is stopped part way. (`Network_Discovery.md:38`) *(answered from source 2026-11-24)*
- [x] Number of missed scans before a port is **missing**. (`Network_Discovery.md:50`) *(answered from source 2026-11-24)*
- [ ] How long the Topology map takes to show a parent change, and the message when Nagios rejects it. (`Topology.md:35`)

### History, reports, logs
- [x] Does the History custom range offer a time of day or dates only? (`Alerts_and_Notification_History.md:25`, `User_Manual.md:485`) *(answered from source 2026-11-24)*
- [x] Previous state and duration near the start of a range with no earlier Nagios record. (`Alerts_and_Notification_History.md:44`) *(answered from source 2026-11-24)*
- [x] Two Nagios records identical to the second: can the wrong row open? (`Alerts_and_Notification_History.md:70`) *(answered from source 2026-11-24)*
- [x] Which categories **Audit Logging** covers. (`System_Logs.md:19`) *(answered from source 2026-11-24)*
- [x] File formats offered when exporting a log entry. (`System_Logs.md:27`) *(answered from source 2026-11-24)*

### Plugins, settings, NCPA, recovery
- [x] Which command fields can be edited in **Override a command**. (`Plugin_Manager.md:71`) *(answered from source 2026-11-24)*
- [ ] Can the Pinpoint service account write to the plugin folder (needed for **Update**)? (`Plugin_Manager.md:73`)
- [x] Is each General setting stored per person or system-wide? (`Settings.md:44`) *(answered from source 2026-11-24)*
- [x] Does Maintenance Mode (Settings) behave like a maintenance window? (`Settings.md:59`) *(answered from source 2026-11-24)*
- [x] Full list of tables under **Settings → Plugins**. (`Settings.md:67`) *(answered from source 2026-11-24)*
- [x] **Register agent** end to end. *(verified on the QA appliance 2026-11-25)* (`User_Manual.md:581`; done once on `db01`, so this can now be written up. Wizard deploy is issue #336.)
- [x] A single walkthrough of the **Remediation** page. *(verified 2026-11-25; needed a hand-installed event handler and spool folder, an installer gap)*
- [ ] Per-service recovery (the **Recover automatically** switch in a Device Inventory drawer, and a restart-type action) walkthrough. (`User_Manual.md:665`, `manuals/README.md:23`)

## B. Browser and device checks (a person with the devices)

- [ ] Supported browsers and versions. (`User_Manual.md:124`, `Technical_Manual.md:356`)
- [ ] Use on tablets and phones. (`User_Manual.md:123`)

## C. Answer from the installer repo (`PinPoint-Installer`), not this repo

Done 2026-11-19 by reading the public installer repo; answers are in the Technical Manual and Hand_Off. The installer maintainer should still confirm them.

- [x] Where the installer reports the bootstrap administrator email and password. (`Technical_Manual.md:707`, `Hand_Off.md:47`)
- [x] On-disk location of the NCPA deployment SSH key and NCPA token. (`Technical_Manual.md:710`, `Hand_Off.md:50`)
- [x] Installer media (ISO or script) and the upgrade command. (`Technical_Manual.md:656-667`, `:888`)
- [x] What the installer configures for the server address, host firewall and HTTPS. (`Technical_Manual.md:150`, `:377`, `:396`, `:411`, `:425`, `:770`, `:801`)
- [x] Nagios unit name on the appliance. (`Technical_Manual.md:716`)
- [x] Whether production uses `https://`. (`User_Manual.md:133`)
- [ ] How to recover when the service is stopped for `VACUUM` (project documents nothing). (`Technical_Manual.md`, section 11.5)

## D. Decisions for the team or the site

- [ ] Support contact name, email and hours. (`User_Manual.md:835`)
- [ ] University IT contact after hand-off. (`Hand_Off.md:38`)
- [ ] Network addressing, VLANs and firewall placement, site design. (`Technical_Manual.md:207`, `:389`)
- [ ] Which Linux distributions are supported for NCPA deployment. (`Technical_Manual.md:303`; the lab used Ubuntu 22.04 and 24.04)
- [ ] Hand-off reviewer for the installer: "not reviewed for the manuals". (`Hand_Off.md:27`)

## E. Needs a measurement

- [ ] Server sizing for the production host count; measured bandwidth on a named appliance; a recorded performance test and rows-per-host figure. (`Technical_Manual.md:269`, `:430`, `:839`)

## Suggested order

1. **Group A** in one sitting on the lab. It clears about half the list and needs no one else.
2. **Group C** in one pass through the installer repo. It clears most of the Technical Manual.
3. Send **D** to the adviser and team as one question list.
4. **B** and **E** last; they need devices or a measured run.

## Not TBC, but related

- The manual guides still say "not yet followed step by step on a demo build" in their verification notes. Remove that line per guide as you finish its Group A items.
- Issue #336 (SSH container for the NCPA wizard) unblocks the wizard walkthrough.
