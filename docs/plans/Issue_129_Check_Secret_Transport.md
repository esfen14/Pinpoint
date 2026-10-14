# Issue #129: check secret transport

Status: supported credential transport implemented and main NCPA engine acceptance passed; owner chose process secrecy with explicit unsupported-plugin refusal on 2026-10-14.

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
| `check_ncpa.py` | Upstream 1.2.5 accepts the token through `-t`/`--token`; its option parser has no credential file/stdin option. | Implemented unprivileged in-process adapter for inspected 1.2.4/1.2.5 clients; bare slot identifiers in generated services. Automated process tests and installed 1.2.4 mocked parity pass. Four real web01 metrics matched stock OK results and performance series as nagios with token-free argv. Full generated-config main Nagios CPU/memory/root-disk checks, argv secrecy and snapshots passed on c9f8e263. |
| `check_nt`, `check_radius`, `check_mysql_query` | Native C plugins may support compiled-in `--extra-opts`, which reads named INI sections. | Implemented extra-options stdin adapter with a runtime help capability check. Required/optional password arguments become bare slot identifiers. Parent/child process tests pass; installed check_nt accepted synthetic stdin authentication and returned expected uptime/performance data. Radius is absent from the current appliance; remaining live parity is pending. |
| `check_disk_smb` | The 2.4.12 Perl script accepts a password argument and passes it to a child `smbclient` command. Its SMB configuration flag is not a password-file input. | Password-bearing config generation is explicitly refused before publication. No silent dropping, pausing or insecure fallback; secure parent/child input remains an external blocker. |

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
   is proven by installed helper tests; do not grant broad chown or directory-write access here.
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
The NCPA and native adapters now implement credential transport using protected resource reads and in-memory/stdin inputs. Tests preserve public arguments and inspect actual running process argv. Installed generated NCPA services passed main Nagios checks; native endpoint parity remains limited to the installed synthetic check_nt run and automated adapter tests.

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
rollback must be tested with the actual service user. A helper and installer packaging/sudoers changes now exist locally on the separate
installer branch `issue-129-resource-helper`; seven isolated tests and shell syntax
checks pass. Application writes and rollback now invoke it for the foreign-owned
default resource path. It is installed on the QA appliance with an exact no-argument
sudo grant; service-user writes, outside-byte/metadata preservation, validation,
rollback and rejected arbitrary path/argument/command probes passed. The new
application integration is published in [app PR #161](https://github.com/esfen14/Pinpoint/pull/161), and the installer branch is published in [draft PR #7](https://github.com/lorraine-pangilinan/PinPoint-Installer/pull/7).

## External blockers

SMB still needs supported child credential transport. NCPA uses the in-process adapter; unsupported client versions fail safely. The paired installer extension is required for default-path ownership-preserving
updates. Full generated-config apply/reload, live 0640/readability, main NCPA results, argv/snapshot/log secrecy and actual-binary validation rollback passed; see [the main-daemon report](../test-runs/2026-10-15-issue-129-main-daemon/REPORT.md). Mandatory live port/cleanup journeys also pass in [the finish-journeys report](../test-runs/2026-10-15-issue-129-finish-journeys/REPORT.md). The complete issue remains draft for new evidence publication/current-head CI and paired human approvals. No production or ISO-build sign-off is implied.
