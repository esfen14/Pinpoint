"""Exercise the device interface revision on throwaway system/history databases."""
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

    def tables():
        with sqlite3.connect(system_db) as connection:
            return [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]

    with app.app_context():
        flask_migrate.upgrade(directory="migrations", revision="head")
    after_upgrade = tables()
    with sqlite3.connect(system_db) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(DEVICE_INTERFACE)")]
    with app.app_context():
        flask_migrate.downgrade(directory="migrations", revision="c5e2a8f4d716")
    after_downgrade = tables()
    with app.app_context():
        flask_migrate.upgrade(directory="migrations", revision="head")
    after_second_upgrade = tables()

    print("REPORT_BEGIN")
    print(json.dumps({
        "columns": columns,
        "has_table_after_upgrade": "DEVICE_INTERFACE" in after_upgrade,
        "has_table_after_downgrade": "DEVICE_INTERFACE" in after_downgrade,
        "has_table_after_second_upgrade": "DEVICE_INTERFACE" in after_second_upgrade,
    }))
    print("REPORT_END")
