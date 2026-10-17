"""
Tests for app/backup_restore.py and the `flask restore-backup` command.

Everything uses temporary SQLite files; no real database, service or
systemctl is touched.
"""
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from app import automation, backup_restore
from app.api.commands import restore as restore_command
from app.backup_restore import (
    RestoreError,
    backup_file_paths,
    integrity_check,
    make_safety_copy,
    resolve_backup_folder,
    restore_databases,
    service_is_active,
)

NOW = datetime(2026, 10, 17, 9, 30, tzinfo=timezone.utc)
BACKUP_NAME = "20261016-020000"


def make_db(path, value):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE sample (value TEXT)")
    conn.execute("INSERT INTO sample VALUES (?)", (value,))
    conn.commit()
    conn.close()
    return path


def read_value(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("SELECT value FROM sample").fetchone()[0]
    finally:
        conn.close()


@pytest.fixture()
def layout(tmp_path):
    """Live databases holding 'current' and a backup folder holding 'backed-up'."""
    live = tmp_path / "live"
    live.mkdir()
    backup_dir = tmp_path / "backups"
    folder = backup_dir / BACKUP_NAME
    folder.mkdir(parents=True)
    paths = [str(make_db(live / "system.db", "current")), str(make_db(live / "history.db", "current"))]
    make_db(folder / "system.db", "backed-up")
    make_db(folder / "history.db", "backed-up")
    return paths, backup_dir, folder


# ==========================================================
# VALIDATION
# ==========================================================

class TestResolveBackupFolder:
    def test_accepts_a_backup_folder(self, layout):
        _, backup_dir, folder = layout
        assert resolve_backup_folder(backup_dir, BACKUP_NAME) == folder

    @pytest.mark.parametrize("name", [
        "latest", "", "../backups/" + BACKUP_NAME, "/etc", BACKUP_NAME + "/", "2026-10-16", "2026101-020000",
        "pre-restore-" + BACKUP_NAME,
    ])
    def test_rejects_names_that_are_not_backup_folders(self, layout, name):
        _, backup_dir, _ = layout
        with pytest.raises(RestoreError):
            resolve_backup_folder(backup_dir, name)

    def test_rejects_a_folder_that_does_not_exist(self, layout):
        _, backup_dir, _ = layout
        with pytest.raises(RestoreError, match="does not exist"):
            resolve_backup_folder(backup_dir, "20200101-000000")

    def test_rejects_a_symlinked_folder(self, layout, tmp_path):
        _, backup_dir, folder = layout
        outside = tmp_path / "outside"
        outside.mkdir()
        (backup_dir / "20200101-000000").symlink_to(outside, target_is_directory=True)
        with pytest.raises(RestoreError):
            resolve_backup_folder(backup_dir, "20200101-000000")


class TestBackupFilePaths:
    def test_missing_database_file_is_refused(self, layout):
        paths, _, folder = layout
        (folder / "history.db").unlink()
        with pytest.raises(RestoreError, match="history.db"):
            backup_file_paths(folder, paths)


class TestIntegrityCheck:
    def test_good_database_passes(self, tmp_path):
        assert integrity_check(make_db(tmp_path / "ok.db", "x")) is True

    def test_text_file_fails(self, tmp_path):
        bad = tmp_path / "bad.db"
        bad.write_text("this is not a database" * 100)
        assert integrity_check(bad) is False

    def test_corrupted_pages_fail(self, tmp_path):
        path = tmp_path / "damaged.db"
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE sample (value TEXT)")
        conn.executemany("INSERT INTO sample VALUES (?)", [("row %d" % i * 20,) for i in range(500)])
        conn.commit()
        conn.close()
        data = bytearray(path.read_bytes())
        data[4096 * 2:4096 * 2 + 200] = b"\xff" * 200
        path.write_bytes(bytes(data))
        assert integrity_check(path) is False

    def test_does_not_modify_or_create_the_file(self, tmp_path):
        assert integrity_check(tmp_path / "missing.db") is False
        assert not (tmp_path / "missing.db").exists()


class TestServiceIsActive:
    def test_active_when_systemctl_succeeds(self):
        result = subprocess.CompletedProcess([], 0)
        assert service_is_active(run=lambda *a, **k: result) is True

    def test_inactive_when_systemctl_fails(self):
        result = subprocess.CompletedProcess([], 3)
        assert service_is_active(run=lambda *a, **k: result) is False

    def test_no_systemctl_counts_as_inactive(self):
        def missing(*args, **kwargs):
            raise FileNotFoundError("systemctl")
        assert service_is_active(run=missing) is False

    def test_timeout_counts_as_inactive(self):
        def slow(*args, **kwargs):
            raise subprocess.TimeoutExpired("systemctl", 10)
        assert service_is_active(run=slow) is False


# ==========================================================
# RESTORE
# ==========================================================

class TestRestoreDatabases:
    def test_replaces_both_databases_and_keeps_a_safety_copy(self, layout):
        paths, backup_dir, folder = layout

        backup_folder, safety_folder = restore_databases(paths, backup_dir, BACKUP_NAME, NOW)

        assert backup_folder == folder
        assert [read_value(path) for path in paths] == ["backed-up", "backed-up"]
        assert read_value(safety_folder / "system.db") == "current"
        assert read_value(safety_folder / "history.db") == "current"
        assert safety_folder.parent == backup_dir

    def test_safety_copy_is_ignored_by_backup_listing_and_rotation(self, layout):
        paths, backup_dir, _ = layout
        _, safety_folder = restore_databases(paths, backup_dir, BACKUP_NAME, NOW)

        assert safety_folder.exists()
        assert [f.name for _, f in automation.list_backups(backup_dir)] == [BACKUP_NAME]

    def test_leaves_no_temporary_files_and_removes_stale_journals(self, layout):
        paths, backup_dir, _ = layout
        for suffix in ("-wal", "-shm", "-journal"):
            open(paths[0] + suffix, "wb").write(b"stale")

        restore_databases(paths, backup_dir, BACKUP_NAME, NOW)

        remaining = sorted(p.name for p in Path(paths[0]).parent.iterdir())
        assert remaining == ["history.db", "system.db"]

    def test_restores_onto_a_host_with_no_databases(self, layout):
        paths, backup_dir, _ = layout
        for path in paths:
            os.remove(path)

        _, safety_folder = restore_databases(paths, backup_dir, BACKUP_NAME, NOW)

        assert safety_folder is None
        assert [read_value(path) for path in paths] == ["backed-up", "backed-up"]

    def test_invalid_name_changes_nothing(self, layout):
        paths, backup_dir, _ = layout
        with pytest.raises(RestoreError):
            restore_databases(paths, backup_dir, "../x", NOW)
        assert [read_value(path) for path in paths] == ["current", "current"]

    def test_missing_database_file_changes_nothing(self, layout):
        paths, backup_dir, folder = layout
        (folder / "history.db").unlink()
        with pytest.raises(RestoreError):
            restore_databases(paths, backup_dir, BACKUP_NAME, NOW)
        assert [read_value(path) for path in paths] == ["current", "current"]
        assert not list(backup_dir.glob("pre-restore-*"))

    def test_corrupted_backup_changes_nothing(self, layout):
        paths, backup_dir, folder = layout
        (folder / "history.db").write_text("garbage" * 500)
        with pytest.raises(RestoreError, match="integrity"):
            restore_databases(paths, backup_dir, BACKUP_NAME, NOW)
        assert [read_value(path) for path in paths] == ["current", "current"]
        assert not list(backup_dir.glob("pre-restore-*"))

    def test_failed_swap_puts_the_first_database_back(self, layout):
        paths, backup_dir, _ = layout
        real_swap = backup_restore.swap_in
        calls = []

        def swap_then_fail(staged, target):
            calls.append(target)
            if len(calls) == 2:
                raise PermissionError("denied")
            real_swap(staged, target)

        with patch("app.backup_restore.swap_in", swap_then_fail):
            with pytest.raises(RestoreError, match="put back"):
                restore_databases(paths, backup_dir, BACKUP_NAME, NOW)

        assert [read_value(path) for path in paths] == ["current", "current"]

    def test_safety_copy_keeps_an_unreadable_current_database(self, layout):
        paths, backup_dir, _ = layout
        Path(paths[0]).write_text("not sqlite" * 500)

        folder = make_safety_copy(paths, backup_dir, NOW)

        assert (folder / "system.db").read_text() == "not sqlite" * 500


# ==========================================================
# COMMAND
# ==========================================================

@pytest.fixture()
def run_command(app, layout):
    paths, backup_dir, _ = layout

    def run(*args, service_active=False):
        runner = app.test_cli_runner()
        with patch.dict(app.config, {"DATABASE_BACKUP_DIR": backup_dir}), \
             patch.object(automation, "database_file_paths", return_value=paths), \
             patch.object(restore_command, "service_is_active", return_value=service_active):
            return runner.invoke(restore_command.restore_backup_command, list(args))

    return run


class TestRestoreCommand:
    def test_restores_and_prints_follow_up_steps(self, run_command, layout):
        paths, _, _ = layout

        result = run_command(BACKUP_NAME, "--yes")

        assert result.exit_code == 0, result.output
        assert [read_value(path) for path in paths] == ["backed-up", "backed-up"]
        assert "flask db upgrade --multidb" in result.output
        assert "flask sync-permissions" in result.output
        assert "Nagios configuration" in result.output
        assert "pre-restore-" in result.output

    def test_refuses_without_confirmation(self, run_command, layout):
        paths, _, _ = layout
        result = run_command(BACKUP_NAME)
        assert result.exit_code != 0
        assert "--yes" in result.output
        assert [read_value(path) for path in paths] == ["current", "current"]

    def test_refuses_while_the_service_runs(self, run_command, layout):
        paths, _, _ = layout
        result = run_command(BACKUP_NAME, "--yes", service_active=True)
        assert result.exit_code != 0
        assert "--force" in result.output
        assert [read_value(path) for path in paths] == ["current", "current"]

    def test_force_restores_while_the_service_runs(self, run_command, layout):
        paths, _, _ = layout
        result = run_command(BACKUP_NAME, "--yes", "--force", service_active=True)
        assert result.exit_code == 0, result.output
        assert [read_value(path) for path in paths] == ["backed-up", "backed-up"]

    def test_refuses_invalid_folder_name(self, run_command, layout):
        paths, _, _ = layout
        result = run_command("../../etc", "--yes")
        assert result.exit_code != 0
        assert "not a backup folder name" in result.output
        assert [read_value(path) for path in paths] == ["current", "current"]

    def test_refuses_missing_database_file(self, run_command, layout):
        paths, _, folder = layout
        (folder / "system.db").unlink()
        result = run_command(BACKUP_NAME, "--yes")
        assert result.exit_code != 0
        assert "system.db" in result.output
        assert [read_value(path) for path in paths] == ["current", "current"]

    def test_refuses_corrupted_database(self, run_command, layout):
        paths, _, folder = layout
        (folder / "system.db").write_text("garbage" * 500)
        result = run_command(BACKUP_NAME, "--yes")
        assert result.exit_code != 0
        assert "integrity" in result.output
        assert [read_value(path) for path in paths] == ["current", "current"]
