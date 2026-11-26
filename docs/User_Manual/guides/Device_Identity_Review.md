# Review and merge duplicate device records

> **Verification status.** Followed on 2026-11-26 on the local lab, whose cloned
> servers raise duplicate identity reviews: opening a review from the table and
> from the device drawer, address history, the device search, **Keep both
> records**, two merges (one with Nagios stopped) and a rescan. Not followed:
> **Keep record unchanged**, other review types, merging a retired record, the
> permission rules and a refused stale selection. Those come from the
> specifications and source.

Open Device Inventory and find **Needs Review** above the host table. Its count
includes unresolved device identity issues even when a record is outside the
Monitored filter. Port-service mismatches are handled separately.

Choose **Review** to compare IDs, names, addresses, monitoring state and identity
evidence. A record without a display name is headed **Display name
unavailable**; tell it apart by its **Nagios host name**, **Current IP** and
**Stable device ID**. Use **Load address history** for previous addresses. A
participating device's information drawer also shows **This device needs identity
review**, with a **Review** link to the same comparison. Missing evidence is
labelled; it does not confirm that records belong together.

Merge only when you have independently verified that both records represent the
same physical device. Matching names or IP addresses alone are not proof. For
example, a replaced computer may reuse the old computer's IP and must remain a
separate device. A recognized IP change already updates the existing record and
does not need a merge.

A duplicate identity review that says two records have the same SSH host key or
certificate usually means the machines were cloned from one image. Pinpoint lists
and monitors each separately. Merge them only if they are one machine, such as one
with two network cards. Give each cloned machine its own SSH host key so that new
addresses are not flagged.

## Keep separate records

For separate machines, choose **Keep both records** in the comparison, check the
two records and confirm with **Keep both records**. Neither device changes, the
review leaves **Needs Review** and later scans do not raise it again for these
records; the page confirms "Review dismissed. No device was changed." There is
no undo. A review that names only one record (a device also seen
on a second address) offers **Keep record unchanged** instead; the extra address
stays unmonitored. Only duplicate identity reviews offer this, and it requires
host edit permission. If saving fails, the error is shown and the review stays
listed.

## Merge duplicate records

1. Choose **Device record to keep**: the record with the intended monitoring
   settings and current address. This is the surviving target.
2. Choose **Duplicate record to merge**: the source to remove from monitoring.
   If a record is missing, use **Search discovered devices** with a name, IP
   address or ID, then choose **Add** on the result. Search includes records
   outside Monitored; a record that is already merged is not listed.
3. Choose **Review merge** (available once two different records are selected)
   and check both IDs, names and IPs. The target keeps
   its address and its records take precedence where settings conflict. Source
   identifiers, address history and nonconflicting ports move to the target.
4. Confirm **Merge duplicate**. The source becomes Merged and leaves monitoring.
   Historical monitoring snapshots stay under their original Nagios host names;
   they are not combined. No undo action is provided.

Cancel or close at any time before saving to leave everything unchanged. Opening
a review never resolves it. While saving, wait for the result; the page then
shows **Merge saved**. A message that begins "Merge saved. Nagios configuration
warning" means the database merge succeeded but Nagios could not be
updated; do not retry that merge. Give the configuration warning to the system
administrator. The page refreshes its reviews, host list and counts automatically.

Review requires discovery permission. Identity/address details also require host
view permission; merging requires host edit permission. A retired record can be
a source, but a retired or merged record cannot be the target. A stale selection
may be refused by the server; review the choices before trying again.
