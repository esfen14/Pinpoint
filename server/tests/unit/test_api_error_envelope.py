"""
Tests for the JSON error envelope on API errors that Flask or Flask-Login
raise before a route runs (app/api/error_handlers.py).
"""
import pytest


class TestSignedOut:
    @pytest.mark.parametrize("method, path", [
        ("get", "/api/system/dashboard/summary"),
        ("get", "/api/user/me"),
        ("post", "/api/user/logout"),
        ("get", "/api/plugin"),
    ])
    def test_protected_route_returns_json_401(self, client, db_session, method, path):
        resp = getattr(client, method)(path)

        assert resp.status_code == 401
        assert resp.content_type == "application/json"
        assert resp.get_json() == {"success": False, "message": "You must be signed in to do that."}


class TestUnknownPath:
    @pytest.mark.parametrize("path", [
        "/api",
        "/api/",
        "/api/system/dashbord/summary",
        "/api/nothing-here",
    ])
    def test_unknown_api_path_returns_json_404(self, client, path):
        resp = client.get(path)

        assert resp.status_code == 404
        assert resp.content_type == "application/json"
        assert resp.get_json() == {"success": False, "message": "Not found."}

    @pytest.mark.parametrize("path", ["/dashbord", "/apis/system"])
    def test_unknown_non_api_path_keeps_html_404(self, client, path):
        resp = client.get(path)

        assert resp.status_code == 404
        assert resp.content_type.startswith("text/html")

    def test_wrong_method_is_still_405(self, client):
        resp = client.get("/api/user/login")

        assert resp.status_code == 405
        assert resp.content_type.startswith("text/html")
