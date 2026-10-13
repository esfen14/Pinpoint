"""Notification policy API authorization, validation and atomic Nagios apply."""
from unittest.mock import patch

import pytest
from app.system_models import NotificationPolicy

URL = "/api/system/notification-policy"


def policy(client):
    response = client.get(URL)
    assert response.status_code == 200
    return response.get_json()["data"]


def test_requires_permission(limited_client):
    assert limited_client.get(URL).status_code == 403
    assert limited_client.put(URL, json={}).status_code == 403


def test_defaults_and_local_time(logged_in_client):
    data = policy(logged_in_client)
    assert data["quietHours"] == []
    assert data["hostOptions"] == ["d", "u", "r", "f", "s"]
    assert data["serviceOptions"] == ["w", "u", "c", "r", "f", "s"]
    assert data["renotifyInterval"] == 30
    assert data["timeZone"] == "Nagios server local time"


@pytest.mark.parametrize("change, field", [
    ({"quietHours": [{"weekday": "monday", "start": "25:00", "end": "09:00"}]}, "start"),
    ({"quietHours": [{"weekday": "monday", "start": "22:00", "end": "07:00"}]}, "start"),
    ({"quietHours": [{"weekday": "noday", "start": "01:00", "end": "02:00"}]}, "weekday"),
    ({"quietHours": [{"weekday": "monday", "start": "01:00", "end": "03:00"},
                     {"weekday": "monday", "start": "02:00", "end": "04:00"}]}, "quietHours"),
    ({"hostOptions": ["x"]}, "hostOptions"),
    ({"serviceOptions": ["x"]}, "serviceOptions"),
    ({"renotifyInterval": 1441}, "renotifyInterval"),
])
def test_invalid_fields(logged_in_client, change, field):
    data = policy(logged_in_client)
    data.update(change)
    response = logged_in_client.put(URL, json=data)
    assert response.status_code == 400
    assert field in response.get_json()["message"]


def test_stale_and_failed_apply_roll_back(logged_in_client, db_session):
    data = policy(logged_in_client)
    data["renotifyInterval"] = 10
    with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status", return_value=("failed", "Nagios rejected policy")):
        response = logged_in_client.put(URL, json=data)
    assert response.status_code == 422
    assert "Nagios rejected policy" in response.get_json()["message"]
    db_session.session.expire_all()
    assert db_session.session.get(NotificationPolicy, 1).Renotify_Interval == 30
    data["version"] = 0
    assert logged_in_client.put(URL, json=data).status_code == 409


def test_save_persists_and_regenerates(logged_in_client):
    data = policy(logged_in_client)
    data["renotifyInterval"] = 15
    data["quietHours"] = [{"weekday": "monday", "start": "09:00", "end": "10:00"}]
    with patch("app.network_discovery.create_host_cfg.regenerate_and_apply_config_status", return_value=("applied", "ok")) as apply:
        response = logged_in_client.put(URL, json=data)
    assert response.status_code == 200
    assert response.get_json()["data"]["version"] == 2
    assert policy(logged_in_client)["quietHours"] == data["quietHours"]
    apply.assert_called_once()
