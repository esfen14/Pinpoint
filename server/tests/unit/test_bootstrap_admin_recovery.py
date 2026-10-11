"""Regression tests for the operator-only bootstrap-admin recovery command."""

from datetime import datetime, timedelta, timezone

import sqlalchemy as sa

from app.system_models import ActivityLog, User, UserStatus
from tests.unit.test_management import _make_user


OLD_PASSWORD = "InstallerPass1!abc"
TEMPORARY_PASSWORD = "TemporaryPass1!xyz"


def _bootstrap_admin(db_session, admin_role, *, needs_setup=False,
                     status=UserStatus.ACTIVE):
    """Create the earliest account, matching production bootstrap ordering."""
    user = _make_user(
        db_session,
        admin_role,
        "admin-r3cover@pinpoint.lan",
        password=OLD_PASSWORD,
        status=status,
    )
    user.Created_At = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user.Needs_Setup = needs_setup
    db_session.session.commit()
    return user


def _invoke(app, monkeypatch, password=TEMPORARY_PASSWORD):
    """Run recovery with a private prompt stub and return its CLI result."""
    from app.api.commands.seed import recover_bootstrap_admin_command

    calls = []

    def prompt(*args, **kwargs):
        calls.append((args, kwargs))
        return password

    monkeypatch.setattr("app.api.commands.seed.click.prompt", prompt)
    result = app.test_cli_runner().invoke(recover_bootstrap_admin_command)
    return result, calls


class TestRecoverBootstrapAdmin:
    """The command changes only a confidently identified bootstrap password."""

    def test_recovers_sole_earliest_account_and_writes_sanitized_audit_log(
        self, app, db_session, admin_role, monkeypatch
    ):
        bootstrap = _bootstrap_admin(db_session, admin_role)
        later = _make_user(db_session, admin_role, "later@example.com")
        before = (bootstrap.Email, bootstrap.Status, bootstrap.RoleID, bootstrap.Needs_Setup)

        result, prompts = _invoke(app, monkeypatch)

        assert result.exit_code == 0, result.output
        assert TEMPORARY_PASSWORD not in result.output
        assert len(prompts) == 1
        assert prompts[0][1]["hide_input"] is True
        assert prompts[0][1]["confirmation_prompt"] is True
        db_session.session.refresh(bootstrap)
        db_session.session.refresh(later)
        assert bootstrap.check_password(TEMPORARY_PASSWORD)
        assert bootstrap.Must_Change_Password is True
        assert (bootstrap.Email, bootstrap.Status, bootstrap.RoleID, bootstrap.Needs_Setup) == before
        assert later.check_password("TestPass1!abc")
        actions = db_session.session.scalars(sa.select(ActivityLog.Action_Type)).all()
        assert any("Recovered bootstrap administrator password" in action for action in actions)
        assert all(TEMPORARY_PASSWORD not in action for action in actions)

    def test_preserves_needs_setup_before_first_run_setup(
        self, app, db_session, admin_role, monkeypatch
    ):
        bootstrap = _bootstrap_admin(db_session, admin_role, needs_setup=True)

        result, _ = _invoke(app, monkeypatch)

        assert result.exit_code == 0, result.output
        db_session.session.refresh(bootstrap)
        assert bootstrap.Needs_Setup is True
        assert bootstrap.Must_Change_Password is True
        assert bootstrap.check_password(TEMPORARY_PASSWORD)

    def test_recovers_after_first_run_setup(self, app, db_session, admin_role, monkeypatch):
        bootstrap = _bootstrap_admin(db_session, admin_role, needs_setup=False)

        result, _ = _invoke(app, monkeypatch)

        assert result.exit_code == 0, result.output
        db_session.session.refresh(bootstrap)
        assert bootstrap.Needs_Setup is False
        assert bootstrap.Must_Change_Password is True

    def test_preserves_inactive_or_suspended_status(self, app, db_session, admin_role, monkeypatch):
        bootstrap = _bootstrap_admin(db_session, admin_role, status=UserStatus.SUSPENDED)

        result, _ = _invoke(app, monkeypatch)

        assert result.exit_code == 0, result.output
        db_session.session.refresh(bootstrap)
        assert bootstrap.Status is UserStatus.SUSPENDED
        assert bootstrap.check_password(TEMPORARY_PASSWORD)

    def test_rejects_policy_invalid_password_without_change(
        self, app, db_session, admin_role, monkeypatch
    ):
        bootstrap = _bootstrap_admin(db_session, admin_role)

        result, _ = _invoke(app, monkeypatch, password="weak")

        assert result.exit_code != 0
        db_session.session.refresh(bootstrap)
        assert bootstrap.check_password(OLD_PASSWORD)
        assert bootstrap.Must_Change_Password is False

    def test_rejects_mismatched_confirmation_without_change(self, app, db_session, admin_role):
        from app.api.commands.seed import recover_bootstrap_admin_command

        bootstrap = _bootstrap_admin(db_session, admin_role)
        result = app.test_cli_runner().invoke(
            recover_bootstrap_admin_command,
            input=f"{TEMPORARY_PASSWORD}\nDifferentPass1!xyz\n",
        )

        assert result.exit_code != 0
        db_session.session.refresh(bootstrap)
        assert bootstrap.check_password(OLD_PASSWORD)
        assert bootstrap.Must_Change_Password is False

    def test_rejects_missing_bootstrap_without_prompt(self, app, db_session, monkeypatch):
        result, prompts = _invoke(app, monkeypatch)

        assert result.exit_code != 0
        assert "could not be identified" in result.output.lower()
        assert prompts == []

    def test_rejects_ambiguous_earliest_accounts_without_change(
        self, app, db_session, admin_role, monkeypatch
    ):
        first = _bootstrap_admin(db_session, admin_role)
        second = _make_user(db_session, admin_role, "same-time@example.com")
        second.Created_At = first.Created_At
        db_session.session.commit()

        result, prompts = _invoke(app, monkeypatch)

        assert result.exit_code != 0
        assert "could not be identified" in result.output.lower()
        assert prompts == []
        db_session.session.refresh(first)
        db_session.session.refresh(second)
        assert first.check_password(OLD_PASSWORD)
        assert second.check_password("TestPass1!abc")
