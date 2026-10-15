import re
from pathlib import Path

import sqlalchemy as sa

from app import db, remediation
from app.system_models import Escalation, NotificationPolicy, RemediationAction, SystemSettings

NOTIFICATION_PERIOD = "pinpoint_notify"
WEEKDAYS = ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday")


def notification_policy():
    """Read the saved policy or use backward-compatible defaults before migration."""
    return db.session.get(NotificationPolicy, 1) or NotificationPolicy(
        Id=1, Quiet_Hours=[], Host_Options="d,u,r,f,s", Service_Options="w,u,c,r,f,s",
        Renotify_Interval=30,
    )


def notification_period(policy):
    """Use the built-in period unless a saved quiet window needs a custom one."""
    return NOTIFICATION_PERIOD if policy.Quiet_Hours else "24x7"


def create_notification_timeperiod(policy=None):
    """Render allowed minutes as each weekday's quiet-window complement."""
    policy = policy or notification_policy()
    if not policy.Quiet_Hours:
        return ""
    lines = []
    for day in WEEKDAYS:
        quiet = sorted((window["start"], window["end"]) for window in policy.Quiet_Hours
                       if window["weekday"] == day)
        allowed = []
        cursor = "00:00"
        for start, end in quiet:
            if cursor < start:
                allowed.append(f"{cursor}-{start}")
            cursor = end
        if cursor < "24:00":
            allowed.append(f"{cursor}-24:00")
        if allowed:
            lines.append(f"    {day:<32}{','.join(allowed)}")
    return _load_template("timeperiod.cfg.tpl").format(name=NOTIFICATION_PERIOD, days="\n".join(lines))



def check_interval():
    row = db.session.get(SystemSettings, 1)
    return row.Check_Interval if row else 5


DEFAULT_RETRY_INTERVAL = 1
DEFAULT_MAX_CHECK_ATTEMPTS = 3


def check_timing():
    """(retry_interval, max_check_attempts) in effect; the values the config always used when nothing is saved."""
    row = db.session.get(SystemSettings, 1)
    if row is None:
        return DEFAULT_RETRY_INTERVAL, DEFAULT_MAX_CHECK_ATTEMPTS
    return row.Retry_Interval, row.Max_Check_Attempts

_template_cache = {}

def _load_template(name):
    if name not in _template_cache:
        template_cache = Path(__file__).parent / "templates" / name
        _template_cache[name] = template_cache.read_text()
    return _template_cache[name]

def add_inactive_lines(rendered, note):
    """
    Append `active_checks_enabled 0` and a notes line to a rendered
    host/service object, just before its closing brace. Used for devices whose
    address is unknown, so Nagios stops checking an IP that now belongs to a
    different machine.
    """
    body = rendered.rstrip()
    assert body.endswith("}")
    lines = [
        body[:-1].rstrip(),
        "    active_checks_enabled           0",
        f"    notes                           {note}",
        "}",
    ]
    return "\n".join(lines)

def flap_settings():
    """(enabled, low, high) flap detection settings in effect; detection on with Nagios's own thresholds when nothing is saved."""
    row = db.session.get(SystemSettings, 1)
    if row is None:
        return True, None, None
    return row.Flap_Detection_Enabled, row.Flap_Low_Threshold, row.Flap_High_Threshold


def add_flap_lines(rendered):
    """
    Append the saved flap detection settings to a rendered host/service object,
    just before its closing brace. Nothing is added for the defaults (detection
    on, no thresholds), so default output is unchanged. When detection is off
    only `flap_detection_enabled 0` is written; the thresholds would be ignored.
    """
    enabled, low, high = flap_settings()
    extra = []
    if not enabled:
        extra.append("    flap_detection_enabled          0")
    else:
        if low is not None:
            extra.append("    low_flap_threshold              %g" % low)
        if high is not None:
            extra.append("    high_flap_threshold             %g" % high)
    if not extra:
        return rendered
    body = rendered.rstrip()
    assert body.endswith("}")
    return "\n".join([body[:-1].rstrip(), *extra, "}"])

def _drop_empty_contact_groups(rendered):
    """Remove a blank contact_groups line (no eligible alert contact exists)."""
    kept = []
    for line in rendered.split("\n"):
        if line.strip() == "contact_groups":
            continue
        kept.append(line)
    return "\n".join(kept)


def create_host(host):
    retry_interval, max_attempts = check_timing()
    # Hosts have never had an explicit retry_interval; write one only when it
    # differs from the default, so default output stays exactly as it was.
    retry_line = "" if retry_interval == DEFAULT_RETRY_INTERVAL else "\n    retry_interval                  %d" % retry_interval
    policy = notification_policy()
    rendered = _load_template("host.cfg.tpl").format(
        host_name=host["host_name"],
        alias=host["alias"],
        address=host["address"],
        contact_groups=host["contact_groups"],
        check_interval=check_interval(),
        max_check_attempts=max_attempts,
        retry_interval_line=retry_line,
        renotify_interval=policy.Renotify_Interval,
        period=notification_period(policy),
        notification_options=(f"\n    notification_options            {policy.Host_Options}"
                              if policy.Host_Options != "d,u,r,f,s" else ""),
    )
    rendered = _drop_empty_contact_groups(rendered)
    rendered = add_flap_lines(rendered)
    rendered = add_event_handler_lines(rendered, "host", host["host_name"], None)
    if host.get("active_checks_enabled") is False:
        rendered = add_inactive_lines(rendered, host.get("notes") or "Address unknown")
    return rendered
    
def create_service(service, service_command):
    retry_interval, max_attempts = check_timing()
    policy = notification_policy()
    fields = (f"\n    notification_period         {notification_period(policy)}"
              f"\n    notification_options        {policy.Service_Options}"
              f"\n    notification_interval       {policy.Renotify_Interval}"
              if policy.Quiet_Hours or policy.Service_Options != "w,u,c,r,f,s" or policy.Renotify_Interval != 30
              else "")
    rendered = _load_template("service.cfg.tpl").format(
        host_name=service["host_name"],
        service_name=service["service_name"],
        command=service_command,
        contact_groups=service["contact_groups"],
        check_interval=check_interval(),
        retry_interval=retry_interval,
        max_check_attempts=max_attempts,
        notification_fields=fields,
    )
    rendered = _drop_empty_contact_groups(rendered)
    rendered = add_flap_lines(rendered)
    rendered = add_event_handler_lines(rendered, "service", service["host_name"], service["service_name"])
    if service.get("active_checks_enabled") is False:
        rendered = add_inactive_lines(rendered, service.get("notes") or "Address unknown")
    return rendered
    
# ----------------------------------------------------------------------
# Notification commands
#
# Alert email is formatted HTML. The two commands below call
# server/scripts/pinpoint_notify_email.py, which builds the message and hands it
# to msmtp. If the script is missing, or its path holds a character that is not
# safe to write into a Nagios command line, contacts keep Nagios's stock
# plain-text commands, so alerts are never lost.
# ----------------------------------------------------------------------
NOTIFY_PYTHON = "/usr/bin/python3"
STOCK_NOTIFY_COMMANDS = {"host": "notify-host-by-email", "service": "notify-service-by-email"}
HTML_NOTIFY_COMMANDS = {"host": "pinpoint_notify_host_html", "service": "pinpoint_notify_service_html"}
_SAFE_COMMAND_PATH = re.compile(r"^/[A-Za-z0-9_./-]+$")


def notification_script_path():
    """Absolute path of the HTML notification script, or None when it cannot be used."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "pinpoint_notify_email.py"
    path = script.as_posix()
    if not script.is_file() or not _SAFE_COMMAND_PATH.match(path):
        return None
    return path


def notification_command_names():
    """{'host': ..., 'service': ...}: the commands contacts use for host and service alerts."""
    return HTML_NOTIFY_COMMANDS if notification_script_path() else STOCK_NOTIFY_COMMANDS


def create_notification_commands():
    """The `define command` blocks for HTML alert email, or an empty string when the stock commands are used."""
    script = notification_script_path()
    if script is None:
        return ""
    return _load_template("notification_commands.cfg.tpl").format(
        host_command=HTML_NOTIFY_COMMANDS["host"],
        service_command=HTML_NOTIFY_COMMANDS["service"],
        python=NOTIFY_PYTHON,
        script=script,
    )


# ----------------------------------------------------------------------
# Event handler (remediation)
#
# A covered host or service gets `event_handler pinpoint_event_handler_<kind>`: Nagios then
# runs server/scripts/pinpoint_event_handler.py (installed by the installer at
# EVENT_HANDLER_PATH) on every state change, and it leaves a note in the spool folder.
# Nothing is written unless an action is enabled AND the program exists on this machine,
# because Nagios rejects a config that names an undefined command. Objects no enabled
# action covers are rendered exactly as before.
# ----------------------------------------------------------------------
EVENT_HANDLER_PATH = "/usr/local/sbin/pinpoint-event-handler"
EVENT_HANDLER_COMMANDS = {"host": "pinpoint_event_handler_host", "service": "pinpoint_event_handler_service"}


def handler_exists(path):
    """True when the handler program is a file on this machine. A separate function so tests can set it."""
    return Path(path).is_file()


def event_handler_path():
    """The handler path to write into config, or None when it is missing or unsafe in a command line."""
    if not _SAFE_COMMAND_PATH.match(EVENT_HANDLER_PATH) or not handler_exists(EVENT_HANDLER_PATH):
        return None
    return EVENT_HANDLER_PATH


def enabled_remediation_actions():
    """All enabled remediation actions (read-only)."""
    return db.session.scalars(sa.select(RemediationAction).where(RemediationAction.Enabled.is_(True))).all()


def create_event_handler_commands():
    """The `define command` blocks for the event handler, or an empty string when none are needed."""
    script = event_handler_path()
    if script is None or not enabled_remediation_actions():
        return ""
    return _load_template("event_handler_commands.cfg.tpl").format(python=NOTIFY_PYTHON, script=script)


def add_event_handler_lines(rendered, kind, host_name, service_name):
    """
    Append `event_handler` and `event_handler_enabled 1` to a rendered host or service when an
    enabled action covers it, just before the closing brace. Otherwise return it unchanged. The
    same matching as the consumer (app/remediation.py) decides what is covered.
    """
    if event_handler_path() is None:
        return rendered
    event = {"kind": kind, "host": host_name, "service": service_name}
    if not any(remediation.covers(action, event) for action in enabled_remediation_actions()):
        return rendered
    body = rendered.rstrip()
    assert body.endswith("}")
    lines = [
        body[:-1].rstrip(),
        "    %-32s%s" % ("event_handler", EVENT_HANDLER_COMMANDS[kind]),
        "    %-32s%s" % ("event_handler_enabled", "1"),
        "}",
    ]
    return "\n".join(lines)


def create_contact(contact):
    commands = notification_command_names()
    # Only the HTML commands are written. Without them the contact inherits
    # Nagios's stock commands from its template, so the file is unchanged.
    lines = ("" if commands is STOCK_NOTIFY_COMMANDS else
             f"\n    service_notification_commands   {commands['service']}"
             f"\n    host_notification_commands      {commands['host']}")
    return _load_template("contact.cfg.tpl").format(
        contact_name=contact["contact_name"],
        use=contact["use"],
        alias=contact["full_name"],
        email_address=contact["email_address"],
        notification_commands=lines,
    )

def create_contact_template(contact_template):
    policy = notification_policy()
    return _load_template("contact_template.cfg.tpl").format(
        template_name=contact_template,
        register=("\n    register                        0" if contact_template == "pinpoint-contact" else ""),
        period=notification_period(policy),
        host_options=policy.Host_Options,
        service_options=policy.Service_Options,
    )
    
def create_hostgroup(hostgroup):
    return _load_template("hostgroup.cfg.tpl").format(
        group_name=hostgroup["group_name"],
        alias=hostgroup["alias_name"],
        members=hostgroup["member_list"] 
    )

def create_contactgroup(contactgroup):
    return _load_template("contactgroup.cfg.tpl").format(
        contactgroup_name=contactgroup["group_name"],
        alias=contactgroup["alias_name"],
        members=contactgroup["member_list"] 
    )

def create_multi_host_service(host_group_name, service_name, command, contactgroup):
    return _load_template("multi_host_service.cfg.tpl").format(
        host_group_name=host_group_name,
        service_name=service_name,
        command=command,
        contact_groups=contactgroup
    )

def create_escalations(groups, hosts, services):
    """Render saved ranges only for eligible groups and present scoped hosts.

    The global wildcard is a fixed literal. Scoped names come from the same
    generated hosts, never the request; reject control/config metacharacters.
    Return blocks and referenced groups; this helper does not commit.
    """
    blocks, needed = [], set()
    for row in db.session.scalars(sa.select(Escalation).order_by(Escalation.EscalationID)):
        if not groups.get(row.Contact_Group):
            continue
        hostname = '*' if row.HostID is None else hosts.get(row.HostID)
        if not hostname or (hostname != '*' and not re.fullmatch(r'[A-Za-z0-9_.:-]+', hostname)):
            continue
        if not (1 <= row.First_Notification <= row.Last_Notification <= 10000
                and 0 <= row.Interval_Minutes <= 1440):
            continue
        fields = dict(host_name=hostname, contact_group=row.Contact_Group,
                      first=row.First_Notification, last=row.Last_Notification,
                      interval=row.Interval_Minutes)
        blocks.append(_load_template('hostescalation.cfg.tpl').format(**fields))
        if row.HostID is None or services.get(hostname):
            blocks.append(_load_template('serviceescalation.cfg.tpl').format(**fields))
        needed.add(row.Contact_Group)
    return blocks, needed
