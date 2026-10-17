# Issue #182 remote restart security review

Source review: 2026-10-17, Codex agent. This is a source and regression review;
human reviewer approval and live target evidence are separate merge gates.
Accepted privilege design: [Part 8.3 design note](Issue_8_3_Remote_Restart_Design_Note.md).

| Surface | Finding and control | Regression evidence |
|---|---|---|
| Request parameters | Only `unit` is accepted for an action; host comes from the event's known device. Strict ASCII unit grammar prevents options, paths, whitespace and shell metacharacters. Settings lists are validated, deduplicated and capped at 20. | `test_remote_restart.py` parameter and settings cases |
| SSH pinning | The initial fingerprint check alone was insufficient: the second transport's key was added to known hosts without comparison. Added comparison with the stored fingerprint before accepting that key; final SSHClient uses RejectPolicy and that exact key. | `test_ssh_port.py::test_key_changed_between_probe_and_connection_is_not_trusted`; nondefault port cases |
| Connection bounds | Explicit socket connection timeout and SSH banner/authentication bounds; transports close in finally. | SSH port tests assert bounded socket creation |
| Remote command | Fixed `sudo -n /usr/local/sbin/pinpoint-service-restart` plus one validated, quoted unit. No request-derived executable or host argument. | Command construction and hostile unit cases in `test_remote_restart.py` |
| Command deadline | Paramiko's `recv_exit_status()` does not honor the channel I/O timeout. Replaced unbounded waiting with monotonic deadline polling; output is drained and discarded so SSH flow control cannot hang a verbose restart. The client closes on timeout. A submitted systemd job may outlive SSH closure. | `test_remote_restart.py::test_remote_exit_status_wait_has_an_actual_deadline` |
| Helper privileges | Root-owned helper executes fixed `/usr/bin/systemctl restart -- "$UNIT"`; exactly one argument, strict grammar and exact on-device allowlist membership. List must be a regular nonsymlink root-owned file, not writable by group/others. | Bash helper negative/positive cases; live ownership/sudo validation pending |
| Bootstrap paths | Fixed root directories/files; reject a symlink allowlist directory, establish root ownership and 755 mode before writing. Remove a preexisting temporary list entry before creating it in the secured directory. Helper is 755, list 644, sudoers 440; validate sudoers before replacing it. | Helper-install regression asserts directory ownership and no symlink; live install pending |
| Secret exposure | Administrator password goes through stdin during bootstrap/cleanup; deployment key path goes to Paramiko, never a remote command. Bootstrap suppresses device stdout/stderr. Restart discards device output; responses and run messages use fixed text/validated unit/exit code, never raw exceptions or key material. | Install suppression, failed authentication/exception and cleanup log secrecy cases |
| Authorization/lifecycle | Settings and cleanup require `system.deploy.ncpa`; action changes require `remediation.manage`. Runtime refuses non-Active, paused, untrusted, disabled and off-list devices plus Maintenance Mode/cooldown/hourly cap. Cleanup on deployed devices is explicitly owner-approved and clears installation trust until redeployment. | API permission, lookup and cleanup regressions |
| Run history | Nullable `ON DELETE SET NULL` foreign key and transactional detachment retain snapshots without transferring deleted-action limits to a replacement. Upgrade detaches orphan links; existing ID reuse cannot be reconstructed retroactively. | API reuse/rollback and populated multi-bind migration tests |

No added dependency. No unrestricted sudo or arbitrary command action. The
on-device list is a limit on the deployment account, not a limit on a device
administrator with root access. Human approval must assess the accepted extra
privilege and review the real target results before merging.
