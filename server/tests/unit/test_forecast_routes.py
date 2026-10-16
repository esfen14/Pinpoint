"""
tests/unit/test_forecast_routes.py — GET /api/system/forecast (app/api/system/forecast.py).

Returns the stored forecasts, soonest crossing first, with the window, sample count and slope
that make each number explainable. Readable with system.dashboard or system.services.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.system_models import Permission, ResourceForecast, Role, RolePermission, User, UserStatus

URL = "/api/system/forecast"


def add_forecast(db_session, host, hours_from_now, service="ncpa-disk-5693", metric="disk/logical/|/used_percent", kind="warning"):
    db_session.session.add(ResourceForecast(
        Hostname=host, Service=service, Metric=metric, Kind=kind, Threshold=80.0,
        Crossing_At=(datetime.now(timezone.utc) + timedelta(hours=hours_from_now)).replace(tzinfo=None),
        Slope_Per_Hour=0.3, R_Squared=0.97, Sample_Count=70, Window_Hours=72.0,
        Current_Value=61.5, Unit="%", Computed_At=datetime.now(timezone.utc).replace(tzinfo=None),
    ))
    db_session.session.commit()


class TestAccess:

    def test_requires_login(self, client, db_session):
        assert client.get(URL).status_code in (401, 302)

    def test_a_user_without_either_permission_is_refused(self, limited_client):
        assert limited_client.get(URL).status_code == 403

    @pytest.mark.parametrize("permission", ["system.dashboard", "system.services"])
    def test_either_view_permission_is_enough(self, client, db_session, seeded_permissions, permission):
        if permission not in seeded_permissions:
            seeded_permissions[permission] = Permission(Name=permission, Description=permission)
            db_session.session.add(seeded_permissions[permission])
            db_session.session.flush()
        role = Role(Name="Viewer2", Is_Active=True, Description="one view permission")
        db_session.session.add(role)
        db_session.session.flush()
        db_session.session.add(RolePermission(RoleID=role.RoleID, PermissionID=seeded_permissions[permission].PermissionID))
        user = User(First_Name="V", Last_Name="W", Email="v@example.com", Status=UserStatus.ACTIVE, RoleID=role.RoleID)
        user.set_password("ViewerPass1!")
        db_session.session.add(user)
        db_session.session.commit()
        assert client.post("/api/user/login", json={"email": "v@example.com", "password": "ViewerPass1!"}).status_code == 200

        assert client.get(URL).status_code == 200


class TestList:

    def test_empty_is_an_empty_list(self, logged_in_client):
        body = logged_in_client.get(URL).get_json()
        assert body["success"] is True
        assert body["data"] == {"forecasts": []}

    def test_sorted_by_soonest_crossing_with_the_basis(self, logged_in_client, db_session):
        add_forecast(db_session, "later", 200)
        add_forecast(db_session, "sooner", 20, metric="memory/virtual/percent", service="ncpa-memory-5693", kind="critical")
        add_forecast(db_session, "middle", 90)

        items = logged_in_client.get(URL).get_json()["data"]["forecasts"]

        assert [i["hostname"] for i in items] == ["sooner", "middle", "later"]
        first = items[0]
        assert first["service_name"] == "ncpa-memory-5693" and first["metric"] == "memory/virtual/percent"
        assert first["kind"] == "critical" and first["threshold"] == 80.0
        assert first["slope_per_hour"] == 0.3 and first["sample_count"] == 70 and first["window_hours"] == 72.0
        assert first["r_squared"] == 0.97 and first["current_value"] == 61.5 and first["unit"] == "%"
        # The browser must read these as UTC, so the offset is always present.
        assert first["crossing_at"].endswith("+00:00") and first["computed_at"].endswith("+00:00")

    def test_filter_by_host(self, logged_in_client, db_session):
        add_forecast(db_session, "a", 10)
        add_forecast(db_session, "b", 20)
        items = logged_in_client.get(f"{URL}?hostname=b").get_json()["data"]["forecasts"]
        assert [i["hostname"] for i in items] == ["b"]

    def test_limit_is_bounded(self, logged_in_client, db_session):
        for n in range(5):
            add_forecast(db_session, f"h{n}", n + 1)
        items = logged_in_client.get(f"{URL}?limit=2").get_json()["data"]["forecasts"]
        assert [i["hostname"] for i in items] == ["h0", "h1"]

    @pytest.mark.parametrize("value", ["0", "-1", "abc", "5000"])
    def test_bad_limit_is_rejected(self, logged_in_client, value):
        assert logged_in_client.get(f"{URL}?limit={value}").status_code == 400
