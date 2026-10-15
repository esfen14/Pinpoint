# Review and merge duplicate device records

Open Device Inventory and find **Needs Review** above the host table. Its count
includes unresolved device identity issues even when a record is outside the
Monitored filter. Port-service mismatches are handled separately.

Choose **Review** to compare IDs, names, addresses, monitoring state and identity
evidence. Use **Load address history** for previous addresses. A participating
device's information drawer also has **This device needs identity review** and
opens the same comparison. Missing evidence is labelled; it does not confirm
that records belong together.

Merge only when you have independently verified that both records represent the
same physical device. Matching names or IP addresses alone are not proof. For
example, a replaced computer may reuse the old computer's IP and must remain a
separate device. A recognized IP change already updates the existing record and
does not need a merge.

1. Choose **Device record to keep**: the record with the intended monitoring
   settings and current address. This is the surviving target.
2. Choose **Duplicate record to merge**: the source to remove from monitoring.
   If a record is missing, search discovered devices by name, IP address or ID
   and add it to the comparison. Search includes records outside Monitored.
3. Choose **Review merge** and check both IDs, names and IPs. The target keeps
   its address and its records take precedence where settings conflict. Source
   identifiers, address history and nonconflicting ports move to the target.
4. Confirm **Merge duplicate**. The source becomes Merged and leaves monitoring.
   Historical monitoring snapshots stay under their original Nagios host names;
   they are not combined. No undo action is provided.

Cancel or close at any time before saving to leave everything unchanged. Opening
a review never resolves it. While saving, wait for the result. A **Merge saved**
configuration warning means the database merge succeeded but Nagios could not be
updated; do not retry that merge. Give the configuration warning to the system
administrator. The page refreshes its reviews, host list and counts automatically.

Review requires discovery permission. Identity/address details also require host
view permission; merging requires host edit permission. A retired record can be
a source, but a retired or merged record cannot be the target. A stale selection
may be refused by the server; review the choices before trying again.
