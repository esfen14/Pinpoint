"""Read appliance storage sizes without following links or scanning an unbounded tree."""
import os
from pathlib import Path
import shutil
import stat
import time

from flask import current_app

from app.automation import database_file_paths


def filesystem_usage(path):
    """Return free/total bytes for a location, using its nearest existing parent if missing."""
    path = Path(path)
    try:
        while not path.exists() and path != path.parent:
            path = path.parent
        usage = shutil.disk_usage(path)
        return {'free_bytes': usage.free, 'total_bytes': usage.total}
    except OSError:
        return None


def directory_usage(path, max_entries=10000, max_seconds=0.1):
    """Sum regular file lengths with entry/time budgets; partial totals are explicitly marked."""
    path = Path(path)
    result = {'bytes': None, 'complete': False, 'filesystem': filesystem_usage(path)}
    try:
        if not stat.S_ISDIR(os.stat(path, follow_symlinks=False).st_mode):
            return result
    except OSError:
        return result
    pending = [path]
    total = 0
    visited = 0
    deadline = time.monotonic() + max_seconds
    complete = True
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    if visited >= max_entries or time.monotonic() >= deadline:
                        return {**result, 'bytes': total, 'complete': False}
                    visited += 1
                    try:
                        info = entry.stat(follow_symlinks=False)
                        if stat.S_ISREG(info.st_mode):
                            total += info.st_size
                        elif stat.S_ISDIR(info.st_mode):
                            pending.append(Path(entry.path))
                    except OSError:
                        complete = False
        except OSError:
            if folder == path:
                return result
            complete = False
    return {**result, 'bytes': total, 'complete': complete}


def storage_usage(database_paths, backup_dir, archive_dir):
    """Measure each configured database, backups, archives and their filesystems; expose no paths."""
    databases = []
    for path in database_paths:
        size = None
        try:
            info = os.stat(path, follow_symlinks=False)
            if stat.S_ISREG(info.st_mode):
                size = info.st_size
        except OSError:
            pass
        databases.append({'name': Path(path).name, 'bytes': size,
                          'filesystem': filesystem_usage(path)})
    return {'databases': databases, 'backups': directory_usage(backup_dir),
            'archives': directory_usage(archive_dir)}


def get_storage_usage():
    """Read the application's SQLite locations and trusted storage-directory settings."""
    return storage_usage(database_file_paths(), current_app.config['DATABASE_BACKUP_DIR'],
                         current_app.config['NAGIOS_LOG_ARCHIVE_DIR'])
