"""
Restore the SQLite databases from a backup folder made by automation.backup_databases.

Used by the `flask restore-backup` command (app/api/commands/restore.py). A restore
is destructive, so everything here is checked before a live database file is
touched, and the previous databases are kept in a safety copy.

Cold-standby recovery only: it replaces the files on one host. It is not
failover between two live nodes.
"""
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

BACKUP_FOLDER_FORMAT = "%Y%m%d-%H%M%S"
SAFETY_COPY_PREFIX = "pre-restore-"
SERVICE_UNIT = "pinpoint-gunicorn.service"
SERVICE_CHECK_TIMEOUT_SECONDS = 10
SQLITE_SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")
RESTORE_TEMP_SUFFIX = ".restore-tmp"


class RestoreError(Exception):
    """A restore was refused or failed; the message is safe to show to an administrator."""


# ==========================================================
# VALIDATION
# ==========================================================

def resolve_backup_folder(backup_dir, name):
    """
    Return the Path of the backup folder called name inside backup_dir.
    name must be a bare folder name in BACKUP_FOLDER_FORMAT (so it cannot
    contain a path), and the folder must be a real directory directly inside
    backup_dir, not a symlink. Raises RestoreError otherwise.
    """
    try:
        valid = datetime.strptime(name, BACKUP_FOLDER_FORMAT).strftime(BACKUP_FOLDER_FORMAT) == name
    except ValueError:
        valid = False
    if not valid:
        raise RestoreError(f"'{name}' is not a backup folder name (expected YYYYMMDD-HHMMSS).")

    folder = Path(backup_dir) / name
    if folder.is_symlink() or not folder.is_dir():
        raise RestoreError(f"Backup folder '{name}' does not exist.")
    if folder.resolve().parent != Path(backup_dir).resolve():
        raise RestoreError(f"Backup folder '{name}' is outside the backup directory.")
    return folder


def backup_file_paths(folder, database_paths):
    """
    Return the backup file for each database in database_paths, in the same
    order. Raises RestoreError if any is missing or is not a regular file.
    """
    files = []
    for database_path in database_paths:
        name = Path(database_path).name
        backup_file = Path(folder) / name
        if backup_file.is_symlink() or not backup_file.is_file():
            raise RestoreError(f"Backup is missing {name}; nothing was changed.")
        files.append(backup_file)
    return files


def integrity_check(path):
    """
    Whether the SQLite file at path opens read-only and passes
    PRAGMA integrity_check. A file that is not a database returns False.
    """
    uri = f"file:{quote(str(Path(path).resolve()))}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
            rows = connection.execute("PRAGMA integrity_check").fetchall()
        finally:
            connection.close()
    except sqlite3.Error:
        return False
    return rows == [("ok",)]


def service_is_active(unit=SERVICE_UNIT, run=subprocess.run):
    """
    Whether the systemd unit is running. A host without systemctl (or one that
    does not answer in time) reports False, so a development machine is not
    blocked. The unit name is a fixed constant, never user input.
    """
    try:
        result = run(
            ["systemctl", "is-active", "--quiet", unit],
            capture_output=True,
            timeout=SERVICE_CHECK_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


# ==========================================================
# RESTORE
# ==========================================================

def make_safety_copy(database_paths, backup_dir, now):
    """
    Copy the current databases into backup_dir/pre-restore-<timestamp>. Existing
    files only; a host with no database yet has nothing to keep. The folder name
    does not match BACKUP_FOLDER_FORMAT, so list_backups ignores it and backup
    rotation never deletes it. Returns the folder, or None if nothing was copied.
    """
    existing = [Path(path) for path in database_paths if Path(path).is_file()]
    if not existing:
        return None

    folder = Path(backup_dir) / f"{SAFETY_COPY_PREFIX}{now.strftime(BACKUP_FOLDER_FORMAT)}"
    folder.mkdir(parents=True, exist_ok=False)
    for source_path in existing:
        target_path = folder / source_path.name
        try:
            source = sqlite3.connect(source_path)
            target = sqlite3.connect(target_path)
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()
        except sqlite3.Error:
            # A damaged current database cannot be read by the backup API; keep the raw file.
            target_path.unlink(missing_ok=True)
            shutil.copy2(source_path, target_path)
    return folder


def stage_database(backup_file, target_path):
    """
    Write a clean copy of backup_file next to target_path (same filesystem, so
    the later rename is atomic) and return the staged path. Uses the SQLite
    backup API, so the staged file has no journal sidecars.
    """
    staged = Path(str(target_path) + RESTORE_TEMP_SUFFIX)
    staged.unlink(missing_ok=True)
    source = sqlite3.connect(f"file:{quote(str(Path(backup_file).resolve()))}?mode=ro", uri=True)
    target = sqlite3.connect(staged)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return staged


def swap_in(staged, target_path):
    """Delete stale journal sidecars of target_path, then atomically rename staged over it."""
    for suffix in SQLITE_SIDECAR_SUFFIXES:
        Path(str(target_path) + suffix).unlink(missing_ok=True)
    os.replace(staged, target_path)


def restore_databases(database_paths, backup_dir, name, now):
    """
    Replace every database in database_paths with its copy from backup folder
    name. All checks and staging happen before any live file changes; the
    previous databases are kept in a safety copy. If a replacement fails part
    way, the databases already replaced are put back from the safety copy.
    Returns (backup_folder, safety_folder). The caller must have stopped the
    web service. Raises RestoreError.
    """
    folder = resolve_backup_folder(backup_dir, name)
    backup_files = backup_file_paths(folder, database_paths)
    for backup_file in backup_files:
        if not integrity_check(backup_file):
            raise RestoreError(f"{backup_file.name} in the backup failed the integrity check; nothing was changed.")

    safety_folder = make_safety_copy(database_paths, backup_dir, now)

    staged_files = []
    try:
        for backup_file, target_path in zip(backup_files, database_paths):
            staged_files.append(stage_database(backup_file, target_path))
    except (sqlite3.Error, OSError) as exc:
        for staged in staged_files:
            staged.unlink(missing_ok=True)
        raise RestoreError(f"Could not prepare the restored databases ({exc.__class__.__name__}); nothing was changed.")

    replaced = []
    try:
        for staged, target_path in zip(staged_files, database_paths):
            swap_in(staged, target_path)
            replaced.append(target_path)
    except OSError as exc:
        for staged in staged_files:
            staged.unlink(missing_ok=True)
        rolled_back = rollback_from_safety_copy(replaced, safety_folder)
        detail = "The previous databases were put back." if rolled_back else "Restore them from the safety copy by hand."
        raise RestoreError(f"Replacing the databases failed ({exc.__class__.__name__}). {detail}")

    return folder, safety_folder


def rollback_from_safety_copy(replaced_paths, safety_folder):
    """
    Put the databases in replaced_paths back from safety_folder. Returns True
    when every one was restored. A database with no saved copy (none existed
    before the restore) is removed again.
    """
    ok = True
    for target_path in replaced_paths:
        target_path = Path(target_path)
        saved = Path(safety_folder) / target_path.name if safety_folder else None
        try:
            if saved is not None and saved.is_file():
                staged = Path(str(target_path) + RESTORE_TEMP_SUFFIX)
                shutil.copyfile(saved, staged)
                swap_in(staged, target_path)
            else:
                target_path.unlink(missing_ok=True)
        except OSError:
            ok = False
    return ok
