# Maintenance windows

Administrators with **maintenance.manage** can open **Maintenance** in the sidebar to schedule planned work. A maintenance window puts devices into Nagios **scheduled downtime**, so alerts and notification email for them stop while the work is done, and the downtime ends by itself at the end time. Run `flask sync-permissions` after upgrading to add the permission (granted to Administrator only); grant it to other roles under **Manage Roles**.

This is not the **Maintenance Mode** switch in **Settings → System**. That switch only pauses PinPoint's own scheduled scans, update checks and security checks and shows a notice; it does not silence any alert. Use a maintenance window to silence alerts.

## Create a window

1. Choose **New window**.
2. **Devices:** one monitored device, or **All monitored devices**. A paused, retired or missing device cannot be chosen.
3. **Starts** and **Ends:** typed in your display time zone (**Settings → General → Time Zone**) and stored as UTC. A one-off window can last up to 30 days and must end in the future.
4. **Repeats:** does not repeat, every day or every week. A repeating window repeats at the same local time (it follows daylight saving when the time zone is your browser's) and cannot be longer than one day or one week. **Stop repeating after** is optional and at most 366 days after the start.
5. **Reason:** up to 200 characters.

PinPoint tells Nagios about each occurrence about 10 minutes before it starts. Until then the window shows as **Scheduled** with its next occurrence. Once Nagios is checking, the hosts and services show the existing downtime indicators.

## Edit and cancel

- **Edit** replaces an active window. Downtime already handed to Nagios for its unfinished occurrences is deleted first and scheduled again from the new times.
- **Cancel** (asks for a second click) deletes the pending and running downtime of that window. Alerts for the devices resume; a problem that is still present notifies again.
- If Nagios could not be told to delete the downtime, the window is still changed and a notice says that Nagios was not updated. The downtime ends at its original end time, or can be removed in Nagios.

## When something goes wrong

If Nagios does not accept the command (for example the command pipe is unavailable, or the device was paused or is no longer in Nagios), PinPoint retries up to 3 times, one minute apart. After that the occurrence shows **Failed for …** with the reason in the Status column and an entry is written to the activity log. Fix the cause and edit the window (saving it sends it again), or create a new one. A window that has ended shows as **Completed**.

All changes (create, edit, cancel, and each time downtime is sent or fails) are written to **System Logs → Activity Log**.
