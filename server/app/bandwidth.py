"""
Bandwidth rate calculation from stored SNMP octet counters.

The Nagios checks only record the raw ifInOctets / ifOutOctets counters. A counter
says nothing about bandwidth until two readings are compared, so the rates are
computed here from the samples kept in history.db and the check itself is left
untouched.

Between two consecutive samples:

    rate (bit/s) = (counter now - counter before) * 8 / seconds between them

Special cases, in order:

  * Counter wrap: a counter that goes down may simply have passed its maximum
    (2**32 for the 32-bit ifInOctets, 2**64 for the 64-bit ifHCInOctets) and started
    again at zero. The wrapped difference is used when it is a believable rate.
  * Device restart: a counter that goes down by more than a wrap can explain (the
    wrapped difference would be faster than the link, or than max_rate_bps) is a reset;
    that interval is left out instead of reported as a huge or negative rate.
  * Gap: two samples further apart than max_gap_seconds (monitoring was paused, Nagios was
    down) say nothing about the time between them, so that interval is left out.

A window with fewer than two valid samples has no rate at all: counter_rates returns None,
which callers show as "insufficient data". A window that has samples but no usable interval
returns an empty list.
"""
import math
from datetime import datetime, timezone

COUNTER_32_RANGE = 2 ** 32
COUNTER_64_RANGE = 2 ** 64

# Two samples further apart than this are not compared. Nagios checks run every few minutes.
DEFAULT_MAX_GAP_SECONDS = 1800

# No interface is faster than this today, so a faster rate can only be a counter reset.
DEFAULT_MAX_RATE_BPS = 100e9

# When the link speed is known, a rate this much above it is still treated as a reset
# (counters are sampled unevenly, so a little overshoot is normal).
SPEED_TOLERANCE = 1.1


def to_epoch_seconds(timestamp):
    """
    Return a timestamp as seconds since the epoch, or None if it cannot be read. Accepts a datetime
    (a naive one is taken as UTC, like the history.db timestamps) or a number.
    """
    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.timestamp()
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        return None
    return float(timestamp) if math.isfinite(timestamp) else None


def valid_samples(samples):
    """
    Return (epoch seconds, counter value) pairs sorted by time, without readings that cannot be
    used: a missing, non-numeric, infinite or negative counter, an unreadable timestamp, or a second
    reading at the same instant as another.
    """
    cleaned = {}
    for timestamp, value in samples or []:
        seconds = to_epoch_seconds(timestamp)
        if seconds is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if not math.isfinite(value) or value < 0:
            continue
        cleaned.setdefault(seconds, float(value))
    return sorted(cleaned.items())


def counter_rates(samples, counter_bits=None, max_gap_seconds=DEFAULT_MAX_GAP_SECONDS, max_rate_bps=DEFAULT_MAX_RATE_BPS):
    """
    Convert counter samples, a list of (timestamp, octets), to bit/s rates.

    counter_bits is 32 or 64; None picks 64 when any reading is above what a 32-bit counter can
    hold, otherwise 32. max_rate_bps is the fastest believable rate (the link speed when known);
    it decides whether a decrease was a wrap or a restart.

    Returns None when there are fewer than two valid samples, otherwise a list (possibly empty)
    of {"timestamp": datetime (UTC, end of the interval), "bps": float}, oldest first.
    """
    samples = valid_samples(samples)
    if len(samples) < 2:
        return None

    if counter_bits is None:
        counter_bits = 64 if max(value for _, value in samples) >= COUNTER_32_RANGE else 32
    wrap_range = COUNTER_64_RANGE if counter_bits == 64 else COUNTER_32_RANGE

    rates = []
    for (before_time, before_value), (now_time, now_value) in zip(samples, samples[1:]):
        seconds = now_time - before_time
        if seconds > max_gap_seconds:
            continue

        octets = now_value - before_value
        if octets < 0:
            octets += wrap_range
        bps = octets * 8 / seconds
        if bps > max_rate_bps:
            continue

        rates.append({"timestamp": datetime.fromtimestamp(now_time, timezone.utc), "bps": bps})
    return rates


def max_rate_for_speed(speed_bps):
    """The fastest believable rate for a link of speed_bps (bit/s); the default ceiling when it is unknown."""
    if isinstance(speed_bps, (int, float)) and not isinstance(speed_bps, bool) and speed_bps > 0:
        return speed_bps * SPEED_TOLERANCE
    return DEFAULT_MAX_RATE_BPS


def bucket_rates(rates, start, end, buckets):
    """
    Average rates into `buckets` equal slices of [start, end): [{"bucket_start": datetime,
    "bps": float | None}, ...]. A slice with no rate in it has bps None, so a chart shows a gap
    instead of a line through missing data.
    """
    width = (end - start) / buckets
    sums = [0.0] * buckets
    counts = [0] * buckets
    for rate in rates:
        index = int((rate["timestamp"] - start) / width)
        if 0 <= index < buckets:
            sums[index] += rate["bps"]
            counts[index] += 1
        elif index == buckets and rate["timestamp"] <= end:
            sums[-1] += rate["bps"]
            counts[-1] += 1

    return [
        {"bucket_start": start + width * i, "bps": sums[i] / counts[i] if counts[i] else None}
        for i in range(buckets)
    ]


def utilisation_pct(bps, speed_bps):
    """Percent of the link used by bps, or None when the rate or the link speed is unknown."""
    if bps is None or not isinstance(speed_bps, (int, float)) or isinstance(speed_bps, bool) or speed_bps <= 0:
        return None
    return bps / speed_bps * 100

