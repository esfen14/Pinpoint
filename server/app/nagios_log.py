"""Bounded read-only Nagios log tail with conservative removal of free-form output."""
import os
import re
import stat

MAX_LINES = 500
MAX_BYTES = 64 * 1024

# Only structural state fields are published. Plugin output, command arguments,
# external commands, debug messages and unknown formats may carry credentials.
STATE_LINE = re.compile(
    r'^(\[\d{1,19}\]) ((?:HOST|SERVICE) ALERT|CURRENT (?:HOST|SERVICE) STATE|INITIAL (?:HOST|SERVICE) STATE): (.*)$'
)
TIMESTAMP = re.compile(r'^\[(\d{1,19})\]')


def redact_log_line(line):
    """Keep host/service state fields; replace all free-form and command-bearing content."""
    match = STATE_LINE.fullmatch(line)
    if match:
        prefix, kind, payload = match.groups()
        fields = payload.split(';')
        count = 5 if 'SERVICE' in kind else 4
        state_index = 2 if 'SERVICE' in kind else 1
        state_fields = fields[:count]
        if (len(fields) >= count and
                all(re.fullmatch(r'[\w .:/@()\-]{1,255}', field) for field in state_fields[:state_index]) and
                state_fields[state_index] in {'UP', 'DOWN', 'UNREACHABLE', 'OK', 'WARNING', 'CRITICAL', 'UNKNOWN'} and
                state_fields[state_index + 1] in {'HARD', 'SOFT'} and
                re.fullmatch(r'\d{1,10}', state_fields[state_index + 2])):
            return f'{prefix} {kind}: {";".join(state_fields)};[output redacted]'
    timestamp = TIMESTAMP.match(line)
    prefix = timestamp.group() + ' ' if timestamp else ''
    return prefix + '[message redacted]'


def read_nagios_log(path, lines=200, after=0):
    """Read at most 64 KiB from a fixed regular file's end, oldest to newest; never block on a FIFO."""
    result = {'lines': [], 'available': False, 'truncated': False,
              'max_lines': MAX_LINES, 'max_bytes': MAX_BYTES}
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                return result
            start = max(0, info.st_size - MAX_BYTES)
            stream.seek(start)
            content = stream.read(MAX_BYTES)
    except OSError:
        return result
    result['available'] = True
    result['truncated'] = start > 0
    if start:
        # The first record may start in the middle of a sensitive value.
        content = content.partition(b'\n')[2]
    records = content.decode('utf-8', errors='replace').splitlines()
    if len(records) > lines:
        result['truncated'] = True
    selected = records[-lines:]
    redacted = []
    used_bytes = 0
    for record in reversed(selected):
        timestamp = TIMESTAMP.match(record)
        if after and (not timestamp or int(timestamp[1]) <= after):
            continue
        safe = redact_log_line(record)
        size = len(safe.encode('utf-8')) + 1
        if used_bytes + size > MAX_BYTES:
            result['truncated'] = True
            break
        redacted.append(safe)
        used_bytes += size
    result['lines'] = list(reversed(redacted))
    return result
