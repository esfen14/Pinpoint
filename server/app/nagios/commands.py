"""
commands.py — The only place PinPoint writes to the Nagios external command pipe.

SECURITY: this is an injection-sensitive path (Engineering Standards "Sensitive
modules"). The allowlist is closed: one function per command, nothing builds a
command name from input. Every field is validated before a line is built, a line
is never longer than PIPE_BUF (so one write is atomic), and nothing is written
unless the host or service is in the latest snapshot.

Commands (https://assets.nagios.com/downloads/nagioscore/docs/externalcmds/):
    acknowledge_host_problem(host, comment, author)
    acknowledge_service_problem(host, service, comment, author)
    remove_host_acknowledgement(host)
    remove_service_acknowledgement(host, service)
    schedule_forced_host_check(host)
    schedule_forced_service_check(host, service)
    schedule_host_downtime(host, start, end, comment, author)
    schedule_service_downtime(host, service, start, end, comment, author)
    cancel_downtime_by_host_name(host, comment)
    send_custom_host_notification(host, comment)
    send_custom_service_notification(host, service, comment)

Acknowledgement type sent: NORMAL (sticky=1), matching AcknowledgementType.NORMACK
in history_models.py. Nagios removes a normal acknowledgement when the state
changes, which matches PinPoint's "problem has changed" behaviour. notify=0 (no
extra notification), persistent=1 (the comment stays visible in Nagios).

Custom notifications always use option 0: the force option is never set, so Nagios still
applies notification-enabled flags, scheduled downtime, timeperiods and escalations.

Each function returns a CommandResult and never raises, so a stopped Nagios cannot
fail or hang the web request: the pipe is opened non-blocking and writes give up
after WRITE_TIMEOUT_SECONDS.
"""
from __future__ import annotations

import errno
import os
import stat
import threading
import time
from dataclasses import dataclass

from flask import current_app

# Longest line written in one atomic pipe write (POSIX guarantees >= 512, Linux 4096).
MAX_LINE_BYTES = 4096
# Longest comment sent to Nagios. PinPoint keeps the full text in its own record.
MAX_COMMENT_CHARS = 255
MAX_NAME_CHARS = 255
WRITE_TIMEOUT_SECONDS = 2.0
# Never log more than this much of a comment.
LOG_COMMENT_CHARS = 40
# Custom notification options bitmask: 0 = no broadcast, no force, no increment (see module docstring).
CUSTOM_NOTIFICATION_OPTIONS = 0

NORMAL_ACK = 1
FORBIDDEN_CHARS = ("\n", "\r", "\0")

# Error codes in CommandResult.error
INVALID = "invalid"
UNKNOWN_TARGET = "unknown_target"
UNAVAILABLE = "unavailable"
TIMEOUT = "timeout"


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    error: str | None = None
    message: str = ""


def _ok() -> CommandResult:
    return CommandResult(True)


def _fail(code: str, message: str) -> CommandResult:
    return CommandResult(False, code, message)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def has_forbidden_chars(value: str) -> bool:
    """True when value holds a newline, carriage return or NUL."""
    return any(char in value for char in FORBIDDEN_CHARS)


def _check_name(label: str, value) -> str | None:
    """Return an error message when a host or service name is unsafe, else None."""
    if not isinstance(value, str) or not value.strip():
        return f"{label} is required."
    if has_forbidden_chars(value) or ";" in value:
        return f"{label} contains a character that is not allowed."
    if len(value) > MAX_NAME_CHARS:
        return f"{label} is too long."
    return None


def validate_comment(comment) -> str | None:
    """Return an error message when a comment cannot be sent to Nagios, else None."""
    if not isinstance(comment, str) or not comment.strip():
        return "comment is required and must not be blank."
    if has_forbidden_chars(comment):
        return "comment must not contain line breaks or NUL characters."
    return None


def _comment_failure(comment) -> CommandResult | None:
    message = validate_comment(comment)
    return _fail(INVALID, message) if message else None


def _wire_comment(comment: str) -> str:
    """The comment as sent: ';' becomes ',' (the field separator) and length is capped."""
    return comment.strip().replace(";", ",")[:MAX_COMMENT_CHARS]


def _wire_author(author) -> str:
    text = str(author or "PinPoint")
    for char in FORBIDDEN_CHARS:
        text = text.replace(char, " ")
    return text.replace(";", ",").strip()[:MAX_NAME_CHARS] or "PinPoint"


def known_targets() -> tuple[set[str], set[tuple[str, str]]]:
    """
    The hosts and (host, service) pairs in the latest snapshot. Load once per request
    and pass to the functions below, so a batch does not query once per command.
    """
    from app.api.system.statistics import get_latest_hosts, get_latest_services
    hosts = {row.Hostname for row in get_latest_hosts()}
    services = {(row.Hostname, row.Service) for row in get_latest_services()}
    return hosts, services


def _validate_target(hostname, service, targets) -> CommandResult | None:
    """Return a failure when the target is unsafe or not in the latest snapshot."""
    message = _check_name("hostname", hostname)
    if message is None and service is not None:
        message = _check_name("service_name", service)
    if message:
        return _fail(INVALID, message)
    hosts, services = targets if targets is not None else known_targets()
    if service is None:
        known = hostname in hosts
    else:
        known = (hostname, service) in services
    if not known:
        return _fail(UNKNOWN_TARGET, "Not in the latest Nagios status; no command was sent.")
    return None


# ---------------------------------------------------------------------------
# Pipe writing
# ---------------------------------------------------------------------------

def _write_line(line: str) -> CommandResult:
    """Write one command line to the Nagios command pipe without ever blocking."""
    data = (line + "\n").encode("utf-8")
    if len(data) > MAX_LINE_BYTES:
        return _fail(INVALID, "Command is too long.")

    path = current_app.config["NAGIOS_COMMAND_FILE"]
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return _fail(UNAVAILABLE, "The Nagios command pipe was not found.")
    if not stat.S_ISFIFO(mode):
        return _fail(UNAVAILABLE, "The Nagios command file is not a pipe.")

    try:
        # O_NONBLOCK: with no reader (Nagios stopped) this fails at once with ENXIO.
        fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
    except OSError as exc:
        if exc.errno == errno.ENXIO:
            return _fail(UNAVAILABLE, "Nagios is not reading its command pipe.")
        return _fail(UNAVAILABLE, "The Nagios command pipe could not be opened.")

    deadline = time.monotonic() + WRITE_TIMEOUT_SECONDS
    try:
        while True:
            try:
                os.write(fd, data)  # <= PIPE_BUF, so all or nothing
                return _ok()
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    return _fail(TIMEOUT, "The Nagios command pipe is full.")
                time.sleep(0.05)
            except OSError:
                return _fail(UNAVAILABLE, "The Nagios command pipe could not be written.")
    finally:
        os.close(fd)


def _send(name: str, args: list, log_target: str, log_comment: str | None = None) -> CommandResult:
    line = f"[{int(time.time())}] {name};" + ";".join(str(arg) for arg in args)
    result = _write_line(line)
    shown = f" comment={log_comment[:LOG_COMMENT_CHARS]!r}" if log_comment else ""
    if result.ok:
        current_app.logger.info("Nagios command %s sent for %s%s", name, log_target, shown)
    else:
        current_app.logger.warning(
            "Nagios command %s for %s failed (%s)", name, log_target, result.error
        )
    return result


def _target_label(hostname, service) -> str:
    return f"{hostname} / {service}" if service else str(hostname)


# ---------------------------------------------------------------------------
# Allowed commands
# ---------------------------------------------------------------------------

def acknowledge_host_problem(hostname, comment, author, targets=None) -> CommandResult:
    bad = _comment_failure(comment) or _validate_target(hostname, None, targets)
    if bad:
        return bad
    return _send(
        "ACKNOWLEDGE_HOST_PROBLEM",
        [hostname, NORMAL_ACK, 0, 1, _wire_author(author), _wire_comment(comment)],
        _target_label(hostname, None), comment,
    )


def acknowledge_service_problem(hostname, service, comment, author, targets=None) -> CommandResult:
    bad = _comment_failure(comment) or _validate_target(hostname, service, targets)
    if bad:
        return bad
    return _send(
        "ACKNOWLEDGE_SVC_PROBLEM",
        [hostname, service, NORMAL_ACK, 0, 1, _wire_author(author), _wire_comment(comment)],
        _target_label(hostname, service), comment,
    )


def remove_host_acknowledgement(hostname, targets=None) -> CommandResult:
    bad = _validate_target(hostname, None, targets)
    if bad:
        return bad
    return _send("REMOVE_HOST_ACKNOWLEDGEMENT", [hostname], _target_label(hostname, None))


def remove_service_acknowledgement(hostname, service, targets=None) -> CommandResult:
    bad = _validate_target(hostname, service, targets)
    if bad:
        return bad
    return _send(
        "REMOVE_SVC_ACKNOWLEDGEMENT", [hostname, service], _target_label(hostname, service)
    )


def schedule_forced_host_check(hostname, targets=None) -> CommandResult:
    bad = _validate_target(hostname, None, targets)
    if bad:
        return bad
    return _send(
        "SCHEDULE_FORCED_HOST_CHECK", [hostname, int(time.time())], _target_label(hostname, None)
    )


def schedule_forced_service_check(hostname, service, targets=None) -> CommandResult:
    bad = _validate_target(hostname, service, targets)
    if bad:
        return bad
    return _send(
        "SCHEDULE_FORCED_SVC_CHECK",
        [hostname, service, int(time.time())],
        _target_label(hostname, service),
    )


def _downtime_window_error(start, end) -> str | None:
    if not isinstance(start, int) or not isinstance(end, int) or isinstance(start, bool) \
            or isinstance(end, bool) or start <= 0 or end <= start:
        return "Downtime start and end must be epoch seconds with end after start."
    return None


def schedule_host_downtime(hostname, start, end, comment, author, targets=None) -> CommandResult:
    bad = _downtime_window_error(start, end)
    bad = (bad and _fail(INVALID, bad)) or _comment_failure(comment) or _validate_target(hostname, None, targets)
    if bad:
        return bad
    return _send(
        "SCHEDULE_HOST_DOWNTIME",
        [hostname, start, end, 1, 0, 0, _wire_author(author), _wire_comment(comment)],
        _target_label(hostname, None), comment,
    )


def schedule_service_downtime(hostname, service, start, end, comment, author, targets=None) -> CommandResult:
    bad = _downtime_window_error(start, end)
    bad = (bad and _fail(INVALID, bad)) or _comment_failure(comment) or _validate_target(hostname, service, targets)
    if bad:
        return bad
    return _send(
        "SCHEDULE_SVC_DOWNTIME",
        [hostname, service, start, end, 1, 0, 0, _wire_author(author), _wire_comment(comment)],
        _target_label(hostname, service), comment,
    )


def cancel_downtime_by_host_name(hostname, comment, targets=None) -> CommandResult:
    """
    Delete the host's and its services' downtime whose comment equals `comment`
    (DEL_DOWNTIME_BY_HOST_NAME;host;;;comment, checked on Nagios 4.5.11). The comment is
    required: with it blank Nagios would delete every downtime of the host.
    """
    bad = _comment_failure(comment) or _validate_target(hostname, None, targets)
    if bad:
        return bad
    return _send(
        "DEL_DOWNTIME_BY_HOST_NAME", [hostname, "", "", _wire_comment(comment)],
        _target_label(hostname, None), comment,
    )


def send_custom_host_notification(hostname, comment, targets=None, author="PinPoint") -> CommandResult:
    """
    Ask Nagios for a custom host notification (SEND_CUSTOM_HOST_NOTIFICATION). Never forced, so
    downtime, disabled notifications and timeperiods still apply. The comment must be fixed text
    built by the caller; it is never plugin or command output.
    """
    bad = _comment_failure(comment) or _validate_target(hostname, None, targets)
    if bad:
        return bad
    return _send(
        "SEND_CUSTOM_HOST_NOTIFICATION",
        [hostname, CUSTOM_NOTIFICATION_OPTIONS, _wire_author(author), _wire_comment(comment)],
        _target_label(hostname, None), comment,
    )


def send_custom_service_notification(hostname, service, comment, targets=None, author="PinPoint") -> CommandResult:
    """The service form of ``send_custom_host_notification`` (SEND_CUSTOM_SVC_NOTIFICATION)."""
    bad = _comment_failure(comment) or _validate_target(hostname, service, targets)
    if bad:
        return bad
    return _send(
        "SEND_CUSTOM_SVC_NOTIFICATION",
        [hostname, service, CUSTOM_NOTIFICATION_OPTIONS, _wire_author(author), _wire_comment(comment)],
        _target_label(hostname, service), comment,
    )


# ---------------------------------------------------------------------------
# Route helper
# ---------------------------------------------------------------------------

def sync_fields(user_id, results: list[CommandResult], what: str) -> dict:
    """
    Fold command results into the {"nagios_synced", "nagios_message"} fields added to
    acknowledge responses. A failure never undoes the local change: it is written to
    the audit log (its own commit) and reported in the message.
    """
    failed = [result for result in results if not result.ok]
    if not failed:
        return {"nagios_synced": True, "nagios_message": None}
    message = (
        f"Saved in PinPoint, but Nagios was not updated ({failed[0].message}) "
        "Notifications may continue."
    )
    from app import db
    from app.logging.user_activity import create_audit_log
    try:
        create_audit_log(user_id, f"Nagios sync failed for {what}: {failed[0].error}")
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not write the Nagios sync failure audit entry")
    return {"nagios_synced": False, "nagios_message": message}


def _author_name() -> str:
    from flask_login import current_user
    return f"{current_user.First_Name} {current_user.Last_Name}"


def acknowledge_target(hostname, service, comment, targets=None) -> CommandResult:
    """Acknowledge a host (service None) or service problem as the current user."""
    if service:
        return acknowledge_service_problem(hostname, service, comment, _author_name(), targets)
    return acknowledge_host_problem(hostname, comment, _author_name(), targets)


def sync_acknowledge(hostname, service, comment) -> dict:
    """Send one saved acknowledgement to Nagios and return the response fields."""
    from flask_login import current_user
    return sync_fields(
        current_user.UserID, [acknowledge_target(hostname, service, comment)],
        f"acknowledge {_target_label(hostname, service)}",
    )


def sync_unacknowledge(hostname, service) -> dict:
    """Remove one acknowledgement in Nagios and return the response fields."""
    from flask_login import current_user
    if service:
        result = remove_service_acknowledgement(hostname, service)
    else:
        result = remove_host_acknowledgement(hostname)
    return sync_fields(
        current_user.UserID, [result], f"unacknowledge {_target_label(hostname, service)}"
    )


# ---------------------------------------------------------------------------
# Check Now (forced re-check) helpers
# ---------------------------------------------------------------------------

RECHECK_INTERVAL_SECONDS = 10
_recheck_times: dict[tuple, float] = {}
_recheck_lock = threading.Lock()


def recheck_refusal(hostname, service=None):
    """
    Return (status, message) when a re-check must be refused, else None: 409 for a
    paused, retired or merged device, 404 for a name not in the latest snapshot.
    """
    from app.network_discovery.device_identity import (
        UNCHECKED_STATES, devices_by_host_name, monitoring_state,
    )
    device = devices_by_host_name([hostname]).get(hostname)
    if device is not None and monitoring_state(device) in UNCHECKED_STATES:
        return 409, f"Host '{hostname}' is {monitoring_state(device)}; Nagios is not checking it."
    hosts, services = known_targets()
    known = (hostname, service) in services if service else hostname in hosts
    if not known:
        return 404, "Not found in the latest Nagios status."
    return None


def claim_recheck(hostname, service=None) -> int:
    """
    Reserve the per-target slot. Returns 0 when the caller may send, otherwise the
    seconds to wait. Call release_recheck() if the command then fails.
    """
    key = (hostname, service)
    now = time.monotonic()
    with _recheck_lock:
        last = _recheck_times.get(key)
        if last is not None and now - last < RECHECK_INTERVAL_SECONDS:
            return max(1, int(RECHECK_INTERVAL_SECONDS - (now - last) + 0.999))
        if len(_recheck_times) > 1000:
            for old in [k for k, t in _recheck_times.items() if now - t >= RECHECK_INTERVAL_SECONDS]:
                del _recheck_times[old]
        _recheck_times[key] = now
    return 0


def release_recheck(hostname, service=None) -> None:
    with _recheck_lock:
        _recheck_times.pop((hostname, service), None)
