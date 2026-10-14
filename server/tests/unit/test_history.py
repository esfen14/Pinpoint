"""
tests/unit/test_history.py
=====================
Tests for app/api/system/history.py.

Routes tested:
  GET /api/system/history/alerts
  GET /api/system/history/alerts/detail
  GET /api/system/history/notifications
  GET /api/system/history/notifications/detail

Nagios archivejson calls (request_alerts_range, request_notifications_range)
are mocked in all tests so no live Nagios instance is needed.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

# Patch targets inside history.py
_ALERTS_RANGE    = "app.api.system.history.request_alerts_range"
_NOTIFS_RANGE    = "app.api.system.history.request_notifications_range"

# ---------------------------------------------------------------------------
# Sample Nagios payloads
# ---------------------------------------------------------------------------

FAKE_ALERTS = [
    {
        "hostname": "webserver",
        "service_description": "http-80-TCP",
        "state": "CRITICAL",
        "last_state": "OK",
        "state_type": "hard",
        "timestamp": 1700001000,
        "duration_seconds": 3600,
        "plugin_output": "HTTP CRITICAL - Connection refused",
    },
    {
        "hostname": "dbserver",
        "service_description": None,
        "state": "DOWN",
        "last_state": "UP",
        "state_type": "hard",
        "timestamp": 1700002000,
        "duration_seconds": 7200,
        "plugin_output": "PING CRITICAL - 100% packet loss",
    },
    {
        "hostname": "fileserver",
        "service_description": "disk-0-TCP",
        "state": "WARNING",
        "last_state": "OK",
        "state_type": "soft",
        "timestamp": 1700003000,
        "duration_seconds": 300,
        "plugin_output": "DISK WARNING - free space low",
    },
    {
        "hostname": "webserver",
        "service_description": "ssh-22-TCP",
        "state": "OK",
        "last_state": "CRITICAL",
        "state_type": "hard",
        "timestamp": 1700004000,
        "duration_seconds": 60,
        "plugin_output": "SSH OK - recovered",
    },
]

FAKE_NOTIFICATIONS = [
    {
        "hostname": "webserver",
        "service_description": "http-80-TCP",
        "notification_reason": "CRITICAL",
        "contact": "admin",
        "notificationmethod": "email",
        "timestamp": 1700001100,
        "output": "HTTP CRITICAL - Connection refused on port 80",
    },
    {
        "hostname": "dbserver",
        "service_description": None,
        "notification_reason": "DOWN",
        "contact": "admin,ops",
        "notificationmethod": "email",
        "timestamp": 1700002100,
        "output": "Host dbserver is DOWN",
    },
    {
        "hostname": "fileserver",
        "service_description": "disk-0-TCP",
        "notification_reason": "WARNING",
        "contact": "admin",
        "notificationmethod": "sms",
        "timestamp": 1700003100,
        "output": "DISK WARNING on fileserver",
    },
]


def test_exact_event_locator_and_links(logged_in_client, db_session):
    alerts = [
        {"hostname": "webserver", "service_description": "http-80-TCP", "state": state,
         "timestamp": ts, "state_type": "hard", "plugin_output": state}
        for ts, state in [(1700001000, "CRITICAL"), (1700001080, "OK"), (1700001100, "CRITICAL")]
    ]
    notifications = [
        {"hostname": "webserver", "service_description": "http-80-TCP", "timestamp": ts,
         "notification_reason": "CRITICAL", "contact": contact, "output": contact}
        for ts, contact in [(1700001010, "alice"), (1700001110, "bob")]
    ]

    def fetch(rows):
        def selected(start, end, hostname=None, service=None):
            return [row for row in rows if start <= row["timestamp"] <= end
                    and (not hostname or row["hostname"] == hostname)
                    and (not service or row["service_description"] == service)]
        return selected

    with patch(_ALERTS_RANGE, side_effect=fetch(alerts)), patch(_NOTIFS_RANGE, side_effect=fetch(notifications)):
        detail = logged_in_client.get('/api/system/history/notifications/detail', query_string={
            'hostname': 'webserver', 'service': 'http-80-TCP', 'timestamp': 1700001110,
        }).get_json()['data']
        assert detail['linked_alert']['timestamp'] == 1700001100
        assert detail['linked_alert']['event_id']
        assert detail['event_id']
        for route, event_id in [('alerts', detail['linked_alert']['event_id']),
                                ('notifications', detail['event_id'])]:
            response = logged_in_client.get(f'/api/system/history/{route}',
                                            query_string={'event_id': event_id, 'preset': '24h'})
            assert response.status_code == 200
            assert response.get_json()['data']['items'][0]['event_id'] == event_id
            assert response.get_json()['data']['total'] == 1
        alert_detail = logged_in_client.get('/api/system/history/alerts/detail', query_string={
            'hostname': 'webserver', 'service': 'http-80-TCP', 'timestamp': 1700001100,
            'new_state': 'CRITICAL',
        }).get_json()['data']
        assert [n['event_id'] for n in alert_detail['linked_notifications']] == [detail['event_id']]
        assert logged_in_client.get('/api/system/history/alerts',
                                    query_string={'event_id': '1700001100:' + '0' * 64}).get_json()['data']['total'] == 0
        assert logged_in_client.get('/api/system/history/alerts',
                                    query_string={'event_id': 'bad'}).status_code == 400


def test_link_host_and_no_match(logged_in_client, db_session):
    host = {'hostname': 'dbserver', 'timestamp': 1700002000, 'state': 'DOWN', 'state_type': 'hard'}
    notifs = [{'hostname': 'dbserver', 'timestamp': 1700002010,
               'notification_reason': 'DOWN', 'contact': 'ops'},
              {'hostname': 'dbserver', 'service_description': 'disk', 'timestamp': 1700002011,
               'notification_reason': 'DOWN', 'contact': 'ops'}]
    with patch(_ALERTS_RANGE, return_value=[host]), patch(_NOTIFS_RANGE, return_value=notifs):
        response = logged_in_client.get('/api/system/history/notifications/detail', query_string={
            'hostname': 'dbserver', 'timestamp': 1700002010,
        })
        assert response.get_json()['data']['linked_alert']['event_id']
        response = logged_in_client.get('/api/system/history/notifications/detail', query_string={
            'hostname': 'dbserver', 'service': 'disk', 'timestamp': 1700002011,
        })
        assert response.get_json()['data']['linked_alert'] is None


# ==========================================================
# Auth / permission guards
# ==========================================================

class TestHistoryAuthGuards:
    READ_ENDPOINTS = [
        "/api/system/history/alerts",
        "/api/system/history/alerts/detail",
        "/api/system/history/notifications",
        "/api/system/history/notifications/detail",
    ]

    @pytest.mark.parametrize("url", READ_ENDPOINTS)
    def test_requires_login(self, client, db_session, url):
        assert client.get(url).status_code in (401, 302)

    @pytest.mark.parametrize("url", READ_ENDPOINTS)
    def test_requires_permission(self, limited_client, db_session, url):
        assert limited_client.get(url).status_code == 403


# ==========================================================
# Shared list range contract
# ==========================================================

@pytest.mark.parametrize("route,archive", [
    ("alerts", _ALERTS_RANGE), ("notifications", _NOTIFS_RANGE),
])
def test_custom_datetime_bounds_use_utc_inclusive_seconds(logged_in_client, db_session, route, archive):
    params = {"start_date": "2024-01-01T08:00:00+08:00",
              "end_date": "2024-01-01T02:00:00Z"}
    with patch(archive, return_value=[]) as fetch:
        response = logged_in_client.get(f"/api/system/history/{route}", query_string=params)
    assert response.status_code == 200
    assert any(call.args[:2] == (1704067200, 1704074400) for call in fetch.call_args_list)


@pytest.mark.parametrize("route", ["alerts", "notifications"])
@pytest.mark.parametrize("params", [
    {"start_date": "2024-01-01T00:00:00Z"},
    {"end_date": "2024-01-01T00:00:00Z"},
    {"start_date": "2024-01-01T00:00:00", "end_date": "2024-01-02T00:00:00Z"},
    {"start_date": "2024-01-02T00:00:00Z", "end_date": "2024-01-01T00:00:00Z"},
    {"start_date": "2024-02-30", "end_date": "2024-03-01"},
    {"start_date": "2024-01-01T00:00:00Z", "end_date": "2024-01-01"},
])
def test_invalid_custom_bounds_rejected(logged_in_client, db_session, route, params):
    assert logged_in_client.get(f"/api/system/history/{route}", query_string=params).status_code == 400


# ==========================================================
# GET /api/system/history/alerts
# ==========================================================

class TestAlertsHistory:

    def test_returns_paginated_list(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_nagios_failure_returns_502(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=None):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h")
        assert resp.status_code == 502

    def test_default_time_range_is_last_24h(self, logged_in_client, db_session):
        """No params → defaults to last 24 hours, returns 200."""
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts")
        assert resp.status_code == 200

    def test_invalid_preset_returns_400(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=5m")
        assert resp.status_code == 400

    def test_invalid_per_page_returns_400(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h&per_page=10")
        assert resp.status_code == 400

    def test_invalid_order_returns_400(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h&order=random")
        assert resp.status_code == 400

    def test_invalid_ack_filter_returns_400(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(
                "/api/system/history/alerts?preset=24h&ack_filter=maybe"
            )
        assert resp.status_code == 400

    def test_invalid_page_returns_400(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h&page=0")
        assert resp.status_code == 400

    @pytest.mark.parametrize("preset", ["1h", "6h", "24h", "7d", "30d"])
    def test_all_valid_presets(self, logged_in_client, db_session, preset):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(f"/api/system/history/alerts?preset={preset}")
        assert resp.status_code == 200

    def test_custom_date_range(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(
                "/api/system/history/alerts?start_date=2024-01-01&end_date=2024-01-31"
            )
        assert resp.status_code == 200

    def test_type_filter_host(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h&type=host")
        items = resp.get_json()["data"]["items"]
        assert all(i["type"] == "host" for i in items)

    def test_type_filter_service(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h&type=service")
        items = resp.get_json()["data"]["items"]
        assert all(i["type"] == "service" for i in items)

    def test_new_state_filter(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(
                "/api/system/history/alerts?preset=24h&new_state=CRITICAL"
            )
        items = resp.get_json()["data"]["items"]
        assert all(i["new_state"] == "CRITICAL" for i in items)

    def test_state_type_filter(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(
                "/api/system/history/alerts?preset=24h&state_type=soft"
            )
        items = resp.get_json()["data"]["items"]
        assert all(i["state_type"] == "soft" for i in items)

    def test_default_sort_is_timestamp_desc(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h")
        items = resp.get_json()["data"]["items"]
        if len(items) > 1:
            timestamps = [i["timestamp"] for i in items]
            assert timestamps == sorted(timestamps, reverse=True)

    def test_sort_asc(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(
                "/api/system/history/alerts?preset=24h&order=asc&sort_by=timestamp"
            )
        items = resp.get_json()["data"]["items"]
        if len(items) > 1:
            timestamps = [i["timestamp"] for i in items]
            assert timestamps == sorted(timestamps)

    def test_pagination_per_page(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h&per_page=25")
        data = resp.get_json()["data"]
        assert len(data["items"]) <= 25

    def test_item_shape(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h")
        items = resp.get_json()["data"]["items"]
        assert len(items) > 0
        item = items[0]
        for key in (
            "timestamp", "type", "hostname", "service_name",
            "previous_state", "new_state", "state_type",
            "duration_seconds", "plugin_output", "acknowledged",
        ):
            assert key in item, f"Missing key: {key}"

    def test_ack_filter_acknowledged(self, logged_in_client, db_session):
        """Records in AckHistory for ACKNOWLEDGED action appear when ack_filter=acknowledged."""
        from app.system_models import AckHistory, AckAction
        from datetime import datetime, timezone
        with db_session.session.begin_nested():
            db_session.session.add(AckHistory(
                Hostname="webserver",
                Service_Name="http-80-TCP",
                Action=AckAction.ACKNOWLEDGED,
                Actioned_At=datetime.now(timezone.utc),
                ActorUserID=None,
                Comment="test ack",
            ))
        db_session.session.commit()

        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(
                "/api/system/history/alerts?preset=24h&ack_filter=acknowledged"
            )
        items = resp.get_json()["data"]["items"]
        assert all(i["acknowledged"] for i in items)

    def test_ack_filter_unacknowledged(self, logged_in_client, db_session):
        """When no acks exist, ack_filter=unacknowledged returns all items."""
        with patch(_ALERTS_RANGE, return_value=FAKE_ALERTS):
            resp = logged_in_client.get(
                "/api/system/history/alerts?preset=24h&ack_filter=unacknowledged"
            )
        items = resp.get_json()["data"]["items"]
        assert all(not i["acknowledged"] for i in items)

    def test_real_nagios_alert_shape(self, logged_in_client, db_session):
        # archivejson sends numeric states, a millisecond timestamp, the host
        # under "name"/"host_name", and no last_state or duration.
        real = [
            {"timestamp": 1791291918000, "object_type": 1, "name": "h1",
             "state_type": 2, "state": 2, "plugin_output": "PING CRITICAL"},
            {"timestamp": 1791291919000, "object_type": 2, "host_name": "h2",
             "description": "http-80-tcp", "state_type": 1, "state": 32, "plugin_output": "HTTP"},
        ]
        with patch(_ALERTS_RANGE, return_value=real):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h&sort_by=hostname&order=asc")
        assert resp.status_code == 200
        items = resp.get_json()["data"]["items"]
        assert [(i["hostname"], i["type"], i["new_state"], i["state_type"], i["timestamp"]) for i in items] == [
            ("h1", "host", "DOWN", "hard", 1791291918),
            ("h2", "service", "CRITICAL", "soft", 1791291919),
        ]

    def test_empty_nagios_response_returns_empty_list(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=[]):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 0

    def test_nagios_dict_response_normalised(self, logged_in_client, db_session):
        """Nagios may return a dict keyed by string index instead of a list."""
        dict_alerts = {str(i): a for i, a in enumerate(FAKE_ALERTS)}
        with patch(_ALERTS_RANGE, return_value=dict_alerts):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == len(FAKE_ALERTS)

    def test_output_truncated_to_200_chars(self, logged_in_client, db_session):
        long_output = "x" * 500
        alert = [{**FAKE_ALERTS[0], "plugin_output": long_output}]
        with patch(_ALERTS_RANGE, return_value=alert):
            resp = logged_in_client.get("/api/system/history/alerts?preset=24h")
        item = resp.get_json()["data"]["items"][0]
        assert len(item["plugin_output"]) == 200


@pytest.mark.parametrize("key", ["type", "hostname", "service_name", "previous_state",
                                      "new_state", "state_type", "duration_seconds", "plugin_output", "duration"])
@pytest.mark.parametrize("order", ["asc", "desc"])
def test_alert_column_sort_and_timestamp_ties(logged_in_client, db_session, key, order):
    rows = [{**FAKE_ALERTS[0], "timestamp": 100},
            {**FAKE_ALERTS[0], "timestamp": 300},
            {**FAKE_ALERTS[1], "timestamp": 200, "state_type": "soft"}]
    with patch(_ALERTS_RANGE, return_value=rows):
        response = logged_in_client.get("/api/system/history/alerts", query_string={"sort_by": key, "order": order})
    assert response.status_code == 200
    items = response.get_json()["data"]["items"]
    field = "duration_seconds" if key == "duration" else key
    values = [i[field] for i in items]
    assert values == sorted(values, key=lambda v: v.lower() if isinstance(v, str) else v or "" if v is None else v,
                            reverse=order == "desc")
    assert [i["timestamp"] for i in items if i["timestamp"] in (100, 300)] == [300, 100]


# ==========================================================
# GET /api/system/history/alerts/detail
# ==========================================================

class TestAlertsHistoryDetail:

    def _base_alert(self):
        return FAKE_ALERTS[0]  # webserver / http-80-TCP / CRITICAL

    def test_returns_detail_for_known_alert(self, logged_in_client, db_session):
        alert = self._base_alert()
        with patch(_ALERTS_RANGE, return_value=[alert]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    f"?hostname={alert['hostname']}"
                    f"&timestamp={alert['timestamp']}"
                    f"&new_state={alert['state']}"
                    f"&service={alert['service_description']}"
                )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["hostname"] == alert["hostname"]
        assert data["new_state"] == alert["state"].upper()

    def test_missing_hostname_returns_400(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=[]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail?timestamp=1700001000&new_state=CRITICAL"
                )
        assert resp.status_code == 400

    def test_missing_timestamp_returns_400(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=[]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail?hostname=webserver&new_state=CRITICAL"
                )
        assert resp.status_code == 400

    def test_nagios_failure_returns_502(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=None):
            resp = logged_in_client.get(
                "/api/system/history/alerts/detail"
                "?hostname=webserver&timestamp=1700001000&new_state=CRITICAL"
            )
        assert resp.status_code == 502

    def test_alert_not_found_returns_404(self, logged_in_client, db_session):
        with patch(_ALERTS_RANGE, return_value=[]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    "?hostname=ghost&timestamp=9999999999&new_state=DOWN"
                )
        assert resp.status_code == 404

    def test_response_shape(self, logged_in_client, db_session):
        alert = self._base_alert()
        with patch(_ALERTS_RANGE, return_value=[alert]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    f"?hostname={alert['hostname']}"
                    f"&timestamp={alert['timestamp']}"
                    f"&new_state={alert['state']}"
                    f"&service={alert['service_description']}"
                )
        data = resp.get_json()["data"]
        for key in (
            "hostname", "service_name", "timestamp", "type",
            "previous_state", "new_state", "state_type",
            "duration_seconds", "plugin_output",
            "acknowledged", "ack", "recovery_duration",
            "linked_notifications",
        ):
            assert key in data, f"Missing key: {key}"

    def test_plugin_output_is_not_truncated(self, logged_in_client, db_session):
        long_output = "y" * 500
        alert = {**self._base_alert(), "plugin_output": long_output}
        with patch(_ALERTS_RANGE, return_value=[alert]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    f"?hostname={alert['hostname']}"
                    f"&timestamp={alert['timestamp']}"
                    f"&new_state={alert['state']}"
                    f"&service={alert['service_description']}"
                )
        # Full output should be present (not truncated to 200 as the list is)
        assert len(resp.get_json()["data"]["plugin_output"]) == 500

    def test_linked_notifications_populated(self, logged_in_client, db_session):
        alert = self._base_alert()
        notif = FAKE_NOTIFICATIONS[0]
        with patch(_ALERTS_RANGE, return_value=[alert]):
            with patch(_NOTIFS_RANGE, return_value=[notif]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    f"?hostname={alert['hostname']}"
                    f"&timestamp={alert['timestamp']}"
                    f"&new_state={alert['state']}"
                    f"&service={alert['service_description']}"
                )
        linked = resp.get_json()["data"]["linked_notifications"]
        assert isinstance(linked, list)

    def test_recovery_duration_set_when_state_ok(self, logged_in_client, db_session):
        recovery_alert = {
            "hostname": "webserver",
            "service_description": "http-80-TCP",
            "state": "OK",
            "last_state": "CRITICAL",
            "state_type": "hard",
            "timestamp": 1700010000,
            "duration_seconds": 1800,
            "plugin_output": "HTTP OK - recovered",
        }
        with patch(_ALERTS_RANGE, return_value=[recovery_alert]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    "?hostname=webserver&timestamp=1700010000"
                    "&new_state=OK&service=http-80-TCP"
                )
        data = resp.get_json()["data"]
        assert data["recovery_duration"] == 1800

    def test_recovery_duration_none_for_non_ok_state(self, logged_in_client, db_session):
        alert = self._base_alert()
        with patch(_ALERTS_RANGE, return_value=[alert]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    f"?hostname={alert['hostname']}"
                    f"&timestamp={alert['timestamp']}"
                    f"&new_state={alert['state']}"
                    f"&service={alert['service_description']}"
                )
        assert resp.get_json()["data"]["recovery_duration"] is None

    def test_host_level_alert_type_is_host(self, logged_in_client, db_session):
        alert = FAKE_ALERTS[1]  # dbserver / no service / DOWN
        with patch(_ALERTS_RANGE, return_value=[alert]):
            with patch(_NOTIFS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/alerts/detail"
                    f"?hostname={alert['hostname']}"
                    f"&timestamp={alert['timestamp']}"
                    f"&new_state={alert['state']}"
                )
        assert resp.get_json()["data"]["type"] == "host"


# ==========================================================
# Acknowledgement episode association (list, filter, detail)
# ==========================================================

@pytest.mark.parametrize("service", [None, "http-80-TCP"])
def test_acknowledgement_belongs_only_to_its_problem_episode(logged_in_client, db_session, admin_user, service):
    from app.system_models import AckHistory, AckAction, User, UserStatus

    hostname = "webserver"
    healthy = "OK" if service else "UP"
    problem = "CRITICAL" if service else "DOWN"
    base = 1_700_000_000
    events = [
        {"hostname": hostname, "service_description": service, "timestamp": base + offset,
         "state": state, "last_state": previous, "state_type": "hard", "plugin_output": state}
        for offset, state, previous in [
            (10, problem, healthy), (20, "WARNING" if service else "UNREACHABLE", problem),
            (40, healthy, problem), (50, problem, healthy), (70, healthy, problem),
            (80, problem, healthy), (110, healthy, problem),
        ]
    ]
    other = User(First_Name="Other", Last_Name="Operator", Email="other@example.com",
                 Status=UserStatus.ACTIVE, RoleID=admin_user.RoleID)
    other.set_password("temporary")
    db_session.session.add(other)
    db_session.session.flush()
    for offset, action, actor, comment in [
        (25, AckAction.ACKNOWLEDGED, admin_user.UserID, "first"),
        (41, AckAction.AUTO_RESOLVED, None, None),
        (60, AckAction.ACKNOWLEDGED, other.UserID, "second"),
        (65, AckAction.UNACKNOWLEDGED, other.UserID, None),
        (71, AckAction.AUTO_RESOLVED, None, None),
        (90, AckAction.ACKNOWLEDGED, other.UserID, "third"),
        (111, AckAction.AUTO_RESOLVED, None, None),
    ]:
        db_session.session.add(AckHistory(
            Hostname=hostname, Service_Name=service, Action=action,
            Actioned_At=datetime.fromtimestamp(base + offset, timezone.utc),
            ActorUserID=actor, Comment=comment,
        ))
    db_session.session.commit()

    with patch(_ALERTS_RANGE, return_value=events), patch(_NOTIFS_RANGE, return_value=[]):
        listed = logged_in_client.get("/api/system/history/alerts?preset=24h")
        acked = logged_in_client.get("/api/system/history/alerts?preset=24h&ack_filter=acknowledged")
        unacked = logged_in_client.get("/api/system/history/alerts?preset=24h&ack_filter=unacknowledged")
        details = {}
        for event in events:
            response = logged_in_client.get("/api/system/history/alerts/detail", query_string={
                "hostname": hostname, "timestamp": event["timestamp"],
                "new_state": event["state"], **({"service": service} if service else {}),
            })
            assert response.status_code == 200
            details[event["timestamp"] - base] = response.get_json()["data"]

    assert listed.status_code == acked.status_code == unacked.status_code == 200
    flags = {item["timestamp"] - base: item["acknowledged"] for item in listed.get_json()["data"]["items"]}
    assert flags == {10: True, 20: True, 40: False, 50: True, 70: False, 80: True, 110: False}
    assert {item["timestamp"] - base for item in acked.get_json()["data"]["items"]} == {10, 20, 50, 80}
    assert {item["timestamp"] - base for item in unacked.get_json()["data"]["items"]} == {40, 70, 110}
    assert details[10]["ack"]["comment"] == "first"
    assert details[10]["ack"]["acknowledged_by"] == f"{admin_user.First_Name} {admin_user.Last_Name}"
    assert details[20]["ack"]["comment"] == "first"
    assert details[50]["ack"]["comment"] == "second"
    assert details[50]["ack"]["acknowledged_by"] == "Other Operator"
    assert details[80]["ack"]["comment"] == "third"
    for offset in (40, 70, 110):
        assert details[offset]["acknowledged"] is False
        assert details[offset]["ack"] is None


def test_episode_boundaries_across_list_window_and_targets(logged_in_client, db_session):
    from app.system_models import AckHistory, AckAction

    base = 1_700_000_000
    events = [
        {"hostname": host, "service_description": service, "timestamp": base + offset,
         "state": state, "state_type": "hard", "plugin_output": state}
        for host, service, offset, state in [
            ("h", None, 10, "DOWN"), ("h", "http", 11, "CRITICAL"),
            ("h", None, 30, "DOWN"), ("h", "http", 31, "OK"),
            ("h", None, 50, "UP"), ("h", None, 60, "DOWN"),
        ]
    ]
    for host, service, offset, action, comment in [
        ("h", None, 20, AckAction.ACKNOWLEDGED, "old host"),
        ("h", None, 25, AckAction.AUTO_RESOLVED, None),
        ("h", None, 40, AckAction.ACKNOWLEDGED, "new host"),
        ("h", "http", 22, AckAction.ACKNOWLEDGED, "service only"),
    ]:
        db_session.session.add(AckHistory(
            Hostname=host, Service_Name=service, Action=action,
            Actioned_At=datetime.fromtimestamp(base + offset, timezone.utc),
            Comment=comment,
        ))
    db_session.session.commit()

    # Nagios returns a bounded list, but the annotation needs the earlier
    # transitions and the AUTO_RESOLVED boundary, not only visible rows.
    def archive(start, end, **filters):
        result = [e for e in events if start <= e["timestamp"] <= end]
        if filters.get("hostname"):
            result = [e for e in result if e["hostname"] == filters["hostname"]]
        if filters.get("service"):
            result = [e for e in result if e["service_description"] == filters["service"]]
        if start != 0 and end - start > 5:
            return [e for e in result if e["timestamp"] >= base + 30 or e["service_description"] == "http"]
        return result

    with patch(_ALERTS_RANGE, side_effect=archive), patch(_NOTIFS_RANGE, return_value=[]), \
            patch("app.api.system.history.resolve_time_range", return_value=(base + 30, base + 100)):
        listed = logged_in_client.get("/api/system/history/alerts?preset=24h")
        detail = logged_in_client.get("/api/system/history/alerts/detail",
                                      query_string={"hostname": "h", "timestamp": base + 30, "new_state": "DOWN"})
    assert listed.status_code == 200
    flags = {(i["service_name"], i["timestamp"] - base): i["acknowledged"]
             for i in listed.get_json()["data"]["items"]}
    assert flags[(None, 30)] is True
    assert flags[(None, 60)] is False
    assert flags[("http", 31)] is False
    assert detail.status_code == 200
    assert detail.get_json()["data"]["ack"]["comment"] == "new host"


# ==========================================================
# GET /api/system/history/notifications
# ==========================================================

class TestNotificationsHistory:

    def test_returns_paginated_list(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get("/api/system/history/notifications?preset=24h")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "items" in data
        assert "total" in data

    def test_nagios_failure_returns_502(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=None):
            resp = logged_in_client.get("/api/system/history/notifications?preset=24h")
        assert resp.status_code == 502

    def test_default_time_range(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get("/api/system/history/notifications")
        assert resp.status_code == 200

    def test_invalid_preset_returns_400(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get("/api/system/history/notifications?preset=99d")
        assert resp.status_code == 400

    def test_invalid_per_page_returns_400(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                "/api/system/history/notifications?preset=24h&per_page=10"
            )
        assert resp.status_code == 400

    def test_invalid_order_returns_400(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                "/api/system/history/notifications?preset=24h&order=sideways"
            )
        assert resp.status_code == 400

    @pytest.mark.parametrize("preset", ["1h", "6h", "24h", "7d", "30d"])
    def test_all_valid_presets(self, logged_in_client, db_session, preset):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                f"/api/system/history/notifications?preset={preset}"
            )
        assert resp.status_code == 200

    def test_type_filter_host(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                "/api/system/history/notifications?preset=24h&type=host"
            )
        items = resp.get_json()["data"]["items"]
        assert all(i["type"] == "host" for i in items)

    def test_type_filter_service(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                "/api/system/history/notifications?preset=24h&type=service"
            )
        items = resp.get_json()["data"]["items"]
        assert all(i["type"] == "service" for i in items)

    def test_state_filter(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                "/api/system/history/notifications?preset=24h&state=CRITICAL"
            )
        items = resp.get_json()["data"]["items"]
        assert all(i["state"] == "CRITICAL" for i in items)

    def test_contact_filter_partial_match(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                "/api/system/history/notifications?preset=24h&contact=admin"
            )
        items = resp.get_json()["data"]["items"]
        assert all("admin" in i["contact"].lower() for i in items)

    def test_default_sort_is_timestamp_desc(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get("/api/system/history/notifications?preset=24h")
        items = resp.get_json()["data"]["items"]
        if len(items) > 1:
            timestamps = [i["timestamp"] for i in items]
            assert timestamps == sorted(timestamps, reverse=True)

    def test_item_shape(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get("/api/system/history/notifications?preset=24h")
        items = resp.get_json()["data"]["items"]
        assert len(items) > 0
        item = items[0]
        for key in (
            "timestamp", "type", "hostname", "service_name",
            "state", "contact", "method", "message",
        ):
            assert key in item, f"Missing key: {key}"

    def test_message_truncated_to_200_chars(self, logged_in_client, db_session):
        long_notif = [{**FAKE_NOTIFICATIONS[0], "output": "z" * 500}]
        with patch(_NOTIFS_RANGE, return_value=long_notif):
            resp = logged_in_client.get("/api/system/history/notifications?preset=24h")
        item = resp.get_json()["data"]["items"][0]
        assert len(item["message"]) == 200

    def test_nagios_dict_response_normalised(self, logged_in_client, db_session):
        dict_notifs = {str(i): n for i, n in enumerate(FAKE_NOTIFICATIONS)}
        with patch(_NOTIFS_RANGE, return_value=dict_notifs):
            resp = logged_in_client.get("/api/system/history/notifications?preset=24h")
        assert resp.get_json()["data"]["total"] == len(FAKE_NOTIFICATIONS)

    def test_empty_response_returns_empty_list(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=[]):
            resp = logged_in_client.get("/api/system/history/notifications?preset=24h")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 0

    def test_pagination_has_correct_metadata(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=FAKE_NOTIFICATIONS):
            resp = logged_in_client.get(
                "/api/system/history/notifications?preset=24h&page=1&per_page=25"
            )
        data = resp.get_json()["data"]
        for key in ("page", "per_page", "total", "pages", "has_next", "has_prev"):
            assert key in data


@pytest.mark.parametrize("key", ["type", "hostname", "service_name", "state", "contact", "method", "message"])
@pytest.mark.parametrize("order", ["asc", "desc"])
def test_notification_column_sort_and_timestamp_ties(logged_in_client, db_session, key, order):
    rows = [{**FAKE_NOTIFICATIONS[0], "timestamp": 100},
            {**FAKE_NOTIFICATIONS[0], "timestamp": 300},
            {**FAKE_NOTIFICATIONS[1], "timestamp": 200}]
    with patch(_NOTIFS_RANGE, return_value=rows):
        response = logged_in_client.get("/api/system/history/notifications", query_string={"sort_by": key, "order": order, "source": "nagios"})
    assert response.status_code == 200
    items = response.get_json()["data"]["items"]
    values = [i[key] for i in items]
    assert values == sorted(values, key=lambda v: v.lower() if isinstance(v, str) else "", reverse=order == "desc")
    assert [i["timestamp"] for i in items if i["timestamp"] in (100, 300)] == [300, 100]


# ==========================================================
# GET /api/system/history/notifications/detail
# ==========================================================

class TestNotificationsHistoryDetail:

    def _base_notif(self):
        return FAKE_NOTIFICATIONS[0]  # webserver / http-80-TCP / CRITICAL

    def test_returns_detail_for_known_notification(self, logged_in_client, db_session):
        notif = self._base_notif()
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                    f"&service={notif['service_description']}"
                )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["hostname"] == notif["hostname"]

    def test_millisecond_timestamp_matches_the_seconds_the_list_sent(self, logged_in_client, db_session):
        raw = {"timestamp": 1_700_001_100_000, "host_name": "webserver", "description": "http-80-tcp",
               "notification_reason": "CRITICAL", "contact_name": "admin", "plugin_output": "down"}
        with patch(_NOTIFS_RANGE, return_value=[raw]), patch(_ALERTS_RANGE, return_value=[]):
            resp = logged_in_client.get(
                "/api/system/history/notifications/detail"
                "?hostname=webserver&timestamp=1700001100&service=http-80-tcp"
            )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["timestamp"] == 1700001100

    def test_missing_hostname_returns_400(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=[]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail?timestamp=1700001100"
                )
        assert resp.status_code == 400

    def test_missing_timestamp_returns_400(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=[]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail?hostname=webserver"
                )
        assert resp.status_code == 400

    def test_nagios_failure_returns_502(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=None):
            resp = logged_in_client.get(
                "/api/system/history/notifications/detail"
                "?hostname=webserver&timestamp=1700001100"
            )
        assert resp.status_code == 502

    def test_notification_not_found_returns_404(self, logged_in_client, db_session):
        with patch(_NOTIFS_RANGE, return_value=[]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    "?hostname=ghost&timestamp=9999999999"
                )
        assert resp.status_code == 404

    def test_response_shape(self, logged_in_client, db_session):
        notif = self._base_notif()
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                    f"&service={notif['service_description']}"
                )
        data = resp.get_json()["data"]
        for key in (
            "hostname", "service_name", "timestamp", "type",
            "state", "contacts", "method", "message", "linked_alert",
        ):
            assert key in data, f"Missing key: {key}"

    def test_contacts_is_list(self, logged_in_client, db_session):
        notif = self._base_notif()
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                    f"&service={notif['service_description']}"
                )
        contacts = resp.get_json()["data"]["contacts"]
        assert isinstance(contacts, list)
        assert "admin" in contacts

    def test_multiple_contacts_split_correctly(self, logged_in_client, db_session):
        """'admin,ops' in contact field → ["admin", "ops"] in contacts list."""
        notif = FAKE_NOTIFICATIONS[1]  # contact = "admin,ops"
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                )
        contacts = resp.get_json()["data"]["contacts"]
        assert "admin" in contacts
        assert "ops" in contacts

    def test_full_message_not_truncated(self, logged_in_client, db_session):
        long_msg = "m" * 500
        notif = {**self._base_notif(), "output": long_msg}
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                    f"&service={notif['service_description']}"
                )
        # Detail endpoint must return the full message, not truncated to 200
        assert len(resp.get_json()["data"]["message"]) == 500

    def test_linked_alert_present_when_nearby(self, logged_in_client, db_session):
        notif = self._base_notif()
        nearby_alert = {**FAKE_ALERTS[0], "timestamp": notif["timestamp"] - 30}
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[nearby_alert]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                    f"&service={notif['service_description']}"
                )
        linked = resp.get_json()["data"]["linked_alert"]
        assert linked is not None
        assert "timestamp" in linked
        assert "new_state" in linked

    def test_linked_alert_null_when_none_nearby(self, logged_in_client, db_session):
        notif = self._base_notif()
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                    f"&service={notif['service_description']}"
                )
        assert resp.get_json()["data"]["linked_alert"] is None

    def test_host_level_type_is_host(self, logged_in_client, db_session):
        notif = FAKE_NOTIFICATIONS[1]  # dbserver / no service
        with patch(_NOTIFS_RANGE, return_value=[notif]):
            with patch(_ALERTS_RANGE, return_value=[]):
                resp = logged_in_client.get(
                    "/api/system/history/notifications/detail"
                    f"?hostname={notif['hostname']}"
                    f"&timestamp={notif['timestamp']}"
                )
        assert resp.get_json()["data"]["type"] == "host"


class TestNagiosArchiveParameters:
    """archivejson rejects an unknown option ("Invalid option: 'service'"), which
    made every service notification/alert detail fail."""

    def test_service_filter_uses_servicedescription(self, app):
        from app.nagios.notifications import request_alerts_range, request_notifications_range

        for request_fn in (request_alerts_range, request_notifications_range):
            with app.app_context(), patch("app.nagios.notifications.requests.get") as get:
                get.return_value.json.return_value = {"data": {"alertlist": [], "notificationlist": []}}
                request_fn(1, 2, hostname="web", service="http-80-tcp")
            params = get.call_args.kwargs["params"]
            assert params["servicedescription"] == "http-80-tcp"
            assert "service" not in params
