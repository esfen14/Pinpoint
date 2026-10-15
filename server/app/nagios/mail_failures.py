"""Read a bounded Nagios worker-log tail for notification delivery failures.

Nagios 4.5.11 base/workers.c emits a NOTIFY job header followed by indented
host/status/stderr/stdout lines. Only fixed reasons leave this module: raw
command lines, output, addresses and credentials are never returned or logged.
The indicator describes the latest failure in the current tail, not proof of
current delivery health; successes do not erase historical failures.
"""
import os
import re
import stat
from datetime import datetime, timezone

MAX_TAIL_BYTES = 64 * 1024
LINE = re.compile(r'^\[(\d{1,12})\] wproc: (.*)$')
JOB = re.compile(r'^NOTIFY job \d+ from worker .+ (?:is a non-check helper but exited with return code ([1-9]\d{0,2})|timed out after [\d.]+s|died by signal \d+.*)$')


def read_mail_failure(path):
    """Return the latest {time, reason}, or None for an unavailable/empty log.

    Open nonblocking and accept only regular files; read at most 64 KiB even
    when the log is large or grows during the request. Ignore a partial first
    or last line and reopen each time so rotation needs no persistent cursor.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode):
                return None
            start = max(0, info.st_size - MAX_TAIL_BYTES)
            handle.seek(start)
            data = handle.read(MAX_TAIL_BYTES)
    except (OSError, ValueError, TypeError):
        return None

    if start:
        data = data.partition(b'\n')[2]
    if not data.endswith(b'\n'):
        data = data.rpartition(b'\n')[0]
    latest = None
    in_notification = False
    for line in data.decode('utf-8', 'replace').splitlines():
        match = LINE.fullmatch(line)
        if not match:
            in_notification = False
            continue
        timestamp, text = match.groups()
        header = JOB.fullmatch(text)
        if header:
            try:
                time = datetime.fromtimestamp(int(timestamp), timezone.utc).isoformat()
            except (ValueError, OverflowError, OSError):
                in_notification = False
                continue
            code = header.group(1)
            reason = f'Notification command failed (exit code {code}).' if code else 'Notification command timed out or was terminated.'
            latest = {'time': time, 'reason': reason}
            in_notification = True
        elif not text.startswith('  '):
            in_notification = False
        elif in_notification and text.startswith('  stderr line '):
            # Match known categories but never reflect the source text.
            detail = text.lower()
            if 'account default not found' in detail or 'cannot read' in detail and 'msmtprc' in detail:
                latest['reason'] = 'Notification mail transport is not configured.'
            elif 'authentication failed' in detail or '535' in detail or 'badcredentials' in detail:
                latest['reason'] = 'Notification email login was rejected.'
            elif 'cannot connect' in detail or 'connection refused' in detail or 'connection timed out' in detail:
                latest['reason'] = 'Notification email could not connect to the SMTP relay.'
            elif 'certificate' in detail or 'tls' in detail:
                latest['reason'] = 'Notification email could not establish a secure SMTP connection.'
    return latest
