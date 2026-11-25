# Storage and Nagios logs

Open **Dashboard → Appliance storage** to see the size of each database,
database backups and Nagios archives, plus free disk space at each location.
The card warns below 10% free space. “Unavailable” means a location could not be
measured; “At least” means the folder scan reached its budget and the total is
partial. The measurements do not need a monitoring plugin. Viewing requires the
Dashboard permission.

Open **System Logs → Nagios log** for the latest 200 lines within the last
64 KiB, in time order with the newest at the bottom. Use **Refresh Nagios log**
to fetch new entries. This is a bounded view, so it cannot search older rotated
logs. Host/service state fields remain visible, including names and addresses;
plugin output, commands and other free-form messages are redacted to protect
credentials. Missing/unreadable files show an unavailable message. Viewing
requires the System Logs permission. The existing five audit categories retain
their filters and export menu.

Nagios owns its own log rotation. The paired installer release adds host-wide
journald defaults of 100 MiB and seven days, and rotates installer file logs
weekly with four archives. Administrators' existing journal limits and edited
rotation rules take precedence. Journald rotates whole files, so an active file
can temporarily exceed the size target; the installer does not delete old
journals. See the installer release notes before upgrading. Application storage
retention settings control database records/backups; they do not change the
host journal policy.
