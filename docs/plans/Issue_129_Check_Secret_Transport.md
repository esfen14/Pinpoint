# Issue #129: check secret transport

Status: implementation incomplete; owner chose process secrecy on 2026-10-14.

## Required behavior

Preserve [issue #129](https://github.com/esfen14/Pinpoint/issues/129)'s requirement
that NCPA tokens and custom-check passwords never appear in operating-system
process arguments. Resource macros remain protected storage; passing an expanded
macro to a plugin password/token flag is insufficient. Do not weaken this
acceptance criterion or mark the macro work complete.

[Nagios macro documentation](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/macros.html)
explains expansion before execution. The existing registry renders the NCPA token
as `-t '$ARG2$'`, so its substitution with a USER macro still exposes the token.
A wrapper that reads a secret and then launches a child with `-t`/`-p` also fails
this requirement. Environment variables are not a substitute for a supported
credential input and can expose secrets through process inspection.

## Compatibility findings

Source inspection motivates the constraints below. Installed compatibility and
ownership evidence is recorded in [the partial run report](../test-runs/2026-10-14-issue-129-resource-compatibility/REPORT.md);
it does not establish live check-result or process-secrecy acceptance.

This plan feeds [Data Model and Integrations](../../spec%20files/Data_Model_and_Integrations.md)
and [Engineering Standards](../../spec%20files/Engineering_Standards.md).

| Plugin | Inspected credential input | Implementation direction |
|---|---|---|
| `check_ncpa.py` | Upstream 1.2.5 accepts the token through `-t`/`--token`; its option parser has no credential file/stdin option. | Block deployment of the secret transport until an owner-supported plugin extension or a reviewed adapter can consume the resource slot without exposing a child process argument. |
| `check_nt`, `check_radius`, `check_mysql_query` | Native C plugins may support compiled-in `--extra-opts`, which reads named INI sections. | Verify the installed executable's help and real process arguments before enabling this transport. Keep passwords out of both required arguments and the final optional-argument bundle. |
| `check_disk_smb` | The 2.4.12 Perl script accepts a password argument and passes it to a child `smbclient` command. Its SMB configuration flag is not a password-file input. | Explicitly blocked pending a supported secure credential input for both parent and child. Do not silently drop or pause existing checks. |

Sources: [NCPA client](https://github.com/NagiosEnterprises/ncpa/blob/master/client/check_ncpa.py),
[Nagios Plugins Extra-Opts](https://nagios-plugins.org/doc/extra-opts.html),
[SMB plugin 2.4.12](https://github.com/nagios-plugins/nagios-plugins/blob/release-2.4.12/plugins-scripts/check_disk_smb.pl).
The `--extra-opts` capability is build-dependent; plugin name alone is not proof.

## Implementation plan after compatibility is resolved

1. Add failing process tests that hold a synthetic check open and inspect parent
   and child `/proc/<pid>/cmdline`. Compare output, performance data and exit code
   against the existing check. Exercise timeout, connection failure and rejected
   authentication without logging the synthetic credential.
2. Build commands from validated public fields and secret slot identifiers.
   Substitute only the known secret field, not matching substrings across an
   entire command. A dummy token `cpu` currently also rewrites `cpu/percent`.
   Assert that metric paths, names and unrelated arguments stay unchanged.
3. Persist stable slot identity across regenerations, exclude externally owned
   USER slots, and reclaim removed/paused device and check secrets. Empty desired
   secret sets must clear the owned block. Assert upgrade command equivalence.
4. Reject missing/unwritable resource files before publishing candidates. Preserve
   `nagios:nagios` and 0660 on resource updates; hosts.cfg must become 0640 at the
   live destination, not only in the generated temporary file. The atomic writer
   now uses a private unique temporary file and copies existing metadata, refusing
   replacement if ownership cannot be retained. Installer privilege compatibility
   remains unverified; do not grant broad chown or directory-write access here.
5. Use one transaction for resources, any extra-options credential files and
   hosts.cfg across regeneration, discovery and post-deployment config paths.
   Back up before changing any resource; restore on generation, validation, copy
   or reload failure. A resource change requires validation/reload even when
   hosts.cfg's timestamp-normalized content is unchanged. Never proceed after a
   backup failure. Remove backups only once application succeeds.
6. Update the five owning specs, Help text and administrator storage/upgrade
   instructions only for implemented and verified behavior. Run `verify.sh all`,
   then the authorized VM cases and sanitized report before requesting review.

## Implemented config safeguards

Secret substitution now targets only declared secret fields. Owned key/slot
metadata persists across regenerations; external slots are reserved, removing a
device from generated hosts frees its slot, and empty desired sets clear secrets.
Unsafe permissions, malformed blocks and collisions are rejected before writing.
Missing or failed resource writes stop candidate publication. All three generation
entry points snapshot resources in memory under the shared lock and restore on
failure or cancellation; resource-only changes trigger validate/apply. Apply
restores both files before a rollback reload and sets live hosts.cfg to 0640.
These safeguards do not implement secure plugin credential transport.

## Required installer handoff

A scoped mechanism must atomically update only the configured resource file while
preserving nagios:nagios and 0660, and support restoring its previous bytes. A
possible contract is a root-owned helper accepting only managed block/slot data through stdin, with an exact
executable sudoers grant to pinpoint, a fixed allowlisted destination, strict
block/value validation, private sibling temporary files and no secret-bearing
logs/output. The helper itself reads and retains every byte outside the owned
block; the caller cannot supply replacement contents for other owners' lines.
The helper and its interpreter must be root-owned and must not import mutable
application code while privileged. It must not accept arbitrary paths, arbitrary
commands, chown targets or broad directory privileges. Both failed apply and
rollback must be tested with the actual service user. This is a proposal for the
separate installer repository, not an implemented application integration.

## External blockers

NCPA and SMB need supported credential transport. Existing installer ownership
and directory permissions must support atomic resource replacement without
changing the installer contract in this repository. Record the deployed plugin
versions, resource metadata and process-list evidence on the available lab before
claiming acceptance. The current macro integration is not ready to deploy.
