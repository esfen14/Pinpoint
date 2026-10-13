#!/usr/bin/python3 -I
"""
pinpoint_notify_email.py — builds and sends one Nagios notification as a formatted
HTML email with a plain-text alternative.

The Nagios config generator (app/network_discovery) points the contacts' host and
service notification commands at this script, in place of the stock `printf | mail`
commands that can only send plain text. It uses the standard library only and does
not import the application, so Nagios can run it as the `nagios` user.

Nagios passes values as key=value arguments, one per macro, for example:

    /usr/bin/python3 -I .../pinpoint_notify_email.py service "type=$NOTIFICATIONTYPE$" \\
        "host=$HOSTNAME$" "address=$HOSTADDRESS$" "service=$SERVICEDESC$" \\
        "state=$SERVICESTATE$" "output=$SERVICEOUTPUT$" "timet=$TIMET$" "to=$CONTACTEMAIL$"

Usage:  pinpoint_notify_email.py [--print] <host|service> key=value ...
    --print   write the finished message to stdout instead of sending it (preview and tests)

Keys: type, host, address, service (service only), state, output, time, timet, comment, to.
Everything is treated as untrusted: control characters are removed (no header
injection), the recipient must look like an email address, lengths are capped
and every value is HTML-escaped. Mail goes to /usr/sbin/sendmail (msmtp on the
appliance), so the account is the one saved in Settings -> Email.

Exit status: 0 sent (or printed), 1 rejected input, 2 misuse, 3 sendmail failed.
"""
import html
import re
import subprocess
import sys
from datetime import datetime, timezone
from email.message import EmailMessage

SENDMAIL = "/usr/sbin/sendmail"
SENDMAIL_TIMEOUT = 30

KINDS = {"host", "service"}
KEYS = {"type", "host", "address", "service", "state", "output", "time", "timet", "comment", "to"}
MAX_LENGTH = {"output": 1000, "comment": 500}
DEFAULT_MAX_LENGTH = 200

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]+")
PACKET_LOSS_RE = re.compile(r"packet\s+loss\s*=\s*(\d{1,3}(?:\.\d+)?)\s*%", re.IGNORECASE)

# Palette: page, card, card border, panel, text, muted text.
PAGE, CARD, BORDER, PANEL = "#0B1220", "#151F30", "#243049", "#101A2A"
TEXT, MUTED = "#E8EEF7", "#9AA7BB"

RED, AMBER, GREEN, BLUE, PURPLE, GREY = "#FF6B6B", "#F5B13D", "#3DD68C", "#6AA9FF", "#B79CFF", "#9AA7BB"
STATE_COLOUR = {
    "CRITICAL": RED, "DOWN": RED, "WARNING": AMBER, "OK": GREEN, "UP": GREEN,
    "UNREACHABLE": PURPLE, "UNKNOWN": GREY,
}


class InputRejected(Exception):
    """Invalid arguments. The message names the problem and never echoes a secret."""


def clean(value, limit):
    """Remove control characters, collapse whitespace, cap the length."""
    value = CONTROL_RE.sub(" ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def parse(argv):
    if len(argv) < 2 or argv[0] not in KINDS:
        raise InputRejected("first argument must be 'host' or 'service'")
    kind, fields = argv[0], {}
    for item in argv[1:]:
        key, sep, value = item.partition("=")
        if not sep or key not in KEYS:
            raise InputRejected(f"unknown or malformed argument: {key[:30]!r}")
        fields[key] = clean(value, MAX_LENGTH.get(key, DEFAULT_MAX_LENGTH))
    if not EMAIL_RE.match(fields.get("to", "")):
        raise InputRejected("'to' is missing or is not an email address")
    if kind == "service" and not fields.get("service"):
        raise InputRejected("a service notification needs 'service'")
    for required in ("host", "state", "type"):
        if not fields.get(required):
            raise InputRejected(f"'{required}' is required")
    return kind, fields


# ---------------------------------------------------------------- wording

def target_of(kind, f):
    return f["host"] if kind == "host" else f"{f['service']} on {f['host']}"


def describe(kind, f):
    """Return (pill label, icon, headline, supporting line, recommended action, accent colour)."""
    kind_type = f["type"].upper()
    state = f["state"].upper()
    accent = STATE_COLOUR.get(state, BLUE)
    host, target = f["host"], target_of(kind, f)

    if kind_type == "RECOVERY":
        headline = f"{host} is back online" if kind == "host" else f"{target} has recovered"
        return ("RECOVERED", "✓", headline, "The problem is over and monitoring is back to normal.",
                "No action needed.", GREEN)
    if kind_type == "ACKNOWLEDGEMENT":
        return ("ACKNOWLEDGED", "i", f"Problem on {target} was acknowledged",
                "Someone has taken ownership of this problem.", "No action needed unless it is not fixed soon.", BLUE)
    if kind_type in ("FLAPPINGSTART", "FLAPPINGSTOP", "FLAPPINGDISABLED"):
        if kind_type == "FLAPPINGSTOP":
            return ("STABLE", "✓", f"{target} is stable again", "The state stopped changing.", "No action needed.", GREEN)
        return ("UNSTABLE", "!", f"{target} keeps changing state",
                "It is switching between states, so alerts are paused to avoid noise.",
                "Check the device and its network link for an intermittent fault.", AMBER)
    if kind_type.startswith("DOWNTIME"):
        label = {"DOWNTIMESTART": "started", "DOWNTIMEEND": "ended", "DOWNTIMECANCELLED": "was cancelled"}.get(kind_type, "changed")
        return ("MAINTENANCE", "i", f"Maintenance on {target} {label}",
                "Alerts for this item are handled according to the maintenance window.", "No action needed.", BLUE)
    if kind_type == "CUSTOM":
        return ("NOTICE", "i", f"Message about {target}", f"Current state: {state}.",
                f["comment"] if f.get("comment") else "Review the details below.", accent)

    # PROBLEM (and anything unrecognised)
    if state == "DOWN":
        return ("CRITICAL ALERT", "!", f"{host} is unreachable", "PinPoint cannot reach this device.",
                "Check device connectivity and network configuration.", RED)
    if state == "UNREACHABLE":
        return ("UNREACHABLE", "!", f"{host} cannot be reached", "A device on the path to it may be down.",
                "Check the device between PinPoint and this host first.", PURPLE)
    if state == "CRITICAL":
        return ("CRITICAL ALERT", "!", f"{target} is critical", "A check reached its critical threshold.",
                "Check the service and the device it runs on.", RED)
    if state == "WARNING":
        return ("WARNING", "!", f"{target} needs attention", "A check passed its warning threshold.",
                "Review it before it becomes critical.", AMBER)
    if state == "UNKNOWN":
        return ("UNKNOWN", "?", f"{target} state is unknown", "The check could not decide a state.",
                "Check that the monitoring agent or plugin is working.", GREY)
    return (state, "!", f"{target} is {state}", "", "Review the details below.", accent)


def detected_utc(f):
    """Detection time in UTC: from the Nagios epoch (timet) when given, else the text Nagios sent."""
    timet = f.get("timet", "")
    if timet.isdigit():
        try:
            return datetime.fromtimestamp(int(timet), timezone.utc).strftime("%b %d, %Y · %H:%M:%S UTC")
        except (OverflowError, OSError, ValueError):
            pass
    return f.get("time", "")


def packet_loss(output):
    """'100% Packet Loss' parsed from ping output, or None when the output has no such figure."""
    match = PACKET_LOSS_RE.search(output or "")
    if not match:
        return None
    number = match.group(1)
    return f"{number.rstrip('0').rstrip('.') if '.' in number else number}% Packet Loss"


def subject_for(kind, f):
    target = f["host"] if kind == "host" else f"{f['host']} / {f['service']}"
    state = f["state"].upper()
    if f["type"].upper() == "RECOVERY":
        return f"[PinPoint] RECOVERY: {target} is {state}"
    return f"[PinPoint] {state}: {target}"


# ---------------------------------------------------------------- rendering

def blend(foreground, background, amount):
    """Mix two #rrggbb colours: `amount` of foreground over background."""
    fg = [int(foreground[i:i + 2], 16) for i in (1, 3, 5)]
    bg = [int(background[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(b + (f_ - b) * amount):02x}" for f_, b in zip(fg, bg))


def device_rows(kind, f):
    rows = [("Host", f["host"], False)]
    if f.get("address"):
        rows.append(("IP address", f["address"], True))
    if kind == "service":
        rows.append(("Service", f["service"], False))
    when = detected_utc(f)
    if when:
        rows.append(("Detected (UTC)", when, False))
    return rows


def render_text(kind, f):
    pill, _icon, headline, support, action, _accent = describe(kind, f)
    lines = [f"PinPoint: {headline}", ""]
    if support:
        lines += [support, ""]
    for label, value, _mono in device_rows(kind, f):
        lines.append(f"{label}: {value}")
    lines.append(f"Status: {f['state'].upper()}")
    if f.get("output"):
        lines += ["", "Check output:", f["output"]]
    if f.get("comment") and f["type"].upper() != "CUSTOM":
        lines += ["", "Note:", f["comment"]]
    lines += ["", f"Recommended action: {action}", "", "-- ",
              "Sent by PinPoint network monitoring. This is an automated alert; please do not reply."]
    return "\n".join(lines) + "\n"


def render_html(kind, f):
    e = html.escape
    pill, icon, headline, support, action, accent = describe(kind, f)
    state = f["state"].upper()
    tint = blend(accent, CARD, 0.12)
    mono = "'JetBrains Mono',Consolas,Menlo,'Courier New',monospace"
    sans = "Inter,'Segoe UI',Helvetica,Arial,sans-serif"

    rows = "".join(
        f'<tr class="row"><td style="padding:9px 0;width:130px;color:{MUTED};font-size:13px;vertical-align:top">{e(label)}</td>'
        f'<td style="padding:9px 0;color:{TEXT};font-size:14px;font-weight:600;word-break:break-word'
        f'{";font-family:" + mono if is_mono else ""}">{e(value)}</td></tr>'
        for label, value, is_mono in device_rows(kind, f)
    )
    rows += (
        f'<tr class="row"><td style="padding:9px 0;width:130px;color:{MUTED};font-size:13px;vertical-align:middle">Status</td>'
        f'<td style="padding:9px 0"><span style="display:inline-block;padding:3px 12px;border-radius:999px;'
        f'background:{tint};border:1px solid {accent};color:{accent};font-size:12px;font-weight:700;letter-spacing:.06em">{e(state)}</span></td></tr>'
    )

    metric = packet_loss(f.get("output"))
    diagnostic = ""
    if metric or f.get("output"):
        metric_html = (
            f'<div style="font-size:30px;line-height:1.1;font-weight:800;color:{accent};margin:0 0 12px">{e(metric)}</div>'
            if metric else ""
        )
        output_html = (
            f'<div style="padding:10px 12px;background:{PAGE};border:1px solid {BORDER};border-radius:8px;'
            f'font-family:{mono};font-size:12.5px;line-height:1.5;color:{TEXT};word-break:break-word">{e(f["output"])}</div>'
            if f.get("output") else ""
        )
        diagnostic = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:16px;'
            f'border-radius:12px;overflow:hidden;background:{tint}"><tr>'
            f'<td width="4" style="width:4px;background:{accent};font-size:0;line-height:0">&nbsp;</td>'
            f'<td style="padding:16px 18px"><div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;'
            f'color:{MUTED};margin:0 0 8px">Diagnostic</div>{metric_html}{output_html}</td></tr></table>'
        )

    note = ""
    if f.get("comment") and f["type"].upper() != "CUSTOM":
        note = (f'<p style="margin:16px 0 0;font-size:13px;line-height:1.5;color:{MUTED}">'
                f'<strong style="color:{TEXT}">Note:</strong> {e(f["comment"])}</p>')

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="supported-color-schemes" content="dark">
<title>{e(subject_for(kind, f))}</title>
<style>
@media only screen and (max-width:620px) {{
  .pill {{ display:none !important; }}
  .pad {{ padding:20px 16px !important; }}
  .h1 {{ font-size:20px !important; }}
  .row td {{ display:block !important; width:100% !important; padding:2px 0 !important; }}
  .row + .row td:first-child {{ padding-top:10px !important; }}
}}
</style></head>
<body style="margin:0;padding:0;background:{PAGE};font-family:{sans}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{PAGE}">{e(headline)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:{CARD};border:1px solid {BORDER};border-radius:16px;border-collapse:separate">
<tr><td class="pad" style="padding:20px 28px;border-bottom:1px solid {BORDER}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="44" style="width:44px"><div style="width:36px;height:36px;line-height:36px;border-radius:10px;background:#2F6BFF;color:#ffffff;text-align:center;font-size:18px;font-weight:800">P</div></td>
<td style="color:{TEXT};font-size:17px;font-weight:700;line-height:1.2">PinPoint<br><span style="font-size:12px;font-weight:400;color:{MUTED}">Network Monitoring</span></td>
<td class="pill" align="right"><span style="display:inline-block;padding:5px 12px;border-radius:999px;background:{tint};border:1px solid {accent};color:{accent};font-size:11px;font-weight:700;letter-spacing:.08em">{e(pill)}</span></td>
</tr></table></td></tr>
<tr><td class="pad" style="padding:28px 28px 8px">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td width="52" style="width:52px;vertical-align:top"><div style="width:40px;height:40px;line-height:36px;border-radius:50%;border:2px solid {accent};color:{accent};text-align:center;font-size:22px;font-weight:800">{e(icon)}</div></td>
<td><h1 class="h1" style="margin:0 0 6px;font-size:24px;line-height:1.25;color:{TEXT}">{e(headline)}</h1>
<p style="margin:0;font-size:14px;line-height:1.5;color:{MUTED}">{e(support)}</p></td></tr></table></td></tr>
<tr><td class="pad" style="padding:16px 28px 8px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PANEL};border:1px solid {BORDER};border-radius:12px"><tr><td style="padding:8px 18px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr></table>
{diagnostic}{note}</td></tr>
<tr><td class="pad" style="padding:8px 28px 24px">
<p style="margin:12px 0 0;font-size:14px;line-height:1.5;color:{TEXT}"><strong>Recommended action:</strong> <span style="color:{MUTED}">{e(action)}</span></p></td></tr>
<tr><td class="pad" style="padding:16px 28px;border-top:1px solid {BORDER};font-size:12px;line-height:1.6;color:{MUTED}">
Please check on this alert.<br>This is an automated message from PinPoint. Please do not reply.</td></tr>
</table></td></tr></table></body></html>
"""


def build_message(kind, f):
    msg = EmailMessage()
    msg["To"] = f["to"]
    msg["Subject"] = subject_for(kind, f)
    msg.set_content(render_text(kind, f))
    msg.add_alternative(render_html(kind, f), subtype="html")
    return msg


def main(argv):
    preview = "--print" in argv
    argv = [a for a in argv if a != "--print"]
    try:
        kind, fields = parse(argv)
    except InputRejected as error:
        print(f"pinpoint-notify-email: {error}", file=sys.stderr)
        return 1 if argv else 2
    message = build_message(kind, fields)
    if preview:
        sys.stdout.write(message.as_string())
        return 0
    try:
        subprocess.run([SENDMAIL, "-t", "-i"], input=message.as_bytes(), check=True,
                       timeout=SENDMAIL_TIMEOUT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"pinpoint-notify-email: could not send ({type(error).__name__})", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
