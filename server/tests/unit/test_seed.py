"""
tests/unit/test_seed.py — Tests for the `flask seed` and `flask init-production`
CLI commands in app/api/commands/seed.py.
"""
import sqlalchemy as sa

from app.api.commands.seed import (
    BUILTIN_ROLE_NAME,
    LEGACY_BUILTIN_ROLE_NAME,
    LEGACY_BUILTIN_ROLE_NAME_FALLBACK,
    PERMISSIONS,
    init_production_command,
    missing_permissions,
    seed_command,
    seed_system_settings,
    upgrade_builtin_role_name,
    sync_permissions,
    sync_permissions_command,
    warn_if_permissions_missing,
)
from app.system_models import (
    Permission, Role, RolePermission, SystemSettings, User, UserStatus,
)


class TestSeedSystemSettings:

    def test_creates_singleton_row_with_defaults(self, db_session):
        seed_system_settings()

        row = db_session.session.get(SystemSettings, 1)
        assert row is not None
        assert row.Scan_Frequency == 6
        assert row.Log_Retention_Days == 30
        assert row.Diagnostic_History_Retention_Days == 90

    def test_does_not_overwrite_existing_row(self, db_session):
        db_session.session.add(SystemSettings(Id=1, Scan_Frequency=12))
        db_session.session.commit()

        seed_system_settings()

        assert db_session.session.get(SystemSettings, 1).Scan_Frequency == 12
        count = db_session.session.scalar(sa.select(sa.func.count()).select_from(SystemSettings))
        assert count == 1

    def test_seed_command_creates_settings(self, app, db_session):
        result = app.test_cli_runner().invoke(seed_command)

        assert "Seed failed" not in result.output
        assert db_session.session.get(SystemSettings, 1) is not None


class TestInitProductionCommand:

    ADMIN_EMAIL = "admin-7f3a2@pinpoint.lan"
    PASSWORD = "S3cure-Passw0rd!"

    def invoke(self, app, password=PASSWORD, email=ADMIN_EMAIL):
        return app.test_cli_runner().invoke(
            init_production_command,
            ["--admin-email", email, "--password-stdin"],
            input=password,
        )

    def test_creates_single_active_admin_and_reference_data(self, app, db_session):
        result = self.invoke(app, password=self.PASSWORD + "\n")

        assert result.exit_code == 0, result.output
        users = db_session.session.scalars(sa.select(User)).all()
        assert len(users) == 1
        admin = users[0]
        assert admin.Email == self.ADMIN_EMAIL
        assert admin.Status == UserStatus.ACTIVE
        assert admin.Role.Name == "Super Admin"
        # Trailing newline from the pipe is not part of the password.
        assert admin.check_password(self.PASSWORD)

        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(Permission)) == len(PERMISSIONS)
        assert db_session.session.get(SystemSettings, 1) is not None

    def test_creates_no_test_users(self, app, db_session):
        self.invoke(app)

        emails = db_session.session.scalars(sa.select(User.Email)).all()
        assert not any(email.endswith("@test.com") for email in emails)

    def test_refuses_when_users_exist(self, app, db_session):
        assert self.invoke(app).exit_code == 0

        result = self.invoke(app, email="second@pinpoint.lan")

        assert result.exit_code != 0
        assert "already exist" in result.output
        count = db_session.session.scalar(sa.select(sa.func.count()).select_from(User))
        assert count == 1

    def test_rejects_short_password(self, app, db_session):
        result = self.invoke(app, password="short")

        assert result.exit_code != 0
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(User)) == 0

    def test_rejects_invalid_email(self, app, db_session):
        result = self.invoke(app, email="not-an-email")

        assert result.exit_code != 0
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(User)) == 0

    def test_requires_password_stdin_flag(self, app, db_session):
        result = app.test_cli_runner().invoke(
            init_production_command, ["--admin-email", self.ADMIN_EMAIL], input=self.PASSWORD
        )

        assert result.exit_code != 0
        assert db_session.session.scalar(sa.select(sa.func.count()).select_from(User)) == 0


def select_permission(name):
    return sa.select(Permission).where(Permission.Name == name)


class TestSyncPermissions:

    def _seed_old_install(self, db_session):
        """An install whose permission list predates system.hosts.edit."""
        from app.api.commands.seed import seed_permissions, seed_roles
        seed_permissions()
        seed_roles()
        perm = db_session.session.scalar(
            sa.select(Permission).where(Permission.Name == "system.hosts.edit")
        )
        db_session.session.execute(
            sa.delete(RolePermission).where(RolePermission.PermissionID == perm.PermissionID)
        )
        db_session.session.execute(
            sa.delete(Permission).where(Permission.PermissionID == perm.PermissionID)
        )
        db_session.session.commit()

    def test_adds_missing_permission_and_grants_administrator(self, app, db_session):
        self._seed_old_install(db_session)
        assert missing_permissions() == ["system.hosts.edit"]

        added, granted = sync_permissions()

        assert added == ["system.hosts.edit"]
        assert granted == ["system.hosts.edit"]
        assert missing_permissions() == []

    def test_sync_adds_recheck_for_an_install_that_predates_check_now(self, app, db_session):
        """An existing install gets system.recheck from `flask sync-permissions`, granted to Administrator only."""
        from app.api.commands.seed import seed_permissions, seed_roles
        seed_permissions()
        seed_roles()
        perm = db_session.session.scalar(select_permission("system.recheck"))
        db_session.session.execute(sa.delete(RolePermission).where(RolePermission.PermissionID == perm.PermissionID))
        db_session.session.execute(sa.delete(Permission).where(Permission.PermissionID == perm.PermissionID))
        db_session.session.commit()
        assert missing_permissions() == ["system.recheck"]

        added, granted = sync_permissions()

        assert added == ["system.recheck"] and granted == ["system.recheck"]
        holders = db_session.session.scalars(
            sa.select(Role.Name)
            .join(RolePermission, RolePermission.RoleID == Role.RoleID)
            .join(Permission, Permission.PermissionID == RolePermission.PermissionID)
            .where(Permission.Name == "system.recheck")
        ).all()
        assert holders == ["Super Admin"]

    def test_second_run_changes_nothing(self, app, db_session):
        self._seed_old_install(db_session)
        sync_permissions()

        assert sync_permissions() == ([], [])

    def test_does_not_grant_other_roles(self, app, db_session):
        self._seed_old_install(db_session)
        sync_permissions()

        holders = db_session.session.scalars(
            sa.select(Role.Name)
            .join(RolePermission, RolePermission.RoleID == Role.RoleID)
            .join(Permission, Permission.PermissionID == RolePermission.PermissionID)
            .where(Permission.Name == "system.hosts.edit")
        ).all()
        assert holders == ["Super Admin"]

    def test_cli_command_reports_changes(self, app, db_session):
        self._seed_old_install(db_session)

        result = app.test_cli_runner().invoke(sync_permissions_command)

        assert result.exit_code == 0, result.output
        assert "Permissions added: system.hosts.edit" in result.output

    def test_startup_warning_names_missing_permission(self, app, db_session):
        self._seed_old_install(db_session)
        messages = []

        class Log:
            def error(self, msg, *args): messages.append(msg % args)
            def warning(self, msg, *args): messages.append(msg % args)

        warn_if_permissions_missing(Log())

        assert any("system.hosts.edit" in m and "sync-permissions" in m for m in messages)


# ==========================================================
# PERMISSIONS STAY IN STEP WITH THE ROUTES
# ==========================================================

class TestPermissionList:

    def test_plugin_configure_is_retired(self):
        from app.api.commands.seed import PERMISSIONS
        assert "plugin.configure" not in PERMISSIONS

    def test_every_permission_a_route_requires_is_seeded(self):
        """A route guarded by a permission nobody can be granted would be unreachable."""
        import re
        from pathlib import Path
        from app.api.commands.seed import PERMISSIONS

        required = set()
        for path in (Path(__file__).resolve().parents[2] / "app").rglob("*.py"):
            if path.name == "permissions.py":      # the decorator's own docs use a placeholder name
                continue
            required.update(re.findall(r"require_permission\(\s*['\"]([\w.]+)['\"]", path.read_text(encoding="utf-8")))

        assert required, "no require_permission calls found; the search is broken"
        assert sorted(required - set(PERMISSIONS)) == []


# ==========================================================
# BUILT-IN ROLE RENAME: Administrator -> Super Admin
# ==========================================================

def _seed_legacy_install(db_session):
    """A pre-rename install: an 'Administrator' role holding one permission and
    one assigned user, plus a Staff role for contrast."""
    from app.system_models import UserStatus, Permission, Role, RolePermission, User

    admin = Role(Name="Administrator", Description="System Administrator", Is_Active=True)
    staff = Role(Name="Staff", Description="Regular Staff", Is_Active=True)
    db_session.session.add_all([admin, staff])
    db_session.session.flush()

    perm = Permission(Name="system.dashboard", Description="x")
    db_session.session.add(perm)
    db_session.session.commit()

    db_session.session.add(RolePermission(RoleID=admin.RoleID, PermissionID=perm.PermissionID))
    user = User(
        First_Name="Legacy", Last_Name="Admin", Email="legacy@example.com",
        Status=UserStatus.ACTIVE, RoleID=admin.RoleID,
    )
    user.set_password("Password123!")
    db_session.session.add(user)
    db_session.session.commit()
    return admin, user, perm


class TestBuiltInRoleRename:

    def test_upgrade_renames_legacy_role_and_keeps_identity(self, db_session):
        admin, user, perm = _seed_legacy_install(db_session)
        role_id = admin.RoleID

        result = upgrade_builtin_role_name()

        assert result == {"renamed": True, "reason": "renamed"}
        db_session.session.refresh(admin)
        assert admin.Name == BUILTIN_ROLE_NAME
        assert admin.RoleID == role_id                       # identity preserved
        assert admin.Description == "System Administrator"
        db_session.session.refresh(user)
        assert user.RoleID == role_id                        # user retained
        held = db_session.session.scalars(
            sa.select(RolePermission.PermissionID).where(RolePermission.RoleID == role_id)
        ).all()
        assert held == [perm.PermissionID]                    # permissions retained

    def test_upgrade_is_idempotent(self, db_session):
        admin, _user, _perm = _seed_legacy_install(db_session)
        assert upgrade_builtin_role_name()["renamed"] is True
        result = upgrade_builtin_role_name()
        assert result == {"renamed": False, "reason": "no legacy role"}
        db_session.session.refresh(admin)
        assert admin.Name == BUILTIN_ROLE_NAME

    def test_upgrade_runs_through_sync_permissions(self, db_session):
        admin, _user, _perm = _seed_legacy_install(db_session)
        sync_permissions()
        db_session.session.refresh(admin)
        assert admin.Name == BUILTIN_ROLE_NAME

    def test_upgrade_keeps_a_preexisting_super_admin_separate(self, db_session):
        legacy, legacy_user, _perm = _seed_legacy_install(db_session)
        legacy_id = legacy.RoleID
        existing = Role(Name="Super Admin", Description="Unrelated", Is_Active=True)
        db_session.session.add(existing)
        db_session.session.commit()
        existing_id = existing.RoleID

        result = upgrade_builtin_role_name()

        assert result.get("renamed") is False and result.get("conflict") is True
        db_session.session.refresh(legacy)
        db_session.session.refresh(existing)
        # The pre-existing role keeps its name and identity...
        assert existing.Name == BUILTIN_ROLE_NAME and existing.RoleID == existing_id
        # ...and the legacy role keeps its own identity under a distinct name.
        assert legacy.Name == LEGACY_BUILTIN_ROLE_NAME_FALLBACK and legacy.RoleID == legacy_id
        # No user reassigned to the other role.
        db_session.session.refresh(legacy_user)
        assert legacy_user.RoleID == legacy_id

    def test_seed_roles_after_upgrade_does_not_duplicate(self, db_session):
        from app.api.commands.seed import seed_roles, seed_permissions
        _seed_legacy_install(db_session)
        upgrade_builtin_role_name()
        seed_permissions()
        seed_roles()
        names = db_session.session.scalars(sa.select(Role.Name)).all()
        assert names.count(BUILTIN_ROLE_NAME) == 1

    def test_fresh_seed_creates_super_admin_not_administrator(self, app, db_session):
        app.test_cli_runner().invoke(seed_command)
        roles = db_session.session.scalars(sa.select(Role.Name)).all()
        assert BUILTIN_ROLE_NAME in roles
        assert LEGACY_BUILTIN_ROLE_NAME not in roles
