"""
Runs the remediation escalation migration (e153c4a8b2d7) against a throwaway database and
prints a JSON report. Launched in a subprocess by test_remediation_migration.py (#153).

Usage (from server/): python tests/support/remediation_escalation_migration_runner.py
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

BEFORE = "f155a3c7d2b1"
TARGET = "e153c4a8b2d7"
report = {}

ACTION = (
    "insert into REMEDIATION_ACTION (Name, Action_Type, Scope_Kind, Host_Pattern, Service_Pattern,"
    " Parameters, Enabled, Max_Runs_Per_Hour, Cooldown_Seconds, Version, Updated_At)"
    " values ('keep', 'RECORD_ONLY', 'SERVICE', 'h', 's', '{}', 1, 2, 600, 1, '2026-01-01')"
)
RUN = (
    "insert into REMEDIATION_RUN (Event_Key, Action_Id, Action_Name, Hostname, Service, State,"
    " State_Type, Attempt, Received_At, Outcome) values (?, 1, 'keep', 'h', 's', 'CRITICAL',"
    " 'HARD', 3, '2026-01-01', ?)"
)


def columns(conn, table):
    return [r[1] for r in conn.execute(f"pragma table_info({table})")]


def tables(conn):
    return sorted(r[0] for r in conn.execute(
        "select name from sqlite_master where type='table' and name like 'REMEDIATION_%'"))


with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
required = {"Id": 1, "Updated_At": "2026-01-01", "Version": 1}
for _cid, name, kind, notnull, default, _pk in c.execute("pragma table_info(SYSTEM_SETTINGS)").fetchall():
    if notnull and default is None and name not in required:
        required[name] = "weekly" if "CHAR" in kind.upper() else 0
c.execute(
    "insert into SYSTEM_SETTINGS (%s) values (%s)" % (", ".join(required), ", ".join("?" * len(required))),
    list(required.values()))
c.execute(ACTION)
c.execute(RUN, ("old", "FAILED"))
c.commit()
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version"] = c.execute("select version_num from alembic_version").fetchall()
report["settings_columns"] = columns(c, "SYSTEM_SETTINGS")
report["action_columns"] = columns(c, "REMEDIATION_ACTION")
report["run_columns"] = columns(c, "REMEDIATION_RUN")
report["settings_defaults"] = c.execute(
    "select Remediation_Repeat_Count, Remediation_Repeat_Window_Hours from SYSTEM_SETTINGS").fetchall()
report["action_default"] = c.execute("select Notify_On from REMEDIATION_ACTION").fetchall()
report["run_defaults"] = c.execute(
    "select Notify_Kind, Notify_State, Notify_Attempts, Notify_Error, Notify_At from REMEDIATION_RUN").fetchall()
c.execute("update REMEDIATION_RUN set Notify_Kind='failed', Notify_State='SENT', Notify_Attempts=1")
c.commit()
report["state_accepted"] = c.execute("select Notify_State from REMEDIATION_RUN").fetchall()
c.close()

with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["version_after_downgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["settings_columns_after_downgrade"] = columns(c, "SYSTEM_SETTINGS")
report["action_columns_after_downgrade"] = columns(c, "REMEDIATION_ACTION")
report["run_columns_after_downgrade"] = columns(c, "REMEDIATION_RUN")
report["runs_after_downgrade"] = c.execute("select count(*) from REMEDIATION_RUN").fetchone()[0]
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version_after_reupgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["runs_after_reupgrade"] = c.execute("select count(*) from REMEDIATION_RUN").fetchone()[0]
c.close()

print("REPORT_BEGIN")
print(json.dumps(report))
print("REPORT_END")
