"""Exercise the notification policy revision on throwaway system/history databases."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())
with tempfile.TemporaryDirectory() as directory:
    system_db = os.path.join(directory, "system.db")
    history_db = os.path.join(directory, "history.db")
    os.environ["DATABASE_URL"] = "sqlite:///" + system_db
    os.environ["SECRET_KEY"] = "test-only"

    import config
    config.Config.SQLALCHEMY_BINDS = {"history": "sqlite:///" + history_db}
    import flask_migrate
    from app import app

    with app.app_context():
        flask_migrate.upgrade(directory="migrations", revision="head")
    with sqlite3.connect(system_db) as connection:
        rows = connection.execute(
            "SELECT Id, Quiet_Hours, Host_Options, Service_Options, Renotify_Interval, Version "
            "FROM NOTIFICATION_POLICY"
        ).fetchall()
    with app.app_context():
        flask_migrate.downgrade(directory="migrations", revision="a4c8e1f6d392")
    with sqlite3.connect(system_db) as connection:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print("REPORT_BEGIN")
    print(json.dumps({"rows": rows, "tables_after_downgrade": tables}))
    print("REPORT_END")
