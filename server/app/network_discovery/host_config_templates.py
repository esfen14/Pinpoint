from pathlib import Path

from app import db
from app.system_models import NotificationPolicy, SystemSettings

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
    if service.get("active_checks_enabled") is False:
        rendered = add_inactive_lines(rendered, service.get("notes") or "Address unknown")
    return rendered
    
def create_contact(contact):
    return _load_template("contact.cfg.tpl").format(
        contact_name=contact["contact_name"],
        use=contact["use"],
        alias=contact["full_name"],
        email_address=contact["email_address"] 
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