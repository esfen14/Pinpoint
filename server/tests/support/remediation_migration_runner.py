"""
Runs the remediation tables migration (e4a7c1d9b305) against throwaway databases and
prints a JSON report. Not a test itself: it is launched in a subprocess by
test_remediation_migration.py because Alembic needs a Flask app configured for
temporary databases before "app" is imported.

Usage (from server/): python tests/support/remediation_migration_runner.py
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())

tmp = tempfile.mkdtemp()
sysdb = os.path.join(tmp, "sys.db").replace("\\", "/")
histdb = os.path.join(tmp, "hist.db").replace("\\", "/")
os.environ["DATABASE_URL"] = "sqlite:///" + sysdb
os.environ["SECRET_KEY"] = "x"

import config  # noqa: E402

config.Config.SQLALCHEMY_BINDS = {"history": "sqlite:///" + histdb}

import flask_migrate  # noqa: E402
from app import app  # noqa: E402

BEFORE = "c5e2a8f4d716"
TARGET = "e4a7c1d9b305"
TABLES = ("REMEDIATION_ACTION", "REMEDIATION_RUN")
report = {}


def tables(conn):
    return sorted(r[0] for r in conn.execute("select name from sqlite_master where type='table'") if r[0] in TABLES)


def columns(conn, table):
    return [row[1] for row in conn.execute(f"pragma table_info({table})")]


def insert_row(conn):
    """One action and one run, to prove the table accepts the documented columns."""
    conn.execute(
        "insert into REMEDIATION_ACTION (Name, Action_Type, Scope_Kind, Host_Pattern, Service_Pattern,"
        " Parameters, Enabled, Max_Runs_Per_Hour, Cooldown_Seconds, Version, Updated_At)"
        " values ('first action', 'RECORD_ONLY', 'SERVICE', 'web-*', 'HTTP', '{}', 1, 2, 600, 1, '2026-01-01')"
    )
    conn.execute(
        "insert into REMEDIATION_RUN (Event_Key, Action_Id, Action_Name, Hostname, Service, State,"
        " State_Type, Attempt, Received_At, Outcome)"
        " values ('k1', 1, 'first action', 'web-01', 'HTTP', 'CRITICAL', 'HARD', 3, '2026-01-01', 'SUCCEEDED')"
    )
    conn.commit()


def duplicate_run_rejected(conn):
    """Same Event_Key for the same action must be refused (replay protection)."""
    try:
        conn.execute(
            "insert into REMEDIATION_RUN (Event_Key, Action_Id, Action_Name, Hostname, Service, State,"
            " State_Type, Attempt, Received_At, Outcome)"
            " values ('k1', 1, 'first action', 'web-01', 'HTTP', 'CRITICAL', 'HARD', 3, '2026-01-01', 'DUPLICATE')"
        )
        conn.commit()
        return False
    except sqlite3.IntegrityError:
        return True


with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["tables_before"] = tables(c)
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version"] = c.execute("select version_num from alembic_version").fetchall()
report["tables_after"] = tables(c)
report["action_columns"] = columns(c, "REMEDIATION_ACTION")
report["run_columns"] = columns(c, "REMEDIATION_RUN")
insert_row(c)
report["duplicate_run_rejected"] = duplicate_run_rejected(c)
c.close()

with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["tables_after_downgrade"] = tables(c)
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version_after_reupgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["tables_after_reupgrade"] = tables(c)
c.close()

print("REPORT_BEGIN")
print(json.dumps(report))
print("REPORT_END")
