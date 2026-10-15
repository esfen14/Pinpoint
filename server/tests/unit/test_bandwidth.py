"""
tests/unit/test_bandwidth.py — The bandwidth rate calculator (app/bandwidth.py).

Synthetic counters in, bit/s out: the plain rate, the wrap of 32-bit and 64-bit counters, a
counter reset (device restart), a gap in the samples, and a window with too few valid samples.
Pure functions: no database or app context.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.bandwidth import (
    COUNTER_32_RANGE,
    COUNTER_64_RANGE,
    bucket_rates,
    counter_rates,
    max_rate_for_speed,
    utilisation_pct,
)

T0 = datetime(2026, 10, 14, 12, 0, 0, tzinfo=timezone.utc)


def at(seconds):
    return T0 + timedelta(seconds=seconds)


def bps(samples, **options):
    rates = counter_rates(samples, **options)
    return None if rates is None else [round(rate["bps"], 3) for rate in rates]


class TestRate:

    def test_octets_become_bits_per_second(self):
        # 7.5 MB in 60 s = 1 Mbit/s.
        assert bps([(at(0), 0), (at(60), 7_500_000)]) == [1_000_000]

    def test_each_interval_has_its_own_rate_stamped_at_its_end(self):
        rates = counter_rates([(at(0), 0), (at(60), 750_000), (at(120), 2_250_000)])
        assert [r["bps"] for r in rates] == [100_000, 200_000]
        assert [r["timestamp"] for r in rates] == [at(60), at(120)]

    def test_naive_timestamps_are_utc(self):
        naive = T0.replace(tzinfo=None)
        rates = counter_rates([(naive, 0), (naive + timedelta(seconds=10), 125)])
        assert rates[0]["bps"] == 100 and rates[0]["timestamp"] == T0 + timedelta(seconds=10)

    def test_unordered_samples_are_sorted(self):
        assert bps([(at(60), 750_000), (at(0), 0)]) == [100_000]

    def test_idle_interface_is_zero(self):
        assert bps([(at(0), 500), (at(60), 500)]) == [0]


class TestWrap:

    def test_32_bit_counter_wraps(self):
        # 1000 octets before the top, 2000 after: 3000 octets in 10 s.
        assert bps([(at(0), COUNTER_32_RANGE - 1000), (at(10), 2000)]) == [2400]

    def test_64_bit_counter_wraps(self):
        # Stored values are floats, so use a delta far above their precision at 2**64.
        samples = [(at(0), COUNTER_64_RANGE - 1_000_000_000), (at(10), 500_000_000)]
        assert bps(samples, counter_bits=64) == [pytest.approx(1_200_000_000, rel=1e-5)]

    def test_64_bit_counter_is_recognised_by_its_size(self):
        # A reading above 2**32 can only come from a 64-bit counter, so a drop is a reset, not a wrap.
        samples = [(at(0), 5_000_000_000), (at(10), 100), (at(20), 1350)]
        assert bps(samples) == [1000]

    def test_explicit_width_overrides_detection(self):
        samples = [(at(0), COUNTER_32_RANGE - 1000), (at(10), 2000)]
        assert bps(samples, counter_bits=32) == [2400]
        assert bps(samples, counter_bits=64) == []   # a 64-bit wrap would be an impossible rate


class TestReset:

    def test_restart_is_left_out_not_negative(self):
        samples = [(at(0), 3_000_000_000), (at(60), 1000), (at(120), 8500)]
        rates = counter_rates(samples, max_rate_bps=max_rate_for_speed(100_000_000))
        assert [r["timestamp"] for r in rates] == [at(120)]
        assert rates[0]["bps"] == pytest.approx(1000)

    def test_without_a_speed_a_believable_wrap_is_kept(self):
        # 3e9 -> 1000 over 60 s is 1.29e9 octets: 172 Mbit/s, not impossible on an unknown link.
        assert bps([(at(0), 3_000_000_000), (at(60), 1000)]) == [pytest.approx(172_000_000, rel=0.01)]

    def test_no_rate_is_ever_negative(self):
        samples = [(at(0), 900), (at(10), 100), (at(20), 50), (at(30), 600)]
        assert all(rate >= 0 for rate in bps(samples, max_rate_bps=1e6))


class TestGapAndInsufficientData:

    def test_a_long_gap_is_not_averaged_over(self):
        samples = [(at(0), 0), (at(60), 750_000), (at(60 + 7200), 9_000_000), (at(60 + 7260), 9_750_000)]
        assert bps(samples) == [100_000, 100_000]

    def test_gap_limit_can_be_changed(self):
        samples = [(at(0), 0), (at(7200), 900_000)]
        assert bps(samples) == []
        assert bps(samples, max_gap_seconds=10_000) == [1000]

    @pytest.mark.parametrize("samples", [[], None, [(at(0), 1)]])
    def test_fewer_than_two_samples_is_none(self, samples):
        assert counter_rates(samples) is None

    def test_invalid_readings_do_not_count(self):
        samples = [(at(0), None), (at(10), float("nan")), (at(20), -5), (at(30), "7"), (at(40), True), (None, 3), (at(50), 10)]
        assert counter_rates(samples) is None

    def test_one_valid_sample_among_bad_ones_is_still_insufficient(self):
        assert counter_rates([(at(0), 100), (at(10), None)]) is None

    def test_two_samples_at_the_same_instant_count_once(self):
        assert counter_rates([(at(0), 100), (at(0), 200)]) is None

    def test_valid_samples_but_no_usable_interval_is_an_empty_list(self):
        assert counter_rates([(at(0), 0), (at(99999), 100)]) == []


class TestBuckets:

    def test_rates_are_averaged_per_bucket_with_gaps_as_none(self):
        rates = [
            {"timestamp": at(10), "bps": 100.0},
            {"timestamp": at(20), "bps": 300.0},
            {"timestamp": at(130), "bps": 50.0},
        ]
        buckets = bucket_rates(rates, at(0), at(180), 3)

        assert [b["bps"] for b in buckets] == [200.0, None, 50.0]
        assert [b["bucket_start"] for b in buckets] == [at(0), at(60), at(120)]

    def test_a_rate_at_the_very_end_belongs_to_the_last_bucket(self):
        assert bucket_rates([{"timestamp": at(180), "bps": 7.0}], at(0), at(180), 3)[-1]["bps"] == 7.0


class TestHelpers:

    def test_known_speed_sets_a_ceiling_just_above_it(self):
        assert max_rate_for_speed(1_000_000_000) == pytest.approx(1_100_000_000)

    @pytest.mark.parametrize("speed", [None, 0, -1, True, "1000"])
    def test_unknown_speed_uses_the_default_ceiling(self, speed):
        assert max_rate_for_speed(speed) == 100e9

    def test_utilisation(self):
        assert utilisation_pct(250_000_000, 1_000_000_000) == 25
        assert utilisation_pct(None, 1_000_000_000) is None
        assert utilisation_pct(1, None) is None
        assert utilisation_pct(1, 0) is None
