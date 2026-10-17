"""
Operator notification for automatic recovery (#153).

When a recovery run fails or times out, is stopped by its cooldown or hourly cap, or the same
action keeps succeeding for the same object, PinPoint asks Nagios for one custom notification
through the command channel (app/nagios/commands.py). Nagios, not PinPoint, decides who is told:
contacts, timeperiods, downtime and escalations all apply because the force option is never set.
There is no recipient list and no second mail path here.

The comment is built from fixed text, the action name (reduced to a safe character set), the
outcome code and the run id. Plugin output, command output and anything else a host controls
never reach it.

State lives on the run (``Notify_Kind``, ``Notify_State``, ``Notify_Attempts``, ``Notify_Error``,
``Notify_At``), so it survives a restart and a run is notified at most once:

    1. the consumer marks the run ``pending`` in the same commit that records its outcome
    2. ``deliver`` counts the attempt and commits it, sends, then commits the result
    3. a failed send keeps the run ``pending`` with a fixed error until ``MAX_ATTEMPTS`` is
       reached, then ``failed``
    4. ``fail_unfinished`` (at startup) fails a run whose attempt never saved a result; it is
       never sent again, the same rule the consumer uses for interrupted actions

Nothing here raises: a missing or unwritable command file is recorded on the run and the
consumer carries on.
"""
import re
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from flask import current_app

from app import db
from app.nagios import commands
from app.system_models import RemediationNotifyState, RemediationOutcome, RemediationRun, SystemSettings

KINDS = ("failed", "capped", "repeated")
MAX_ATTEMPTS = 3
# At most this many pending notifications are handled per consumer tick.
BATCH_SIZE = 50
MAX_NAME_CHARS = 40
# How far apart (in seconds) the archive's time and the time PinPoint wrote the command may be.
MATCH_WINDOW_SECONDS = 120
DEFAULT_REPEAT_COUNT = 3
DEFAULT_REPEAT_WINDOW_HOURS = 24
STOPPED_ERROR = "PinPoint stopped while sending the notification."
UNEXPECTED_ERROR = "The notification could not be sent."

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9 ._:/-]")
DOT_RUN_RE = re.compile(r"\.{2,}")

OUTCOME_KINDS = {
    RemediationOutcome.FAILED: "failed",
    RemediationOutcome.TIMED_OUT: "failed",
    RemediationOutcome.SKIPPED_COOLDOWN: "capped",
    RemediationOutcome.SKIPPED_HOURLY_CAP: "capped",
}


# ==========================================================
# DECISIONS
# ==========================================================

def kind_for_outcome(outcome):
    """The notification kind a run outcome calls for, or None. Deliberate skips never notify."""
    return OUTCOME_KINDS.get(outcome)


def wants(notify_on, kind):
    """True when the action's Notify_On list includes this kind."""
    return isinstance(notify_on, (list, tuple)) and kind in notify_on


def mark_for_notification(run, kind, notify_on):
    """
    Mark a run as owing the operator a notification when the action asks for this kind. Sets the
    fields only; the caller commits. Returns True when the run was marked.
    """
    if kind not in KINDS or not wants(notify_on, kind):
        return False
    run.Notify_Kind = kind
    run.Notify_State = RemediationNotifyState.PENDING
    run.Notify_Attempts = 0
    run.Notify_Error = None
    return True


def repeat_settings():
    """The repeat count and window in hours from the settings row (defaults when it is missing)."""
    settings = db.session.get(SystemSettings, 1)
    if settings is None:
        return DEFAULT_REPEAT_COUNT, DEFAULT_REPEAT_WINDOW_HOURS
    return (
        settings.Remediation_Repeat_Count or DEFAULT_REPEAT_COUNT,
        settings.Remediation_Repeat_Window_Hours or DEFAULT_REPEAT_WINDOW_HOURS,
    )


def check_repeat(run, notify_on, count, window_hours, now):
    """
    After a successful run, mark it for a "repeated" notification when the same action has now
    succeeded ``count`` times for the same host and service inside the window and no repeat
    notification went out inside the window. Sets fields only; the caller commits.
    """
    if run.Outcome != RemediationOutcome.SUCCEEDED or run.Action_Id is None or not wants(notify_on, "repeated"):
        return False
    since = now - timedelta(hours=window_hours)
    same = (
        RemediationRun.Action_Id == run.Action_Id,
        RemediationRun.Hostname == run.Hostname,
        RemediationRun.Service == run.Service,
        RemediationRun.Received_At >= since,
    )
    successes = db.session.scalar(sa.select(sa.func.count()).select_from(RemediationRun).where(
        *same, RemediationRun.Outcome == RemediationOutcome.SUCCEEDED))
    if (successes or 0) < count:
        return False
    already = db.session.scalar(sa.select(sa.func.count()).select_from(RemediationRun).where(
        *same, RemediationRun.Notify_Kind == "repeated"))
    if already:
        return False
    return mark_for_notification(run, "repeated", notify_on)


# ==========================================================
# COMMENT
# ==========================================================

def safe_text(value, max_chars=MAX_NAME_CHARS):
    """Reduce text to letters, digits and . _ : / - and space; anything else becomes ?. Never raises."""
    text = SAFE_NAME_RE.sub("?", str(value))
    return DOT_RUN_RE.sub(".", text)[:max_chars]


def build_comment(kind, action_name, outcome_code, run_id):
    """
    The comment Nagios shows with the notification: fixed text plus the action name, the outcome
    code and the run id. Plain ASCII without ; $ quotes, backticks, pipes or line breaks, and no
    longer than the command channel allows.
    """
    name = safe_text(action_name)
    code = safe_text(outcome_code, 20)
    run = int(run_id)
    if kind == "capped":
        text = f"PinPoint automatic recovery was stopped by its limits: action {name} did not run ({code}, run {run})."
    elif kind == "repeated":
        text = (f"PinPoint recovered this automatically several times and the fault persists: "
                f"action {name} (run {run}).")
    else:
        text = f"PinPoint automatic recovery did not succeed: action {name} ended {code} (run {run})."
    return text[:commands.MAX_COMMENT_CHARS]


# ==========================================================
# FEED
# ==========================================================

def attach_comments(items, service_key):
    """
    Give each custom notification in a feed its comment text. Nagios does not keep the comment in
    the archive, so the text is rebuilt from the run that sent the notification: same host and
    service, a notification that was sent, and the send time within MATCH_WINDOW_SECONDS of the
    item's ``timestamp`` (the nearest run wins). Only items with ``is_custom`` set are touched;
    they always get a ``comment`` key (None when no run matches, for example a notification
    someone sent by hand). ``service_key`` names the item key that holds the service. Never
    raises: a database problem leaves every comment None. Returns the same list.
    """
    custom = [item for item in items if item.get("is_custom")]
    if not custom:
        return items
    for item in custom:
        item["comment"] = None
    try:
        stamps = [int(item.get("timestamp") or 0) for item in custom]
        low = datetime.fromtimestamp(min(stamps) - MATCH_WINDOW_SECONDS, timezone.utc)
        high = datetime.fromtimestamp(max(stamps) + MATCH_WINDOW_SECONDS, timezone.utc)
        runs = db.session.scalars(sa.select(RemediationRun).where(
            RemediationRun.Notify_State == RemediationNotifyState.SENT,
            RemediationRun.Notify_At >= low, RemediationRun.Notify_At <= high,
        ).limit(500)).all()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Remediation: could not match custom notifications to runs")
        return items
    for item in custom:
        stamp = int(item.get("timestamp") or 0)
        best, best_gap = None, MATCH_WINDOW_SECONDS + 1
        for run in runs:
            if run.Hostname != item.get("hostname") or run.Service != (item.get(service_key) or None):
                continue
            moment = run.Notify_At if run.Notify_At.tzinfo else run.Notify_At.replace(tzinfo=timezone.utc)
            gap = abs(int(moment.timestamp()) - stamp)
            if gap < best_gap:
                best, best_gap = run, gap
        if best is not None:
            outcome = best.Outcome.value if best.Outcome is not None else "unknown"
            item["comment"] = build_comment(best.Notify_Kind, best.Action_Name, outcome, best.Id)
    return items


# ==========================================================
# DELIVERY
# ==========================================================

def send_for(run):
    """Send the notification for one run through the command channel and return its CommandResult."""
    outcome = run.Outcome.value if run.Outcome is not None else "unknown"
    comment = build_comment(run.Notify_Kind, run.Action_Name, outcome, run.Id)
    if run.Service:
        return commands.send_custom_service_notification(run.Hostname, run.Service, comment)
    return commands.send_custom_host_notification(run.Hostname, comment)


def deliver(run_id):
    """
    Try once to notify for one run. Does nothing unless the run is ``pending``. The attempt is
    counted and committed before sending, so a stop mid-send is never sent again. A failure is
    recorded as a fixed message; after MAX_ATTEMPTS the run becomes ``failed``. Never raises.
    """
    try:
        row = db.session.get(RemediationRun, run_id)
        if row is None or row.Notify_State != RemediationNotifyState.PENDING:
            return
        row.Notify_Attempts = (row.Notify_Attempts or 0) + 1
        row.Notify_Error = None
        db.session.commit()
        try:
            result = send_for(row)
            ok, message = result.ok, (result.message or UNEXPECTED_ERROR)
        except Exception as exc:
            current_app.logger.warning("Remediation: notification for run %s raised %s", run_id, type(exc).__name__)
            ok, message = False, UNEXPECTED_ERROR
        row = db.session.get(RemediationRun, run_id)
        if ok:
            row.Notify_State = RemediationNotifyState.SENT
            row.Notify_At = datetime.now(timezone.utc)
        else:
            row.Notify_Error = message[:200]
            if row.Notify_Attempts >= MAX_ATTEMPTS:
                row.Notify_State = RemediationNotifyState.FAILED
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Remediation: could not record a notification result")


def deliver_pending():
    """
    Deliver every pending notification that has not been tried yet or whose last try failed and
    has attempts left. At most BATCH_SIZE per call. Returns how many were attempted.
    """
    try:
        ids = db.session.scalars(sa.select(RemediationRun.Id).where(
            RemediationRun.Notify_State == RemediationNotifyState.PENDING,
            sa.or_(
                RemediationRun.Notify_Attempts == 0,
                sa.and_(RemediationRun.Notify_Error.is_not(None), RemediationRun.Notify_Attempts < MAX_ATTEMPTS),
            ),
        ).order_by(RemediationRun.Id).limit(BATCH_SIZE)).all()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Remediation: could not list pending notifications")
        return 0
    for run_id in ids:
        deliver(run_id)
    return len(ids)


def fail_unfinished():
    """
    At startup, fail notifications whose attempt started but never saved a result. They are never
    sent again. Returns the count.
    """
    result = db.session.execute(sa.update(RemediationRun).where(
        RemediationRun.Notify_State == RemediationNotifyState.PENDING,
        RemediationRun.Notify_Attempts > 0,
        RemediationRun.Notify_Error.is_(None),
    ).values(Notify_State=RemediationNotifyState.FAILED, Notify_Error=STOPPED_ERROR))
    db.session.commit()
    return result.rowcount
