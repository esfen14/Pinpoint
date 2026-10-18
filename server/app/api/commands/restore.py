from datetime import datetime, timezone

import click
from flask import current_app
from flask.cli import with_appcontext

from app import db
from app.backup_restore import (
    SERVICE_UNIT,
    RestoreError,
    restore_databases,
    service_is_active,
)

FOLLOW_UP_STEPS = (
    "flask db upgrade --multidb",
    "flask sync-permissions",
    "Regenerate the Nagios configuration (save a device or run a discovery scan; "
    "the existing writer validates it with nagios -v before reloading).",
    "Start the service: sudo systemctl start " + SERVICE_UNIT,
)


@click.command("restore-backup")
@click.argument("folder")
@click.option("--yes", is_flag=True, help="Confirm that the current databases will be replaced.")
@click.option("--force", is_flag=True, help=f"Restore even if {SERVICE_UNIT} is running.")
@with_appcontext
def restore_backup_command(folder, yes, force):
    """Replace system.db and history.db with the backup FOLDER (YYYYMMDD-HHMMSS).

    FOLDER is a name from DATABASE_BACKUP_DIR, not a path. The current
    databases are kept in a pre-restore-* folder next to the backups.
    Stop the web service first; --force skips that check.
    """
    from app.automation import database_file_paths

    if not yes:
        raise click.ClickException(
            "This replaces the current databases. Stop the service, then run again with --yes."
        )

    if service_is_active() and not force:
        raise click.ClickException(
            f"{SERVICE_UNIT} is running. Stop it first (sudo systemctl stop {SERVICE_UNIT}) "
            "or use --force."
        )

    backup_dir = current_app.config["DATABASE_BACKUP_DIR"]
    # Release pooled connections so no open handle points at a replaced file.
    for engine in [db.engine] + list(db.engines.values()):
        engine.dispose()

    try:
        backup_folder, safety_folder = restore_databases(
            database_file_paths(), backup_dir, folder, datetime.now(timezone.utc)
        )
    except RestoreError as exc:
        raise click.ClickException(str(exc))

    for engine in [db.engine] + list(db.engines.values()):
        engine.dispose()

    click.echo(f"Restored the databases from {backup_folder.name}.")
    if safety_folder is not None:
        click.echo(f"Previous databases kept in {safety_folder.name} inside the backup directory.")
    click.echo("Next steps, in order:")
    for number, step in enumerate(FOLLOW_UP_STEPS, start=1):
        click.echo(f"  {number}. {step}")
