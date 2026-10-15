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

BEFORE = "e79b7d3c2641"
TARGET = "e4a7c1d9b305"
TABLES = ("REMEDIATION_ACTION", "REMEDIATION_RUN")
report = {}


def tables(conn):
    return sorted(r[0] for r in conn.execute("select name from sqlite_master where type='table'") if r[0] in TABLES)


def columns(conn, table):
    return [row[1] for row in conn.execute(f"pragma table_info({table})")]


def insert_administrator_role(conn):
    """The Administrator role, filling every NOT NULL column that has no default."""
    names, values = [], []
    for _cid, name, ctype, notnull, default, pk in conn.execute("pragma table_info(ROLE)"):
        if pk:
            continue
        if name == "Name":
            names.append(name)
            values.append("Administrator")
        elif notnull and default is None:
            names.append(name)
            values.append(1 if "INT" in ctype.upper() or "BOOL" in ctype.upper() else "x")
    conn.execute(f"insert into ROLE ({', '.join(names)}) values ({', '.join('?' * len(values))})", values)


def permissions(conn):
    """Remediation permissions that exist, and the ones the Administrator role holds."""
    existing = sorted(r[0] for r in conn.execute("select Name from PERMISSION where Name like 'remediation.%'"))
    granted = sorted(r[0] for r in conn.execute(
        "select p.Name from ROLE_PERMISSION rp join PERMISSION p on p.PermissionID = rp.PermissionID"
        " join ROLE r on r.RoleID = rp.RoleID where r.Name = 'Administrator' and p.Name like 'remediation.%'"))
    return {"existing": existing, "administrator": granted}


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
            " values ('k1', 1, 'first action', 'web-01', 'HTTP', 'CRITICAL', 'HARD', 3, '2026-01-01', 'SUCCEEDED')"
        )
        conn.commit()
        return False
    except sqlite3.IntegrityError:
        return True


with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["tables_before"] = tables(c)
insert_administrator_role(c)
c.commit()
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version"] = c.execute("select version_num from alembic_version").fetchall()
report["tables_after"] = tables(c)
report["permissions"] = permissions(c)
report["action_columns"] = columns(c, "REMEDIATION_ACTION")
report["run_columns"] = columns(c, "REMEDIATION_RUN")
insert_row(c)
report["duplicate_run_rejected"] = duplicate_run_rejected(c)
c.close()

with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["tables_after_downgrade"] = tables(c)
report["permissions_after_downgrade"] = permissions(c)
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version_after_reupgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["tables_after_reupgrade"] = tables(c)
report["permissions_after_reupgrade"] = permissions(c)
c.close()

print("REPORT_BEGIN")
print(json.dumps(report))
print("REPORT_END")
