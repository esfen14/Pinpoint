"""Provision a repeatable restricted-role account without printing credentials."""

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke import Client


def require_env(name):
    """Return a required secret environment variable without logging it."""
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"missing required environment variable: {name}")
    return value


def call_ok(api, method, path, body=None, statuses=(200,)):
    """Call one API route and return its data or stop with a sanitized error."""
    status, response = api.call(method, path, body)
    if status not in statuses or not response.get("success"):
        message = response.get("message") or "request failed"
        raise SystemExit(f"{method} {path} failed (HTTP {status}): {message}")
    return response.get("data") or {}


def main():
    """Create or reset one active Staff account and require its password change."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--email", default="qa-restricted@example.com")
    args = parser.parse_args()

    admin_email = require_env("PINPOINT_ADMIN_USER")
    admin_password = require_env("PINPOINT_ADMIN_PASSWORD")
    temporary_password = require_env("PINPOINT_RESTRICTED_PASSWORD")

    api = Client(args.base_url)
    call_ok(api, "POST", "/api/user/login", {
        "email": admin_email,
        "password": admin_password,
    })

    roles = call_ok(api, "GET", "/api/user/roles/options").get("items", [])
    staff = next((role for role in roles if role.get("name") == "Staff"), None)
    if staff is None:
        raise SystemExit("the seeded active Staff role is missing")

    accounts = call_ok(
        api, "GET", f"/api/user/accounts?search={args.email}&per_page=100"
    ).get("items", [])
    matches = [item for item in accounts if item.get("email") == args.email]
    if len(matches) > 1:
        raise SystemExit("more than one restricted QA account matched")

    body = {
        "first_name": "QA",
        "last_name": "Restricted",
        "email": args.email,
        "password": temporary_password,
        "confirm_password": temporary_password,
        "status": "Active",
        "role_id": staff["id"],
        "receive_email_alerts": False,
    }
    if matches:
        call_ok(api, "PUT", f"/api/user/accounts/{matches[0]['id']}", body)
        action = "reset"
    else:
        body["require_password_change"] = True
        call_ok(api, "POST", "/api/user/accounts", body, statuses=(201,))
        action = "created"

    print(f"restricted QA account {action}; credentials remain in the private state directory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
