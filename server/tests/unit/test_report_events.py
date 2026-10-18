"""Availability detail, alert summary and histogram (#199).

Fixtures use the native archivejson shapes probed on Nagios Core 4.5.11:
millisecond timestamps, state bitmasks, HARD=1 / SOFT=2 and a synthetic
"Initial ... Pseudo-State" first entry. No live Nagios is contacted.
"""
import os
import time
from unittest.mock import patch

import pytest

from app.nagios import report_events as re_
from app.nagios.service_availability import AvailabilityError

CGI = "app.nagios.report_events.request_cgi"
DETAIL = "/api/system/report/availability-detail"
SUMMARY = "/api/system/report/alert-summary"
HISTOGRAM = "/api/system/report/alert-histogram"
START, END = 1_700_000_000, 1_700_001_000


def envelope(data):
    return {"result": {"type_code": 0, "query_time": 9_999_999_999_000}, "data": data}


def svc_event(ts, state, state_type=1, host="web", desc="http", output="out"):
    return {"timestamp": ts * 1000, "object_type": 2, "host_name": host, "description": desc,
            "state_type": state_type, "state": state, "plugin_output": output}


def host_event(ts, state, state_type=1, host="web", output="out"):
    return {"timestamp": ts * 1000, "object_type": 1, "name": host,
            "state_type": state_type, "state": state, "plugin_output": output}


def initial(ts, state=8):
    return svc_event(ts, state, output="Initial Service Pseudo-State")


def native_service(ok=0, warning=0, critical=0, unknown=0, nodata=0, notrunning=0, sched=None):
    sched = sched or {}
    return {"host_name": "web", "description": "http",
            "time_ok": ok, "time_warning": warning, "time_critical": critical, "time_unknown": unknown,
            "scheduled_time_ok": sched.get("ok", 0), "scheduled_time_warning": 0,
            "scheduled_time_critical": sched.get("critical", 0), "scheduled_time_unknown": 0,
            "time_indeterminate_nodata": nodata, "time_indeterminate_notrunning": notrunning}


def fake_cgi(availability=None, changes=None, alerts=None, assumed=None):
    def call(config_key, params, deadline):
        query = params["query"]
        if query == "availability":
            if assumed is not None and params.get("assumestatesduringnagiosdowntime") == "true":
                return envelope(assumed)
            return envelope(availability)
        key = {"statechangelist": "statechangelist", "alertlist": "alertlist"}[query]
        rows = (changes if query == "statechangelist" else alerts) or []
        start, count = params["start"], params["count"]
        return envelope({key: rows[start:start + count]})
    return call


def service_detail(events, native):
    with patch(CGI, fake_cgi(availability={"service": native}, changes=events)):
        return re_.read_availability_detail("web", "http", START, END)


class TestIntervals:
    def test_pre_range_onset_has_unknown_start_not_a_healthy_state(self):
        detail = service_detail([initial(START)], native_service(nodata=1000))
        assert [i["state"] for i in detail["intervals"]] == ["no_data"]
        assert detail["intervals"][0]["unknown_onset"] is True
        assert detail["reconciliation"]["matches"] is True

    def test_mixed_states_continuing_outage_and_exact_bounds(self):
        events = [initial(START), svc_event(START + 100, 8), svc_event(START + 400, 32, output="down"),
                  svc_event(START + 700, 16)]
        detail = service_detail(events, native_service(nodata=100, ok=300, critical=300, warning=300))
        states = [(i["state"], i["start"], i["end"]) for i in detail["intervals"]]
        assert states == [("no_data", START, START + 100), ("ok", START + 100, START + 400),
                          ("critical", START + 400, START + 700), ("warning", START + 700, END)]
        assert detail["intervals"][-1]["continuing"] is True
        assert sum(i["duration_seconds"] for i in detail["intervals"]) == END - START
        assert detail["intervals"][2]["information"] == "down"

    def test_unknown_service_state_is_recorded_not_missing_history(self):
        detail = service_detail([svc_event(START, 64)], native_service(unknown=1000))
        assert [i["state"] for i in detail["intervals"]] == ["unknown"]
        assert detail["totals"]["no_recorded_data_seconds"] == 0

    def test_repeated_state_events_merge_and_irregular_intervals_sum(self):
        events = [svc_event(START + 10, 8), svc_event(START + 17, 8), svc_event(START + 503, 32),
                  svc_event(START + 999, 8)]
        detail = service_detail(events, native_service(nodata=10, ok=493 + 1, critical=496))
        assert [i["state"] for i in detail["intervals"]] == ["no_data", "ok", "critical", "ok"]
        assert detail["reconciliation"]["matches"] is True

    def test_event_before_range_is_clipped_and_marked(self):
        detail = service_detail([svc_event(START - 500, 32)], native_service(critical=1000))
        interval = detail["intervals"][0]
        assert (interval["start"], interval["clipped_start"]) == (START, True)

    def test_discrepancy_withholds_intervals_but_keeps_native_totals(self):
        detail = service_detail([svc_event(START, 8)], native_service(ok=400, nodata=600))
        assert detail["intervals_available"] is False
        assert detail["intervals"] == []
        assert detail["reconciliation"]["differences"]
        assert "native" in detail["notice"]
        assert detail["totals"]["known_seconds"] == 400

    def test_maintenance_is_a_subdivision_not_extra_time(self):
        detail = service_detail([svc_event(START, 8)], native_service(ok=750, sched={"ok": 250}))
        ok = detail["totals"]["states"][0]
        assert (ok["seconds"], ok["scheduled_seconds"], ok["unscheduled_seconds"]) == (1000, 250, 750)
        assert detail["totals"]["known_seconds"] == ok["seconds"]

    def test_zero_denominators_are_null(self):
        detail = service_detail([initial(START)], native_service(nodata=1000))
        state = detail["totals"]["states"][0]
        assert state["pct_of_known"] is None
        assert state["pct_of_total"] == 0.0

    def test_contradictory_native_durations_are_rejected(self):
        with pytest.raises(AvailabilityError):
            service_detail([], native_service(ok=5000))

    def test_host_detail_uses_host_key_and_states(self):
        native = {"name": "web", "time_up": 600, "time_down": 400, "time_unreachable": 0,
                  "scheduled_time_up": 0, "scheduled_time_down": 0, "scheduled_time_unreachable": 0,
                  "time_indeterminate_nodata": 0, "time_indeterminate_notrunning": 0}
        events = [host_event(START, 1), host_event(START + 600, 2)]
        with patch(CGI, fake_cgi(availability={"host": native}, changes=events)):
            detail = re_.read_availability_detail("web", None, START, END)
        assert [i["state"] for i in detail["intervals"]] == ["up", "down"]
        assert detail["reconciliation"]["matches"]

    def test_truncated_state_changes_are_not_a_complete_timeline(self):
        events = [svc_event(START + i, 8 if i % 2 else 32) for i in range(60)]
        with patch.object(re_, "PAGE_SIZE", 10), patch.object(re_, "MAX_EVENTS", 30), \
                patch(CGI, fake_cgi(availability={"service": native_service(ok=1000)}, changes=events)):
            detail = re_.read_availability_detail("web", "http", START, END)
        assert detail["complete"] is False
        assert detail["intervals"] == []
        assert "narrow" in detail["notice"]


class TestNagiosDowntimeAndMissingObjects:
    def test_state_continues_through_nagios_downtime_and_totals_exclude_it(self):
        events = [svc_event(START, 32)]
        shown = {"service": native_service(critical=400, notrunning=600)}
        assumed = {"service": native_service(critical=1000)}
        with patch(CGI, fake_cgi(availability=shown, changes=events, assumed=assumed)):
            detail = re_.read_availability_detail("web", "http", START, END)
        assert detail["totals"]["known_seconds"] == 400
        assert detail["totals"]["nagios_not_running_seconds"] == 600
        assert detail["intervals_available"] is True
        assert detail["reconciliation"]["nagios_not_running_seconds"] == 600
        assert "600 s Nagios was not running" in detail["notice"]

    def test_unknown_object_is_not_found_not_an_upstream_error(self, logged_in_client, db_session, seeded_permissions):
        with patch(CGI, fake_cgi(availability={})):
            response = logged_in_client.get(f"{DETAIL}?hostname=nosuch&service=http")
        assert response.status_code == 404
        assert "No such host or service" in response.get_json()["message"]


class TestPaging:
    def test_pages_until_short_page_with_bounded_requests(self):
        rows = [svc_event(START + i, 32) for i in range(25)]
        calls = []

        def call(key, params, deadline):
            calls.append(params["start"])
            return envelope({"alertlist": rows[params["start"]:params["start"] + params["count"]]})
        with patch.object(re_, "PAGE_SIZE", 10), patch(CGI, call):
            got, complete = re_.fetch_list("alertlist", {}, "alertlist")
        assert (len(got), complete, calls) == (25, True, [0, 10, 20])

    def test_request_limit_marks_incomplete(self):
        rows = [svc_event(START + i, 32) for i in range(100)]
        with patch.object(re_, "PAGE_SIZE", 10), patch.object(re_, "MAX_REQUESTS", 3), \
                patch(CGI, fake_cgi(alerts=rows)):
            got, complete = re_.fetch_list("alertlist", {}, "alertlist")
        assert (len(got), complete) == (30, False)

    def test_malformed_payload_is_a_source_error(self):
        with patch(CGI, lambda *a: envelope({"alertlist": "nope"})):
            with pytest.raises(AvailabilityError):
                re_.fetch_list("alertlist", {}, "alertlist")

    def test_failed_envelope_is_rejected(self):
        with patch(CGI, lambda *a: {"result": {"type_code": 6}, "data": {}}):
            with pytest.raises(AvailabilityError):
                re_.fetch_list("alertlist", {}, "alertlist")


class TestAlertPolicy:
    def test_default_params_are_hard_problem_events(self):
        params = re_.alert_params(START, END)
        assert params["statetypes"] == "hard"
        assert params["hoststates"] == "down unreachable"
        assert params["servicestates"] == "warning critical unknown"
        assert params["objecttypes"] == "host service"

    def test_recoveries_and_both_state_types_are_explicit(self):
        params = re_.alert_params(START, END, state_type="both", include_recoveries=True, scope="service")
        assert params["statetypes"] == "hard soft"
        assert "ok" in params["servicestates"].split()
        assert params["objecttypes"] == "service"

    def test_initial_entries_are_dropped_unless_requested(self):
        rows = [initial(START), svc_event(START + 5, 32)]
        with patch(CGI, fake_cgi(alerts=rows)):
            events, _ = re_.fetch_alerts(START, END)
            with_initial, _ = re_.fetch_alerts(START, END, include_initial=True)
        assert len(events) == 1 and len(with_initial) == 2

    def test_hard_is_one_and_soft_is_two(self):
        with patch(CGI, fake_cgi(alerts=[svc_event(START, 32, 1), svc_event(START + 1, 32, 2)])):
            events, _ = re_.fetch_alerts(START, END, state_type="both")
        assert [e["state_type"] for e in events] == ["hard", "soft"]


class TestSummary:
    def events(self):
        rows = [svc_event(START + i, 32, host="b", desc="x") for i in range(3)]
        rows += [svc_event(START + 10, 16, host="a", desc="y"), svc_event(START + 11, 32, host="a", desc="y"),
                 svc_event(START + 12, 32, host="c", desc="z"), svc_event(START + 13, 32, host="c", desc="z"),
                 svc_event(START + 14, 32, host="d", desc="z"), host_event(START + 15, 2, host="a"),
                 svc_event(START + 16, 8, host="b", desc="x")]
        with patch(CGI, fake_cgi(alerts=rows)):
            return re_.fetch_alerts(START, END, include_recoveries=True)[0]

    def test_ranking_is_deterministic_with_tied_identities(self):
        result = re_.summarize_alerts(self.events(), by="service")
        order = [(r["hostname"], r["service"], r["total"]) for r in result["ranking"]]
        assert order == [("b", "x", 3), ("a", "y", 2), ("c", "z", 2), ("a", None, 1), ("d", "z", 1)]
        assert [r["rank"] for r in result["ranking"]] == [1, 2, 3, 4, 5]

    def test_recoveries_are_separate_and_distinct_counts_are_correct(self):
        totals = re_.summarize_alerts(self.events(), by="service")["totals"]
        assert totals["problem_events"] == 9
        assert totals["recovery_events"] == 1
        assert totals["distinct_hosts"] == 4
        assert totals["distinct_objects"] == 5
        assert totals["host_problem_events"] == 1 and totals["service_problem_events"] == 8

    def test_by_host_merges_services_and_top_is_limited(self):
        result = re_.summarize_alerts(self.events(), by="host", limit=2)
        assert [(r["hostname"], r["total"]) for r in result["top"]] == [("a", 3), ("b", 3)]
        assert len(result["ranking"]) == 4


class TestHistogram:
    def test_hour_has_96_zero_filled_quarter_hour_buckets(self, monkeypatch):
        monkeypatch.setenv("TZ", "UTC"); time.tzset()
        ev = [{"timestamp": 3600 * 5 + 20 * 60, "state": "CRITICAL"}]
        result = re_.histogram(ev, "hour")
        assert len(result["buckets"]) == 96
        assert result["buckets"][5 * 4 + 1]["label"] == "05:15"
        assert result["buckets"][5 * 4 + 1]["total"] == 1
        assert result["total"] == 1 == sum(b["total"] for b in result["buckets"])

    @pytest.mark.parametrize("breakdown,size", [("month", 12), ("day_of_month", 31), ("weekday", 7), ("hour", 96)])
    def test_all_four_breakdowns_have_stable_buckets(self, breakdown, size):
        assert len(re_.bucket_labels(breakdown)) == size
        assert re_.histogram([], breakdown)["total"] == 0

    def test_series_and_buckets_agree(self, monkeypatch):
        monkeypatch.setenv("TZ", "UTC"); time.tzset()
        ev = [{"timestamp": 86400 * i, "state": "CRITICAL" if i % 2 else "DOWN"} for i in range(1, 8)]
        result = re_.histogram(ev, "weekday")
        for state, counts in result["series"].items():
            assert sum(counts) == sum(b["states"].get(state, 0) for b in result["buckets"])

    def test_weekday_zero_is_sunday_like_core(self, monkeypatch):
        monkeypatch.setenv("TZ", "UTC"); time.tzset()
        assert re_.bucket_index(3 * 86400, "weekday") == 0   # 1970-01-04 was a Sunday
        assert re_.bucket_index(4 * 86400, "weekday") == 1

    def test_dst_repeated_hour_counts_twice_and_skipped_hour_is_zero(self, monkeypatch):
        monkeypatch.setenv("TZ", "America/New_York"); time.tzset()
        try:
            fall_a, fall_b = 1_730_611_800, 1_730_615_400      # 2024-11-03 01:30 EDT and 01:30 EST
            assert re_.bucket_index(fall_a, "hour") == re_.bucket_index(fall_b, "hour") == 6
            spring = [1_710_053_999, 1_710_054_000]            # 01:59:59 EST then 03:00 EDT
            indexes = {re_.bucket_index(t, "hour") for t in spring}
            assert not any(8 <= i < 12 for i in indexes)       # nothing lands in the skipped 02:xx
        finally:
            monkeypatch.setenv("TZ", "UTC"); time.tzset()


class TestRoutes:
    def test_detail_requires_hostname_and_bounds_range(self, logged_in_client, db_session, seeded_permissions):
        assert logged_in_client.get(DETAIL).status_code == 400
        too_long = f"{DETAIL}?hostname=web&period=custom&start=2024-01-01&end=2024-06-01"
        assert logged_in_client.get(too_long).status_code == 400

    def test_detail_route_returns_period_zone_and_source(self, logged_in_client, db_session, seeded_permissions):
        with patch(CGI, fake_cgi(availability={"service": native_service(ok=1)}, changes=[])):
            response = logged_in_client.get(f"{DETAIL}?hostname=web&service=http&period=custom&start=2024-01-01&end=2024-01-02")
        data = response.get_json()["data"]
        assert response.status_code == 200
        assert data["period"]["time_zone"]["name"] and data["source"] == "Nagios archive"
        assert data["object"] == {"hostname": "web", "service": "http"}

    def test_summary_route_policy_and_upstream_error(self, logged_in_client, db_session, seeded_permissions):
        with patch(CGI, fake_cgi(alerts=[svc_event(START, 32)])):
            data = logged_in_client.get(SUMMARY).get_json()["data"]
        assert data["filters"]["policy"].startswith("HARD problem events")
        assert data["totals"]["problem_events"] == 1 and data["complete"] is True
        with patch(CGI, side_effect=AvailabilityError("x")):
            assert logged_in_client.get(SUMMARY).status_code == 502

    def test_summary_incomplete_suppresses_totals(self, logged_in_client, db_session, seeded_permissions):
        rows = [svc_event(START + i, 32) for i in range(40)]
        with patch.object(re_, "PAGE_SIZE", 10), patch.object(re_, "MAX_EVENTS", 20), patch(CGI, fake_cgi(alerts=rows)):
            data = logged_in_client.get(SUMMARY).get_json()["data"]
        assert data["complete"] is False and data["totals"] is None and data["ranking"] == []

    @pytest.mark.parametrize("query", ["scope=bad", "state_type=bad", "states=bogus", "by=bad"])
    def test_summary_rejects_invalid_filters(self, logged_in_client, db_session, seeded_permissions, query):
        assert logged_in_client.get(f"{SUMMARY}?{query}").status_code == 400

    def test_histogram_route_and_invalid_breakdown(self, logged_in_client, db_session, seeded_permissions):
        with patch(CGI, fake_cgi(alerts=[svc_event(START, 32)])):
            data = logged_in_client.get(f"{HISTOGRAM}?breakdown=month").get_json()["data"]
        assert data["recurring"] is True and len(data["buckets"]) == 12 and data["total"] == 1
        assert logged_in_client.get(f"{HISTOGRAM}?breakdown=year").status_code == 400

    def test_new_routes_require_login_and_permission(self, client, db_session):
        for url in (DETAIL, SUMMARY, HISTOGRAM):
            assert client.get(url).status_code == 401


class TestListFiltersAndReaders:
    def test_alert_filters_become_native_options_and_default_is_unfiltered(self, logged_in_client, db_session, seeded_permissions):
        target = "app.api.system.report.request_alerts_range"
        with patch(target, return_value=[]) as alerts:
            logged_in_client.get("/api/system/report/alerts")
            assert alerts.call_args.kwargs["extra"] == {}
            logged_in_client.get("/api/system/report/alerts?scope=service&state_type=both&states=critical")
        extra = alerts.call_args.kwargs["extra"]
        assert extra["objecttypes"] == "service" and extra["statetypes"] == "hard soft"
        assert extra["servicestates"] == "critical"

    def test_invalid_alert_and_notification_filters_are_rejected(self, logged_in_client, db_session, seeded_permissions):
        assert logged_in_client.get("/api/system/report/alerts?states=bogus").status_code == 400
        assert logged_in_client.get("/api/system/report/notifications?notification_types=bogus").status_code == 400
        assert logged_in_client.get("/api/system/report/notifications?scope=bad").status_code == 400

    def test_notification_contact_and_type_filters(self, logged_in_client, db_session, seeded_permissions):
        target = "app.api.system.report.request_notifications_range"
        with patch(target, return_value=[]) as notifications, \
                patch("app.api.system.report.request_notification_count_range", return_value={}):
            logged_in_client.get("/api/system/report/notifications?contact=ops&notification_types=down,critical")
        extra = notifications.call_args.kwargs["extra"]
        assert extra["contactname"] == "ops"
        assert extra["hostnotificationtypes"] == "down" and extra["servicenotificationtypes"] == "critical"

    def test_single_host_availability_reads_the_host_object(self, app):
        from app.nagios import notifications
        with app.app_context(), patch.object(notifications, "_request_archive", return_value={"name": "web"}) as call:
            rows = notifications.request_host_availability_range(1, 2, hostname="web")
        assert rows == [{"name": "web"}]
        assert call.call_args.kwargs["result_key"] == "host"
        assert call.call_args.args[1]["assumeinitialstate"] == "false"

    def test_summary_uses_one_request_per_page_not_per_row(self, logged_in_client, db_session, seeded_permissions):
        rows = [svc_event(START + i, 32, host=f"h{i}") for i in range(1200)]
        calls = []
        base = fake_cgi(alerts=rows)

        def counted(key, params, deadline):
            calls.append(params["start"])
            return base(key, params, deadline)
        with patch(CGI, counted):
            data = logged_in_client.get(f"{SUMMARY}?by=host").get_json()["data"]
        assert data["totals"]["problem_events"] == 1200 and calls == [0, 500, 1000]


class TestRecurrenceDrilldown:
    def test_alerts_filter_to_a_histogram_bucket(self, logged_in_client, db_session, seeded_permissions, monkeypatch):
        monkeypatch.setenv("TZ", "UTC"); time.tzset()
        sunday = 1_699_747_200  # 2023-11-12 00:00 UTC
        alerts = [svc_event(sunday, 32), svc_event(sunday + 86400, 32)]
        with patch("app.api.system.report.request_alerts_range", return_value=alerts), \
                patch("app.api.system.report.request_alert_count_range", return_value={}):
            data = logged_in_client.get("/api/system/report/alerts?recurrence=weekday:0").get_json()["data"]
            bad = logged_in_client.get("/api/system/report/alerts?recurrence=weekday:9")
        assert [a["timestamp"] for a in data["alerts"]] == [sunday]
        assert bad.status_code == 400


class TestCapturedNativeShape:
    """A real Core 4.5.11 answer (lab capture) reconciles with its own native durations."""

    def test_lab_capture_reconciles_with_native_availability(self):
        import json
        from pathlib import Path
        fixture = json.loads((Path(__file__).parent.parent / "fixtures" / "archivejson_core_4_5_11.json").read_text())
        window = fixture["window_seconds"]
        events = fixture["statechangelist_service"]["statechangelist"]
        with patch(CGI, fake_cgi(availability={"service": fixture["availability_service"]}, changes=events)):
            detail = re_.read_availability_detail("lab-host", "SSH", window["start"], window["end"])
        assert detail["reconciliation"]["matches"], detail["reconciliation"]
        assert [(i["state"], i["duration_seconds"]) for i in detail["intervals"]] == [
            ("no_data", 182742), ("critical", 76398)]
        assert detail["intervals"][0]["unknown_onset"] is True


class TestSourceFailuresAndRemovedObjects:
    """Auth, timeout and removed-object behavior of the new readers and routes."""

    def _get(self, client, url):
        return client.get(url)

    @pytest.mark.parametrize("failure", ["timeout", "unauthorized", "redirect", "not_json"])
    def test_upstream_failures_are_sanitized_502s(self, logged_in_client, db_session, seeded_permissions, failure):
        import requests

        class Response:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return {}

        def fake_get(url, **kwargs):
            if failure == "timeout":
                raise requests.Timeout("secret-host.example connect timed out")
            resp = Response()
            if failure == "unauthorized":
                resp.status_code = 401
                def raise_for_status():
                    raise requests.HTTPError("401 for http://nagios.internal/cgi-bin/archivejson.cgi?password=hunter2")
                resp.raise_for_status = raise_for_status
            elif failure == "redirect":
                resp.status_code = 302
            else:
                def not_json():
                    raise ValueError("<html>login</html>")
                resp.json = not_json
            return resp

        with patch("app.nagios.service_availability.requests.get", fake_get):
            for url in (SUMMARY, HISTOGRAM, f"{DETAIL}?hostname=web&service=http"):
                response = logged_in_client.get(url)
                assert response.status_code == 502, (failure, url)
                message = response.get_json()["message"]
                assert "hunter2" not in message and "nagios.internal" not in message and "secret-host" not in message

    def test_events_for_an_object_missing_from_inventory_are_still_summarized(self, logged_in_client, db_session, seeded_permissions):
        # History of a removed device remains in the archive; reports do not consult the inventory.
        with patch(CGI, fake_cgi(alerts=[svc_event(START, 32, host="removed-host")])):
            data = logged_in_client.get(f"{SUMMARY}?by=host").get_json()["data"]
        assert [r["hostname"] for r in data["ranking"]] == ["removed-host"]

    def test_host_report_lists_only_hosts_nagios_returns_not_removed_inventory(self, logged_in_client, db_session, seeded_permissions):
        from tests.support.seed_helpers import _make_host
        _make_host(db_session, "removed-host")
        db_session.session.commit()
        rows = [{"hostname": "kept", "time_up": 10, "time_down": 0, "time_unreachable": 0}]
        with patch("app.api.system.report.request_host_availability_range", return_value=rows):
            data = logged_in_client.get("/api/system/report/hosts-by-os").get_json()["data"]
        names = [h["hostname"] for group in data["by_os"] for h in group["hosts"]]
        assert names == ["kept"]

    def test_multiple_contacts_for_one_event_remain_separate_deliveries(self, logged_in_client, db_session, seeded_permissions):
        ts = 1_700_000_000_000
        notifications = [
            {"timestamp": ts, "object_type": 2, "host_name": "web", "description": "http", "state": 32,
             "contact_name": "ops", "notification_type": 1, "plugin_output": "down"},
            {"timestamp": ts, "object_type": 2, "host_name": "web", "description": "http", "state": 32,
             "contact_name": "oncall", "notification_type": 1, "plugin_output": "down"},
        ]
        with patch("app.api.system.report.request_notifications_range", return_value=notifications) as call, \
                patch("app.api.system.report.request_notification_count_range", return_value={}):
            data = logged_in_client.get("/api/system/report/notifications?contact=ops").get_json()["data"]
        assert [n["contact"] for n in data["notifications"]] == ["ops", "oncall"]
        assert call.call_args.kwargs["extra"]["contactname"] == "ops"
