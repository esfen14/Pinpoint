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
- [x] How long the Topology map takes to show a parent change (0.15 s to save; Refresh shows it). *(verified 2026-11-25; the Nagios-rejection message could not be provoked, noted in the guide)* (`Topology.md:35`)

### History, reports, logs
- [x] Does the History custom range offer a time of day or dates only? (`Alerts_and_Notification_History.md:25`, `User_Manual.md:485`) *(answered from source 2026-11-24)*
- [x] Previous state and duration near the start of a range with no earlier Nagios record. (`Alerts_and_Notification_History.md:44`) *(answered from source 2026-11-24)*
- [x] Two Nagios records identical to the second: can the wrong row open? (`Alerts_and_Notification_History.md:70`) *(answered from source 2026-11-24)*
- [x] Which categories **Audit Logging** covers. (`System_Logs.md:19`) *(answered from source 2026-11-24)*
- [x] File formats offered when exporting a log entry. (`System_Logs.md:27`) *(answered from source 2026-11-24)*

### Plugins, settings, NCPA, recovery
- [x] Which command fields can be edited in **Override a command**. (`Plugin_Manager.md:71`) *(answered from source 2026-11-24)*
- [x] Can the Pinpoint service account write to the plugin folder (needed for **Update**)? *(tested 2026-11-25: the folder yes, the plugin files no; Update fails with a 500 until the file is owned by `pinpoint`; Roll back works)* (`Plugin_Manager.md:73`)
- [x] Is each General setting stored per person or system-wide? (`Settings.md:44`) *(answered from source 2026-11-24)*
- [x] Does Maintenance Mode (Settings) behave like a maintenance window? (`Settings.md:59`) *(answered from source 2026-11-24)*
- [x] Full list of tables under **Settings → Plugins**. (`Settings.md:67`) *(answered from source 2026-11-24)*
- [x] **Register agent** end to end. *(verified on the QA appliance 2026-11-25)* (`User_Manual.md:581`; done once on `db01`, so this can now be written up. Wizard deploy is issue #336.)
- [x] A single walkthrough of the **Remediation** page. *(verified 2026-11-25; the lab appliance needed a hand-installed event handler and spool folder; a fresh ISO install has both)*
- [x] Per-service recovery walkthrough. *(2026-11-25: the restart-nagios action ran and the drawer was checked; the switch itself needs an SSH-trusted NCPA Linux device, not available until #336)* (`User_Manual.md:665`, `manuals/README.md:23`)

## B. Browser and device checks (a person with the devices)

- [x] Supported browsers and versions. *(2026-11-25: minimums from the build toolchain; load check in Playwright Chromium, Firefox and WebKit. Real Edge and Safari not tried)* (`User_Manual.md:124`, `Technical_Manual.md:356`)
- [x] Use on tablets and phones. *(2026-11-25, emulation only: tablet width fits, phone does not, and the sidebar toggle does nothing; a real-device check is still worth doing)* (`User_Manual.md:123`)

## C. Answer from the installer repo (`PinPoint-Installer`), not this repo

Done 2026-11-19 by reading the public installer repo; answers are in the Technical Manual and Hand_Off. The installer maintainer should still confirm them.

- [x] Where the installer reports the bootstrap administrator email and password. (`Technical_Manual.md:707`, `Hand_Off.md:47`)
- [x] On-disk location of the NCPA deployment SSH key and NCPA token. (`Technical_Manual.md:710`, `Hand_Off.md:50`)
- [x] Installer media (ISO or script) and the upgrade command. (`Technical_Manual.md:656-667`, `:888`)
- [x] What the installer configures for the server address, host firewall and HTTPS. (`Technical_Manual.md:150`, `:377`, `:396`, `:411`, `:425`, `:770`, `:801`)
- [x] Nagios unit name on the appliance. (`Technical_Manual.md:716`)
- [x] Whether production uses `https://`. (`User_Manual.md:133`)
- [x] How to recover when the service is stopped for `VACUUM`. *(tried on the ISO install 2026-11-25; small, healthy database only)* (`Technical_Manual.md`, section 11.5)

## D. Decisions for the team or the site

- [x] Support contact. *(team, 2026-11-25: Lorraine, Rafael or Elle; limited availability during OJT; no personal contact details published)* (`User_Manual.md` 6.3)
- [ ] University IT contact after hand-off. **Still to be added**: contact person and deployment scope (CICT or campus-wide) unknown. (`Hand_Off.md`, Contacts)
- [x] Network addressing, VLANs and firewall placement. *(team, 2026-11-25: unknown, and not to be put in this public repository)* (`Technical_Manual.md` 2.4, 5.4)
- [x] Which Linux distributions are supported for NCPA deployment. *(answered from source 2026-11-25: Debian or Ubuntu based)* (`Technical_Manual.md:303`)
- [x] Hand-off reviewer for the installer. *(team, 2026-11-25: the CICT IT team; review not yet done)* (`Hand_Off.md`, Repositories)

## E. Needs a measurement

- [x] Measured bandwidth on a named appliance, and a recorded lab measurement. *(2026-11-25, QA appliance, one scan)* (`Technical_Manual.md` 5.8, 10.4)
- [x] Server sizing. *(team, 2026-11-25: state the tested limit of 14 hosts and the measured metrics instead; production-scale test not done, rows-per-host stays in #82)* (`Technical_Manual.md` 3.1, 10.4)

## Suggested order

1. **Group A** in one sitting on the lab. It clears about half the list and needs no one else.
2. **Group C** in one pass through the installer repo. It clears most of the Technical Manual.
3. Send **D** to the adviser and team as one question list.
4. **B** and **E** last; they need devices or a measured run.

## Not TBC, but related

- The manual guides still say "not yet followed step by step on a demo build" in their verification notes. Remove that line per guide as you finish its Group A items.
- Issue #336 (SSH container for the NCPA wizard) unblocks the wizard walkthrough.
