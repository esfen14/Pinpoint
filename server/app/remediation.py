"""
Remediation consumer: turns spool files left by the Nagios event handler into recorded decisions.

The handler (scripts/pinpoint_event_handler.py) writes one small JSON file per state change to a
spool folder. A scheduler job calls ``process_spool`` every few seconds. Everything in a spool
file is untrusted: the file must be a regular file of the expected size owned by the trusted
user, and its content is parsed strictly. For each valid HARD problem event (a SOFT state or a
recovery to OK or UP is ignored) the consumer finds the
enabled actions that cover it, applies the safety controls (kill switch, Maintenance Mode,
scheduled downtime, an acknowledged problem) and then the cooldown and hourly cap, writes one
RemediationRun row per action (a skip is a row with its reason, never silent), and only then runs
the action type from app/remediation_actions.py.

Order for one event (so a crash can never run an action twice):
    1. save the run rows (``running`` or ``skipped_*``) and commit
    2. delete the spool file
    3. run each ``running`` action and update its row

``mark_interrupted`` turns rows left ``running`` by a stop into ``interrupted`` at startup; they
are never run again. Discarded files are written to the application log by reason only, never
with their content.
"""
import hashlib
import json
import os
import re
import stat
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from flask import current_app

from app import db
from app.history_models import AcknowledgementType, HostStatus, ServiceStatus
from app.remediation_actions import RunContext, run_action
from app.system_models import (
    RemediationAction, RemediationConsumerState, RemediationEventState, RemediationEventStateType,
    RemediationOutcome, RemediationRun, RemediationScope, SystemSettings,
)

MAX_FILES_PER_RUN = 200
# A spool longer than this is a flood or a stalled consumer: the oldest files are dropped (and
# counted). Event files nobody handled for SPOOL_MAX_AGE_DAYS are removed by the daily purge.
SPOOL_CAP = 1000
SPOOL_MAX_AGE_DAYS = 7
MAX_FILE_BYTES = 2048
MAX_HOST_LENGTH = 100
MAX_SERVICE_LENGTH = 150
MAX_ATTEMPT = 100
MAX_LAST_CHANGE = 10**12
MAX_OUTPUT_CHARS = 1024

SPOOL_NAME_RE = re.compile(r"[0-9]{10,25}-[0-9]+\.json", re.ASCII)
NAME_RE = re.compile(r"[A-Za-z0-9 ._:/-]+", re.ASCII)
SECRET_RE = re.compile(
    r"\b(pass(?:word|wd)?|secret|token|api[_-]?key|key|community|auth\w*)\b\s*[=:]\s*\S+", re.IGNORECASE)

EVENT_KEYS = {"v", "kind", "host", "service", "state", "state_type", "attempt", "last_change"}
# A HARD recovery is not a failure: actions react to problems, never to the return to OK or UP.
RECOVERY_STATES = {"OK", "UP"}
HOST_STATES = {"UP", "DOWN", "UNREACHABLE"}
SERVICE_STATES = {"OK", "WARNING", "CRITICAL", "UNKNOWN"}

# Outcomes that mean the action was started, so they count toward cooldown and the hourly cap.
EXECUTED = (
    RemediationOutcome.RUNNING, RemediationOutcome.SUCCEEDED, RemediationOutcome.FAILED,
    RemediationOutcome.TIMED_OUT, RemediationOutcome.INTERRUPTED,
)
RESULT_OUTCOMES = {
    "succeeded": RemediationOutcome.SUCCEEDED,
    "failed": RemediationOutcome.FAILED,
    "timed_out": RemediationOutcome.TIMED_OUT,
}


# ==========================================================
# TRUST AND PARSING
# ==========================================================

def trusted_uid():
    """Return the user id whose spool files are trusted, or None when it cannot be determined."""
    try:
        import pwd
        return pwd.getpwnam(current_app.config["REMEDIATION_SPOOL_OWNER"]).pw_uid
    except (ImportError, KeyError):
        return None


def valid_name(value, max_length):
    """True when value is a host or service name the handler would also accept."""
    return (
        isinstance(value, str) and 0 < len(value) <= max_length
        and NAME_RE.fullmatch(value) is not None and ".." not in value
    )


def is_int(value):
    """True for a real integer (a JSON true or false is not one)."""
    return isinstance(value, int) and not isinstance(value, bool)


def parse_event(data):
    """Parse spool bytes strictly. Returns the event dict, or None when anything is off."""
    try:
        event = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(event, dict) or set(event) != EVENT_KEYS or event["v"] != 1 or not is_int(event["v"]):
        return None
    kind = event["kind"]
    if kind not in ("host", "service"):
        return None
    if event["state"] not in (SERVICE_STATES if kind == "service" else HOST_STATES):
        return None
    if event["state_type"] not in ("SOFT", "HARD"):
        return None
    if not valid_name(event["host"], MAX_HOST_LENGTH):
        return None
    if kind == "service":
        if not valid_name(event["service"], MAX_SERVICE_LENGTH):
            return None
    elif event["service"] is not None:
        return None
    if not is_int(event["attempt"]) or not 1 <= event["attempt"] <= MAX_ATTEMPT:
        return None
    if not is_int(event["last_change"]) or not 1 <= event["last_change"] <= MAX_LAST_CHANGE:
        return None
    return event


def read_spool_file(path, uid):
    """
    Read one spool file if it is safe to. Returns the raw bytes, or None to discard it: not a
    regular file (symlinks are never followed), too large, or not owned by the trusted user.
    """
    if uid is None:
        return None
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES or info.st_uid != uid:
        return None
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_uid != uid:
            return None
        data = handle.read(MAX_FILE_BYTES + 1)
    return None if len(data) > MAX_FILE_BYTES else data


def remove(path):
    """Delete a spool entry (never following a symlink); a failure is ignored."""
    try:
        if os.path.isdir(path) and not os.path.islink(path):
            os.rmdir(path)
        else:
            os.unlink(path)
    except OSError:
        pass


def get_state():
    """Return the one consumer-state row (Id 1), creating it when missing. The caller commits."""
    state = db.session.get(RemediationConsumerState, 1)
    if state is None:
        state = RemediationConsumerState(Id=1, Dropped_Count=0)
        db.session.add(state)
    return state


def drop_over_cap(spool_dir, names):
    """
    Delete the oldest files when more than SPOOL_CAP are waiting, and record how many went in
    the consumer state and the log. ``names`` is sorted oldest first; returns the names kept.
    """
    excess = len(names) - SPOOL_CAP
    if excess <= 0:
        return names
    dropped = 0
    for name in names[:excess]:
        path = os.path.join(spool_dir, name)
        remove(path)
        if not os.path.lexists(path):
            dropped += 1
    state = get_state()
    state.Dropped_Count = (state.Dropped_Count or 0) + dropped
    state.Dropped_At = datetime.now(timezone.utc)
    db.session.commit()
    current_app.logger.warning("Remediation: the spool held more than %d files; dropped the %d oldest", SPOOL_CAP, dropped)
    return names[excess:]


def purge_old_spool_files(spool_dir=None, now=None):
    """
    Remove event files in the spool older than SPOOL_MAX_AGE_DAYS (stuck or unreadable ones; a
    handled file is already gone). Other names are left alone. Returns the number removed.
    """
    spool_dir = spool_dir or current_app.config["REMEDIATION_SPOOL_DIR"]
    cutoff = (now or datetime.now(timezone.utc)).timestamp() - SPOOL_MAX_AGE_DAYS * 86400
    removed = 0
    try:
        names = [name for name in os.listdir(spool_dir) if SPOOL_NAME_RE.fullmatch(name)]
    except OSError:
        return removed
    for name in names:
        path = os.path.join(spool_dir, name)
        try:
            if os.lstat(path).st_mtime >= cutoff:
                continue
        except OSError:
            continue
        remove(path)
        if not os.path.lexists(path):
            removed += 1
    if removed:
        current_app.logger.info("Remediation: removed %d spool files older than %d days", removed, SPOOL_MAX_AGE_DAYS)
    return removed


# ==========================================================
# DECISIONS
# ==========================================================

def event_key(event):
    """Stable id of one event, so a replayed file cannot run an action twice."""
    text = "|".join([event["kind"], event["host"], event["service"] or "", event["state"], str(event["last_change"])])
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pattern_matches(pattern, value):
    """True when value equals pattern, where ``*`` matches any run of characters. No regex."""
    if not pattern:
        return False
    regex = ".*".join(re.escape(part) for part in pattern.split("*"))
    return re.fullmatch(regex, value) is not None


def covers(action, event):
    """True when the action's scope and patterns cover this event."""
    if action.Scope_Kind.value != event["kind"]:
        return False
    if not pattern_matches(action.Host_Pattern, event["host"]):
        return False
    if action.Scope_Kind == RemediationScope.SERVICE:
        return pattern_matches(action.Service_Pattern, event["service"])
    return True


def safety_state(event):
    """
    Return (in_downtime, acknowledged) for the object an event is about, from its newest Nagios
    status snapshot. An object with no snapshot is neither.
    """
    if event["kind"] == "service":
        newest = db.session.scalars(sa.select(ServiceStatus).where(
            ServiceStatus.Hostname == event["host"], ServiceStatus.Service == event["service"],
        ).order_by(ServiceStatus.Timestamp.desc(), ServiceStatus.ServiceStatusID.desc()).limit(1)).first()
    else:
        newest = db.session.scalars(sa.select(HostStatus).where(
            HostStatus.Hostname == event["host"],
        ).order_by(HostStatus.Timestamp.desc(), HostStatus.HostStatusID.desc()).limit(1)).first()
    if newest is None:
        return False, False
    return (
        (newest.Scheduled_Downtime_Depth or 0) > 0,
        newest.Acknowledgement_Type != AcknowledgementType.NOACK,
    )


def safety_skip(action, settings, state):
    """
    Return (outcome, reason) when a safety control stops this action, else None. Order: the kill
    switch, Maintenance Mode, scheduled downtime, an acknowledged problem. ``state`` is the
    (in_downtime, acknowledged) pair from ``safety_state``.
    """
    if settings is not None and settings.Remediation_Enabled is False:
        return (RemediationOutcome.SKIPPED_KILL_SWITCH,
                "Automatic recovery is switched off (kill switch).")
    if settings is not None and settings.Maintenance_Mode:
        return (RemediationOutcome.SKIPPED_MAINTENANCE, "Maintenance Mode is on.")
    in_downtime, acknowledged = state
    if in_downtime:
        return (RemediationOutcome.SKIPPED_DOWNTIME, "The problem is in scheduled downtime.")
    if acknowledged and not action.Run_When_Acknowledged:
        return (RemediationOutcome.SKIPPED_ACKNOWLEDGED,
                "An operator has already acknowledged this problem.")
    return None


def skip_reason(action, event, now):
    """Return (outcome, reason) when the cooldown or hourly cap stops this run, else None."""
    cooldown_start = now - timedelta(seconds=action.Cooldown_Seconds)
    recent = db.session.scalar(sa.select(sa.func.count()).select_from(RemediationRun).where(
        RemediationRun.Action_Id == action.Id,
        RemediationRun.Hostname == event["host"],
        RemediationRun.Service == event["service"],
        RemediationRun.Outcome.in_(EXECUTED),
        RemediationRun.Received_At >= cooldown_start,
    ))
    if recent:
        return (RemediationOutcome.SKIPPED_COOLDOWN,
                f"Within the {action.Cooldown_Seconds} second cooldown since the last run for this host and service.")
    in_last_hour = db.session.scalar(sa.select(sa.func.count()).select_from(RemediationRun).where(
        RemediationRun.Action_Id == action.Id,
        RemediationRun.Outcome.in_(EXECUTED),
        RemediationRun.Received_At >= now - timedelta(hours=1),
    ))
    if in_last_hour >= action.Max_Runs_Per_Hour:
        return (RemediationOutcome.SKIPPED_HOURLY_CAP,
                f"Reached the limit of {action.Max_Runs_Per_Hour} runs per hour for this action.")
    return None


def clean_output(text):
    """Redact secret-like pairs, then cap the length. Output only ever comes from fixed code."""
    return SECRET_RE.sub(lambda m: m.group(1) + "=***", str(text))[:MAX_OUTPUT_CHARS]


# ==========================================================
# PROCESSING
# ==========================================================

def record_decisions(event, now):
    """
    Save one run row per enabled action covering the event (``running`` or a ``skipped_*``) and
    commit. Returns the actions to run as (run_id, action_id, name, type, parameters). An action
    that already has a row for this event (a replay) is left alone.
    """
    key = event_key(event)
    to_run = []
    actions = db.session.scalars(sa.select(RemediationAction).where(RemediationAction.Enabled.is_(True))).all()
    # Read on every event, so a change to the kill switch applies on the next tick.
    settings = db.session.get(SystemSettings, 1)
    state = None
    for action in actions:
        if not covers(action, event):
            continue
        already = db.session.scalar(sa.select(RemediationRun.Id).where(
            RemediationRun.Event_Key == key, RemediationRun.Action_Id == action.Id))
        if already is not None:
            current_app.logger.info("Remediation: replayed event ignored for action %r", action.Name)
            continue
        if state is None:
            state = safety_state(event)
        skipped = safety_skip(action, settings, state) or skip_reason(action, event, now)
        row = RemediationRun(
            Event_Key=key, Action_Id=action.Id, Action_Name=action.Name, Hostname=event["host"],
            Service=event["service"], State=RemediationEventState(event["state"]),
            State_Type=RemediationEventStateType(event["state_type"]), Attempt=event["attempt"],
            Received_At=now,
            Outcome=skipped[0] if skipped else RemediationOutcome.RUNNING,
            Reason=skipped[1] if skipped else None,
        )
        db.session.add(row)
        db.session.flush()
        if not skipped:
            to_run.append((row.Id, action.Id, action.Name, action.Action_Type.value, dict(action.Parameters or {})))
    db.session.commit()
    return to_run


def execute(run_id, name, action_type, parameters, event):
    """Run one action and write its outcome to the row; logs one line with no output or parameters."""
    row = db.session.get(RemediationRun, run_id)
    row.Started_At = datetime.now(timezone.utc)
    db.session.commit()
    settings = db.session.get(SystemSettings, 1)
    context = RunContext(
        hostname=event["host"], service=event["service"], state=event["state"],
        maintenance_mode=bool(settings and settings.Maintenance_Mode))
    result = run_action(action_type, parameters, context)
    row = db.session.get(RemediationRun, run_id)
    row.Outcome = RESULT_OUTCOMES.get(result.outcome, RemediationOutcome.FAILED)
    row.Output = clean_output(result.output)
    row.Finished_At = datetime.now(timezone.utc)
    db.session.commit()
    current_app.logger.info(
        "Remediation: action %r %s for %s%s", name, row.Outcome.value, event["host"],
        f" / {event['service']}" if event["service"] else "")


def handle_file(path, uid, summary):
    """Handle one spool file end to end; see the module docstring for the order."""
    data = read_spool_file(path, uid)
    event = parse_event(data) if data is not None else None
    if event is None:
        current_app.logger.warning("Remediation: discarded a spool file (not trusted or not a valid event)")
        remove(path)
        summary["discarded"] += 1
        return
    summary["processed"] += 1
    if event["state_type"] != "HARD" or event["state"] in RECOVERY_STATES:
        remove(path)
        return
    to_run = record_decisions(event, datetime.now(timezone.utc))
    remove(path)
    for run_id, _action_id, name, action_type, parameters in to_run:
        execute(run_id, name, action_type, parameters, event)
        summary["runs"] += 1


def process_spool(spool_dir=None):
    """
    Handle up to MAX_FILES_PER_RUN spool files, oldest first. Never raises: a failure on one
    file is logged and rolled back, and the next file is still handled. Returns counts
    (processed, discarded, runs).
    """
    spool_dir = spool_dir or current_app.config["REMEDIATION_SPOOL_DIR"]
    summary = {"processed": 0, "discarded": 0, "runs": 0}
    try:
        names = sorted(name for name in os.listdir(spool_dir) if SPOOL_NAME_RE.fullmatch(name))
    except OSError:
        return summary
    uid = trusted_uid()
    try:
        names = drop_over_cap(spool_dir, names)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Remediation: could not apply the spool cap")
    for name in names[:MAX_FILES_PER_RUN]:
        try:
            handle_file(os.path.join(spool_dir, name), uid, summary)
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Remediation: could not handle a spool file")
    return summary


def mark_interrupted():
    """At startup, turn rows left ``running`` into ``interrupted``. They are never run again. Returns the count."""
    result = db.session.execute(
        sa.update(RemediationRun).where(RemediationRun.Outcome == RemediationOutcome.RUNNING).values(
            Outcome=RemediationOutcome.INTERRUPTED, Finished_At=datetime.now(timezone.utc),
            Reason="PinPoint stopped while this action was running."))
    db.session.commit()
    return result.rowcount
